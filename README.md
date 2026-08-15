# 🎥 DarkCam v1.0.0

> Webcam Video Capture Framework for Authorized Red Team Engagements

```
  ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗ █████╗ ███╗   ███╗
  ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██╔══██╗████╗ ████║
  ██║  ██║███████║██████╔╝█████╔╝ ██║     ███████║██╔████╔██║
  ██║  ██║██╔══██║██╔══██╗██╔═██╗ ██║     ██╔══██║██║╚██╔╝██║
  ██████╔╝██║  ██║██║  ██║██║  ██╗╚██████╗██║  ██║██║ ╚═╝ ██║
  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝

  [ Webcam Video Capture Framework | Authorized Red Team Use Only ]
  [ By: Yaman RedTeam | v1.0.0 ]
```

---

## ⚠️ Disclaimer

**DarkCam is strictly for authorized security testing, red team engagements, and educational purposes only.**  
Unauthorized use against individuals without explicit consent is illegal. The developer assumes no liability for misuse.

---

## Features

- 🎭 **8 Lure Pages** — Google Meet, Zoom, WhatsApp, Instagram, Omegle, Microsoft Teams, Telegram, FaceTime
- 📹 **WebM Video Capture** — Browser-native MediaRecorder API, 5-second chunked upload
- 🌍 **IP + Geolocation Logging** — City, ISP, country via ipapi.co
- 🔗 **Auto Cloudflared Tunnel** — Instant public HTTPS URL, no account needed
- 💾 **Auto Merge** — Chunks auto-merged into single `.webm` file on session end
- 📋 **Victim Log** — JSON log with timestamp, IP, User-Agent, geolocation

---

## Lure Pages

| Page | Flag | Lure |
|------|------|------|
| Google Meet | `meet` | Fake meeting join page |
| Zoom | `zoom` | Waiting for host screen |
| WhatsApp | `whatsapp` | Incoming video call |
| Instagram | `instagram` | Video call with LIVE badge |
| Omegle | `omegle` | Random stranger video chat |
| Microsoft Teams | `teams` | Corporate meeting with fake ID |
| Telegram | `telegram` | Incoming call with pulse animation |
| FaceTime | `facetime` | Full-screen iOS-style call UI |

---

## Installation

```bash
git clone https://github.com/Yaman-RedTeam/darkcam
cd darkcam
pip install -r requirements.txt
```

**Install cloudflared (auto-installs if missing):**
```bash
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
```

---

## Usage

```bash
# Google Meet lure (default)
python3 darkcam.py

# WhatsApp lure
python3 darkcam.py --page whatsapp

# Zoom lure
python3 darkcam.py --page zoom

# FaceTime lure
python3 darkcam.py --page facetime

# Custom port
python3 darkcam.py --page telegram --port 9090

# Local only (no tunnel)
python3 darkcam.py --page instagram --no-tunnel
```

---

## Output

```
output/
├── <session_id>.webm     # Captured video
└── victims.log           # JSON log of all visitors
```

**victims.log format:**
```json
{
  "timestamp": "2026-08-16T00:00:00",
  "ip": "x.x.x.x",
  "user_agent": "Mozilla/5.0...",
  "session": "abc123",
  "geo": {
    "city": "Mumbai",
    "country": "IN",
    "org": "Reliance Jio"
  }
}
```

---

## How It Works

```
darkcam.py starts
    → Flask server (local)
    → Cloudflared tunnel → public HTTPS URL
    → Victim opens URL
    → Lure page loads (fake video call)
    → Browser requests camera permission
    → MediaRecorder captures video in 5s chunks
    → Chunks sent to /upload endpoint
    → /finalize merges chunks → .webm saved
    → IP + geo logged to victims.log
```

---

## Part of Ghost Series

| Tool | Description |
|------|-------------|
| [GhostPhish](https://github.com/Yaman-RedTeam/ghostphish) | Phishing Framework |
| [GhostBuster](https://github.com/Yaman-RedTeam/ghostbuster) | OSINT Recon Framework |
| **DarkCam** | Webcam Video Capture |

---

## Author

**Yaman RedTeam** — Red Team Associate, VAPT Analyst  
GitHub: [@Yaman-RedTeam](https://github.com/Yaman-RedTeam)
