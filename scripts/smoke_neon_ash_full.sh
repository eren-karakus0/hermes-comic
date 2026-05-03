#!/usr/bin/env bash
# Phase 2.5 full Neon & Ash production + demo flagship features.
# Assumes Chapter 1 already rendered by smoke_neon_ash_ch1.sh
set -euo pipefail

cd /mnt/c/Users/EREN/Desktop/nous/hermes-comic
export PATH="$HOME/.local/bin:$PATH"
set -a && source .env && set +a
export HERMES_COMIC_WORKSPACE="$(pwd)/workspaces/neon-and-ash"

echo "════════════════════════════════════════════════════════════"
echo "  [1/7] chapter 2 new — The Pursuit"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter new \
    "The Pursuit. Unknown corporate agents have traced Kira's location through her bike's cyan headlamp. Ghost manifests in a storefront hologram, warning her of an ambush two blocks ahead. Kira reluctantly trusts the AI and reroutes through a cramped neon market district. Chase sequence: Kira weaving through fish-stall holograms and steam vents while hunter drones swoop behind; Ghost flickers into each shop sign along her escape path, guiding her with direction arrows. They finally break into a derelict data temple — lights flicker on as Ghost steps fully out of a central holo-projector, showing Kira its complete form for the first time."

echo
echo "════════════════════════════════════════════════════════════"
echo "  [2/7] chapter 2 render"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter render 2 --seed 42

echo
echo "════════════════════════════════════════════════════════════"
echo "  [3/7] multimodal continuity guardian on chapter 2 (FLAGSHIP)"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter continuity 2 --multimodal

echo
echo "════════════════════════════════════════════════════════════"
echo "  [4/7] style evolver feedback for chapter 3"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter feedback \
    "For Chapter 3 I want more cinematic silence — max 1 speech bubble per panel, add 2-3 mandatory wordless transition panels in the middle of the chapter (environment, hands, close-ups of objects), and make the action panels take at least 70% of their canvas with motion blur or particle streaks."

echo
echo "════════════════════════════════════════════════════════════"
echo "  [5/7] chapter 3 new — The Truth (with evolved style)"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter new \
    "The Truth. Inside the derelict data temple, dust motes floating in cyan Ghost-light. Kira confronts Ghost: 'What are you?' Ghost, in silent cinematic beats, reveals — through holographic projections around them — that IT IS the data chip. The buyer wants to lock Ghost forever inside a corporate server. Silent montage: Ghost's memory fragments floating around Kira; Kira's cybernetic arm pulsing in sympathy; Kira's hand hovering over the chip case on her belt. Final panel: Kira's hand closes around the chip — but does she deliver it or break it? The choice hangs."

echo
echo "════════════════════════════════════════════════════════════"
echo "  [6/7] chapter 3 render"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter render 3 --seed 42

echo
echo "════════════════════════════════════════════════════════════"
echo "  [7/7] series export"
echo "════════════════════════════════════════════════════════════"
uv run comic series export

echo
echo "=== artifacts ==="
for c in 01 02 03; do
  echo "-- chapter $c --"
  ls -la "$HERMES_COMIC_WORKSPACE/chapters/$c/" | grep -v "^total\|\.\\.$\|\\.$"
done
echo "-- series --"
ls -la "$HERMES_COMIC_WORKSPACE/series.png" 2>/dev/null

echo
echo "[done] Neon & Ash full Phase 2.5/3 complete"
echo "→ open:"
echo "  C:\\Users\\EREN\\Desktop\\nous\\hermes-comic\\workspaces\\neon-and-ash\\series.png"
echo "  C:\\Users\\EREN\\Desktop\\nous\\hermes-comic\\workspaces\\neon-and-ash\\chapters\\02\\chapter.png"
echo "  C:\\Users\\EREN\\Desktop\\nous\\hermes-comic\\workspaces\\neon-and-ash\\chapters\\03\\chapter.png"
