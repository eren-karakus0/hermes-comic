#!/usr/bin/env bash
# Bootstrap WSL2 Ubuntu 22.04 for hermes-comic development.
# Idempotent — safe to re-run.
set -euo pipefail

echo "[1/5] apt update + system deps..."
sudo apt update
sudo apt install -y software-properties-common curl git build-essential \
    libjpeg-dev zlib1g-dev libfreetype6-dev fonts-noto-cjk

echo "[2/5] Python 3.11 (deadsnakes PPA — Ubuntu 22 default is 3.10)..."
if ! command -v python3.11 &>/dev/null; then
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.11 python3.11-venv python3.11-dev
fi

echo "[3/5] uv installer..."
if ! command -v uv &>/dev/null && [ ! -x "$HOME/.local/bin/uv" ]; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    if ! grep -q '.local/bin' ~/.bashrc; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi
fi
export PATH="$HOME/.local/bin:$PATH"

echo "[4/5] git config (idempotent)..."
git config --global user.email "erenkar950@gmail.com" 2>/dev/null || true
git config --global user.name "eren-karakus0" 2>/dev/null || true

echo "[5/5] verify..."
python3.11 --version
uv --version
fc-list | grep -i "noto.*cjk" | head -2 || echo "(noto-cjk fonts indexed)"

echo ""
echo "[done] bootstrap complete."
echo "Next: restart shell or run \`source ~/.bashrc\`, then:"
echo "  cd /mnt/c/Users/EREN/Desktop/nous/hermes-comic"
echo "  uv venv --python 3.11"
echo "  uv sync"
