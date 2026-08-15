#!/bin/bash
# DarkCam — Setup Script (Termux + Linux/Kali)

R="\033[0m"
G="\033[38;5;196m"
O="\033[38;5;208m"
W="\033[38;5;255m"

echo -e "${G}"
echo "  ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗ █████╗ ███╗   ███╗"
echo "  ██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝██╔════╝██╔══██╗████╗ ████║"
echo "  ██║  ██║███████║██████╔╝█████╔╝ ██║     ███████║██╔████╔██║"
echo "  ██████╔╝██║  ██║██║  ██║██║  ██╗╚██████╗██║  ██║██║ ╚═╝ ██║"
echo "  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝"
echo -e "${O}  [ Setup Script | DarkCam v1.0.0 ]${R}"
echo ""

# ── Detect environment ──
IS_TERMUX=false
if [ -n "$PREFIX" ] && echo "$PREFIX" | grep -q "termux"; then
    IS_TERMUX=true
fi

if $IS_TERMUX; then
    echo -e "  ${O}[*]${R} Termux environment detected."
    echo -e "  ${O}[*]${R} Updating pkg..."
    pkg update -y -q 2>/dev/null

    echo -e "  ${O}[*]${R} Installing system packages..."
    pkg install -y python git curl 2>/dev/null
    pkg install -y cloudflared 2>/dev/null || true

    echo -e "  ${O}[*]${R} Installing Python packages..."
    pip install flask colorama requests -q

    echo -e "  ${O}[*]${R} Setting up storage permission..."
    if ! ls ~/storage &>/dev/null; then
        echo -e "  ${O}[!]${R} Allow storage permission when prompted..."
        termux-setup-storage
        sleep 3
    fi
else
    echo -e "  ${O}[*]${R} Linux/Kali environment detected."

    echo -e "  ${O}[*]${R} Installing Python packages..."
    pip install flask colorama requests -q --break-system-packages 2>/dev/null || \
    pip3 install flask colorama requests -q --break-system-packages 2>/dev/null || \
    pip install flask colorama requests -q

    echo -e "  ${O}[*]${R} Installing cloudflared..."
    ARCH=$(uname -m)
    if echo "$ARCH" | grep -qE "arm|aarch"; then
        CF_BIN="cloudflared-linux-arm64"
    else
        CF_BIN="cloudflared-linux-amd64"
    fi
    curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/${CF_BIN}" \
        -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared
fi

echo ""
echo -e "  ${G}[+]${R} Setup complete!"
echo ""
echo -e "  ${W}Usage:${R}"
echo -e "  ${O}  python3 darkcam.py --page whatsapp${R}"
echo -e "  ${O}  python3 darkcam.py --page meet${R}"
echo -e "  ${O}  python3 darkcam.py --page facetime${R}"
echo ""
