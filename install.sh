#!/usr/bin/env bash
# Installs receipt-bridge on a Raspberry Pi running Raspberry Pi OS.
# Run as root: sudo bash install.sh
set -euo pipefail

INSTALL_DIR=/opt/receipt-bridge
CONFIG_DIR=/etc/receipt-bridge
SERVICE_NAME=receipt-bridge

# ── sanity checks ────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
  echo "error: run with sudo" >&2
  exit 1
fi

command -v python3 >/dev/null 2>&1 || { apt-get install -y python3 python3-venv; }

# ── copy package ─────────────────────────────────────────────────────────────
echo "→ installing to $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cp -r receipt_bridge "$INSTALL_DIR/"

# ── virtualenv (no external deps, but keeps system Python clean) ─────────────
python3 -m venv "$INSTALL_DIR/venv"

# ── config ───────────────────────────────────────────────────────────────────
mkdir -p "$CONFIG_DIR"
if [[ ! -f "$CONFIG_DIR/config.conf" ]]; then
  cp config.conf.example "$CONFIG_DIR/config.conf"
  echo "→ created $CONFIG_DIR/config.conf (edit before starting)"
else
  echo "→ $CONFIG_DIR/config.conf already exists, skipping"
fi

# ── systemd ──────────────────────────────────────────────────────────────────
cp receipt-bridge.service /etc/systemd/system/"$SERVICE_NAME".service
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"

echo ""
echo "Installation complete."
echo "Edit $CONFIG_DIR/config.conf if needed, then:"
echo "  sudo systemctl start $SERVICE_NAME"
echo "  sudo journalctl -u $SERVICE_NAME -f"
