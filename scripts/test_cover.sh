#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.." 
export PATH="$HOME/.local/bin:$PATH"
export HERMES_COMIC_WORKSPACE="$(pwd)/workspaces/neon-and-ash"

echo "=== generate cover for Neon & Ash ==="
uv run comic series cover \
    --tagline "Rain-slick courier. AI ghost in the hologram." \
    --seed 42
