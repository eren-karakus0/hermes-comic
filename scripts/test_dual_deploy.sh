#!/usr/bin/env bash
# Deploy Neon & Ash to BOTH Cloudflare Pages + Surge.
set -euo pipefail

cd "$(dirname "$0")/.." 
export PATH="$HOME/.local/bin:$PATH"
export HERMES_COMIC_WORKSPACE="$(pwd)/workspaces/neon-and-ash"

echo "=== dual deploy: Cloudflare Pages primary + Surge fallback ==="
uv run comic series publish \
    --tagline "Rain-slick courier. AI ghost in the hologram. Three chapters. Shareable." \
    --provider both
