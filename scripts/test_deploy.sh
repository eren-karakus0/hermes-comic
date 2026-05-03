#!/usr/bin/env bash
# Deploy Neon & Ash bundle to surge.sh for the first time.
set -euo pipefail

cd "$(dirname "$0")/.." 
export PATH="$HOME/.local/bin:$PATH"
export HERMES_COMIC_WORKSPACE="$(pwd)/workspaces/neon-and-ash"

echo "=== workspace: $HERMES_COMIC_WORKSPACE ==="
echo "=== publishing to surge.sh ==="
uv run comic series publish \
    --tagline "Rain-slick courier. AI ghost in the hologram. Three chapters. Shareable." \
    --domain "hermes-neon-and-ash"
