#!/usr/bin/env bash
# Phase 1 end-to-end smoke — isolated workspace, full CLI flow + continuity.
# Cost estimate: ~$0.05 (3 Kimi calls).
set -euo pipefail

# Use isolated workspace so we don't pollute red-vs-blue canon
WS="$(pwd)/workspaces/phase1-smoke"
export HERMES_COMIC_WORKSPACE="$WS"
rm -rf "$WS"
mkdir -p "$WS"

echo "=== workspace: $WS ==="
echo

echo "=== [1/4] comic series new ==="
uv run comic series new \
    "In a world divided between Pyraleth (red-haired conquerors with laser vision) and Azura (blue-haired peacekeepers with psionic empathy), a princess and a warrior stand on opposing sides of an ancient war." \
    --title "red-vs-blue-smoke"

echo
echo "=== [2/4] comic series status ==="
uv run comic series status

echo
echo "=== [3/4] comic chapter new ==="
uv run comic chapter new \
    "The Pyraleth princess Ignara awakens to her laser powers during a royal ceremony. Meanwhile, the Azura warrior Theros is dispatched on a tense border patrol."

echo
echo "=== [4/4] continuity_guard (skill script) ==="
uv run python skills/comic-series/scripts/continuity_guard.py --chapter 1

echo
echo "=== artifacts ==="
echo "-- canon --"
ls -la "$WS/canon/"
echo "-- chapters/01 --"
ls -la "$WS/chapters/01/"
echo "-- history --"
ls -la "$WS/history/"

echo
echo "[done] Phase 1 smoke OK"
