#!/usr/bin/env bash
# Phase 3 E2E — full Red vs Blue production (3 chapters + self-improving skill + continuity).
#
# Cost estimate:
#   series new           ~$0.01
#   3 × chapter new      ~$0.04
#   3 × chapter render   ~$0.75  (18 panels × $0.04)
#   2 × continuity check ~$0.04  (ch2 multimodal, ch3 text)
#   1 × style evolve     ~$0.01
#   1 × plot twist       ~$0.08  (k2-thinking)
#   series export        $0
#   ─────────────────────────────
#   total                ~$0.93
set -euo pipefail

WS="$(pwd)/workspaces/red-vs-blue"
export HERMES_COMIC_WORKSPACE="$WS"

# Keep existing characters/ (Phase 0 references); wipe canon/chapters to start fresh
rm -rf "$WS/canon" "$WS/chapters" "$WS/history"
mkdir -p "$WS/canon" "$WS/chapters" "$WS/history"

echo "=== workspace: $WS ==="
echo "character refs:"
ls "$WS/characters/ignara/" "$WS/characters/theros/" | grep -v _candidates
echo

echo "════════════════════════════════════════════════════════════"
echo "  [1/10] comic series new"
echo "════════════════════════════════════════════════════════════"
uv run comic series new \
    "Two planets locked in eternal conflict. Pyraleth — red-haired conquerors with laser vision, led by Princess Ignara who carries an ancestral gold wrist gauntlet and wears the Crown of Embers. Azura — blue-haired peacekeepers with psionic empathy, protected by warrior Theros who wields a glowing cyan psi-blade in his left hand. Ignara and Theros are destined to meet across the burning void, and their encounter will either end the war or destroy both worlds." \
    --title "red-vs-blue"

echo
echo "════════════════════════════════════════════════════════════"
echo "  [2/10] comic chapter new  (Chapter 1 — Origins)"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter new \
    "Origins. Princess Ignara awakens to her laser vision during a royal Pyraleth crystal ceremony, her Crown of Embers glowing with inherited power. Meanwhile, warrior Theros patrols the Azura border with his cyan psi-blade, sensing a surge of distant heat pierce the peaceful horizon."

echo
echo "════════════════════════════════════════════════════════════"
echo "  [3/10] comic chapter render 1"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter render 1 --seed 42

echo
echo "════════════════════════════════════════════════════════════"
echo "  [4/10] comic chapter new  (Chapter 2 — Collision)"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter new \
    "Collision. Driven by curiosity about the power she now wields, Ignara crosses the void into Azura's sky, cloak blazing. Theros intercepts her with his psi-blade raised. The two face each other for the first time — tense, uncertain, both armed — and instead of battle, a charged dialogue erupts that neither expected."

echo
echo "════════════════════════════════════════════════════════════"
echo "  [5/10] comic chapter render 2"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter render 2 --seed 42

echo
echo "════════════════════════════════════════════════════════════"
echo "  [6/10] comic chapter continuity 2 --multimodal  (flagship demo)"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter continuity 2 --multimodal

echo
echo "════════════════════════════════════════════════════════════"
echo "  [7/10] comic chapter feedback  (self-improving skill)"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter feedback \
    "I want Chapter 3 to feel more cinematic: less dialogue (≤1 bubble per panel maximum), bigger action panels (each action panel ≥70% of its canvas with dynamic motion), and the pacing should lean into silent dramatic beats."

echo
echo "════════════════════════════════════════════════════════════"
echo "  [8/10] comic chapter twist 3  (Kimi K2-Thinking plot twist proposer)"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter twist 3

echo
echo "════════════════════════════════════════════════════════════"
echo "  [9/10] comic chapter new  (Chapter 3 — Pivot, with evolved style)"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter new \
    "Pivot. After their charged encounter, Ignara makes an impossible choice — she turns her back on Pyraleth and seeks sanctuary with Theros on Azura. The chapter opens with a silent montage: Ignara's Crown of Embers falling from her head; a lone flight across the void; landing on Azura soil. Theros meets her without words. The final panel: two hands — one gold-gauntleted, one silver-gauntleted — nearly touching."

echo
echo "════════════════════════════════════════════════════════════"
echo "  [10/10] comic chapter render 3  +  series export"
echo "════════════════════════════════════════════════════════════"
uv run comic chapter render 3 --seed 42
uv run comic series export

echo
echo "════════════════════════════════════════════════════════════"
echo "  artifacts"
echo "════════════════════════════════════════════════════════════"
echo "-- canon --"
ls -la "$WS/canon/"
echo
echo "-- chapters --"
for c in 01 02 03; do
  echo "  chapter $c:"
  ls "$WS/chapters/$c/" 2>/dev/null | sed 's/^/    /'
done
echo
echo "-- history (style-card + canon snapshots) --"
ls -la "$WS/history/" 2>/dev/null | head -20
echo
echo "-- series.png --"
ls -la "$WS/series.png" 2>/dev/null

echo
echo "[done] Phase 3 complete."
echo "→ open in Windows Explorer:"
echo "  C:\\Users\\EREN\\Desktop\\nous\\hermes-comic\\workspaces\\red-vs-blue\\series.png"
echo "  C:\\Users\\EREN\\Desktop\\nous\\hermes-comic\\workspaces\\red-vs-blue\\chapters\\01\\chapter.png"
echo "  (... chapters 02, 03 ...)"
