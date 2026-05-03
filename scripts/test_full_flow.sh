#!/usr/bin/env bash
# Verify auto-env + series new + chapter propose end-to-end from CLEAN SHELL
# (mimics what Hermes's terminal tool invocations look like).
set -euo pipefail

cd /mnt/c/Users/EREN/Desktop/nous/hermes-comic
bash scripts/install_skill.sh > /dev/null 2>&1 || true
export PATH="$HOME/.local/bin:$PATH"

# Isolated test workspace (don't pollute existing ones)
export HERMES_COMIC_WORKSPACE="$(pwd)/workspaces/auto-env-test"
rm -rf "$HERMES_COMIC_WORKSPACE"
mkdir -p "$HERMES_COMIC_WORKSPACE"

echo "=== clean shell — no env sourcing ==="
unset OPENROUTER_API_KEY KIMI_API_KEY FAL_KEY CIVITAI_TOKEN MANHWA_LORA_URL 2>/dev/null || true
echo "  OPENROUTER_API_KEY = ${OPENROUTER_API_KEY:-<unset>}"

echo
echo "=== [1/2] comic series new (auto-loads .env, 10000 max_tokens) ==="
uv run comic series new \
    "Across dying dimensions, the last Horologist of the Celestial Mechanism wanders with a toolkit of stellar matter, repairing fractures caused by the Shaded Ones — ancient entropy deities who devour linear time. A mythic epic of cosmic maintenance: fixing a watch might mean re-aligning the orbit of a sun." \
    --title "tenth-hour-chronicles"

echo
echo "=== [2/2] comic chapter propose ==="
uv run comic chapter propose "The Horologist arrives in a dying system where a shadowed entity is slowly freezing time around a child" 2>&1 | head -35

echo
echo "=== artifacts ==="
ls -la "$HERMES_COMIC_WORKSPACE/canon/"
echo
echo "[done] pipeline works from clean shell"
