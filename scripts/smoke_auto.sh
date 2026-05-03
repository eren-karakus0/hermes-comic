#!/usr/bin/env bash
# Minimal smoke test for `comic auto` — 1 chapter, 4 panels, no publish.
# Expected: ~3 min, ~$0.25
set -euo pipefail

cd "$(dirname "$0")/.." 
export PATH="$HOME/.local/bin:$PATH"

# Fresh workspace name to avoid collisions
SLUG="auto-smoke-$(date +%s)"

echo "=== comic auto smoke test (slug: $SLUG) ==="
uv run comic auto \
    "A lighthouse keeper who collects dying stars in glass bottles, haunted by a sea-ghost that wants its light back" \
    --title "$SLUG" \
    --chapters 1 \
    --panels 4 \
    --no-publish \
    --no-cover \
    --seed 42

echo
echo "=== verify outputs ==="
WORKSPACE="$(pwd)/workspaces/$SLUG"
echo "canon:"
ls -la "$WORKSPACE/canon/" 2>&1 | head -10
echo
echo "chapter 01:"
ls -la "$WORKSPACE/chapters/01/" 2>&1 | head -10
echo
echo "series.png:"
ls -la "$WORKSPACE/series.png" 2>&1

echo
echo "[done] smoke test complete"
