#!/usr/bin/env bash
# Verify `comic series publish --no-deploy` builds a valid HTML bundle.
set -euo pipefail

cd "$(dirname "$0")/.." 
export PATH="$HOME/.local/bin:$PATH"
export HERMES_COMIC_WORKSPACE="$(pwd)/workspaces/neon-and-ash"

echo "=== workspace: $HERMES_COMIC_WORKSPACE ==="
ls "$HERMES_COMIC_WORKSPACE/chapters"

echo
echo "=== building bundle (no deploy) ==="
uv run comic series publish \
    --tagline "A rain-slick courier and an AI ghost running forbidden data through the neon" \
    --no-deploy

echo
echo "=== bundle contents ==="
ls -la "$HERMES_COMIC_WORKSPACE/_publish/"

echo
echo "=== index.html head ==="
head -40 "$HERMES_COMIC_WORKSPACE/_publish/index.html"
