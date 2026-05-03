#!/usr/bin/env bash
set -euo pipefail
cd /mnt/c/Users/EREN/Desktop/nous/hermes-comic
bash scripts/install_skill.sh > /dev/null 2>&1
export PATH="$HOME/.local/bin:$PATH"

echo "=== chapter new --help ==="
uv run comic chapter new --help | head -15
echo
echo "=== chapter render --help ==="
uv run comic chapter render --help | head -12
echo
echo "=== gen_references --help ==="
uv run python scripts/gen_references.py --help | head -20
