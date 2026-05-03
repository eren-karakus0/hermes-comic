#!/usr/bin/env bash
set -euo pipefail

cd /mnt/c/Users/EREN/Desktop/nous/hermes-comic
export PATH="$HOME/.local/bin:$PATH"
export HERMES_COMIC_WORKSPACE="$(pwd)/workspaces/neon-and-ash"

echo "=== generate cover for Neon & Ash ==="
uv run comic series cover \
    --tagline "Rain-slick courier. AI ghost in the hologram." \
    --seed 42
