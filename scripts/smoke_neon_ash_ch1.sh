#!/usr/bin/env bash
# Phase 2.5 — Neon & Ash Chapter 1 test (Kira + Ghost)
set -euo pipefail

cd /mnt/c/Users/EREN/Desktop/nous/hermes-comic
export PATH="$HOME/.local/bin:$PATH"
set -a && source .env && set +a
export HERMES_COMIC_WORKSPACE="$(pwd)/workspaces/neon-and-ash"

echo "=== [1/5] pick references (_1 for all) ==="
for CHAR in kira ghost; do
  for POSE in portrait full_body action; do
    bash scripts/pick_ref.sh "$CHAR" "$POSE" 1
  done
done

echo
echo "=== [2/5] comic series new ==="
uv run comic series new \
    "In a rain-slick neon cyberpunk megacity, Kira — a 23-year-old female courier with short platinum silver hair, a single vivid magenta streak over her left eye, sharp grey eyes, red-tinted mirror visor goggles, a black leather biker jacket with electric purple glowing trim, and a cyan-glowing cybernetic left arm — runs forbidden data chips on her antique motorcycle. Ghost — a translucent pale-blue AI entity that manifests in city holograms as an androgynous figure in flowing white monastic robes with solid cyan void eyes and data particles trailing from its hands — begins appearing uninvited, warning Kira of traps she never saw. Ghost might be her ally. Or Ghost might BE the chip she's carrying, fighting to escape its buyers." \
    --title "neon-and-ash"

echo
echo "=== [3/5] comic chapter new ==="
uv run comic chapter new \
    "Awakening. Kira accepts a new delivery at a dim rain-wet backroom drop-off, the client's face obscured by a mirrored mask. As she rides through neon-drenched alleys toward the recipient, holographic ads flicker above her — and in one, Ghost appears, calling her by name. Kira slams the brakes, stunned, her cybernetic arm flaring cyan. She dismounts and confronts Ghost's reflection in a shop window, demanding answers. Ghost's data particles swirl in reply."

echo
echo "=== [4/5] comic chapter render 1 (hybrid LoRA pipeline) ==="
uv run comic chapter render 1 --seed 42

echo
echo "=== [5/5] artifacts ==="
ls -la "$HERMES_COMIC_WORKSPACE/chapters/01/"
echo
echo "[done] Phase 2.5 Chapter 1 complete"
echo "→ open: C:\\Users\\EREN\\Desktop\\nous\\hermes-comic\\workspaces\\neon-and-ash\\chapters\\01\\chapter.png"
