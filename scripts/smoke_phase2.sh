#!/usr/bin/env bash
# Phase 2 E2E smoke — series + chapter + render → single webtoon PNG.
# Uses red-vs-blue character references (Ignara + Theros).
# Cost: series (~$0.01) + chapter (~$0.01) + 5-6 panels × $0.04 = ~$0.25
set -euo pipefail

WS="$(pwd)/workspaces/phase2-smoke"
export HERMES_COMIC_WORKSPACE="$WS"
rm -rf "$WS"
mkdir -p "$WS/characters"

# Copy reference PNGs from red-vs-blue so character lookups work
cp -r workspaces/red-vs-blue/characters/ignara "$WS/characters/"
cp -r workspaces/red-vs-blue/characters/theros "$WS/characters/"

echo "=== workspace: $WS ==="
ls "$WS/characters/ignara/" "$WS/characters/theros/"
echo

echo "=== [1/3] comic series new ==="
uv run comic series new \
    "In a world divided between Pyraleth (red-haired conquerors with laser vision, led by Princess Ignara) and Azura (blue-haired peacekeepers with psionic empathy, protected by warrior Theros). Ignara and Theros stand on opposing sides of an ancient war, but a fateful encounter will change everything." \
    --title "red-vs-blue-smoke"

echo
echo "=== [2/3] comic chapter new ==="
uv run comic chapter new \
    "Chapter 1 Origins. Princess Ignara awakens to her laser vision during a royal Pyraleth ceremony, crown and gold gauntlet catching the light. Meanwhile, warrior Theros patrols the Azura border with his glowing cyan psi-blade in his left hand, sensing an incoming threat."

echo
echo "=== [3/3] comic chapter render ==="
uv run comic chapter render 1 --seed 42

echo
echo "=== artifacts ==="
echo "-- chapters/01/panels/ --"
ls -la "$WS/chapters/01/panels/" 2>/dev/null || echo "  (missing)"
echo "-- chapter.png --"
ls -la "$WS/chapters/01/chapter.png" 2>/dev/null || echo "  (missing)"

echo
echo "[done] Phase 2 smoke complete"
echo "→ open in Windows Explorer:"
echo "  C:\\Users\\EREN\\Desktop\\nous\\hermes-comic\\workspaces\\phase2-smoke\\chapters\\01\\chapter.png"
