#!/usr/bin/env bash
# Verify comic CLI auto-loads .env without explicit sourcing.
set -euo pipefail

cd /mnt/c/Users/EREN/Desktop/nous/hermes-comic
bash scripts/install_skill.sh > /dev/null 2>&1 || true
export PATH="$HOME/.local/bin:$PATH"

echo "=== clean shell, no env sourcing, just cd + PATH ==="
# Unset any env vars that might leak from parent shell
unset OPENROUTER_API_KEY KIMI_API_KEY FAL_KEY CIVITAI_TOKEN MANHWA_LORA_URL 2>/dev/null || true

echo "pre-flight — these should all be UNSET:"
for v in OPENROUTER_API_KEY KIMI_API_KEY FAL_KEY; do
    echo "  $v = ${!v:-<unset>}"
done
echo

echo "=== running: uv run comic series propose ... ==="
uv run comic series propose "a wandering clockmaker mending time while shadows chase him" 2>&1 | head -25
