#!/usr/bin/env bash
# Link the comic-series skill into ~/.hermes/skills/ so Hermes' skills toolset discovers it.
# Symlink approach keeps SKILL.md edits live-reflected.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/skills/comic-series"
DST_DIR="$HOME/.hermes/skills"
DST="$DST_DIR/comic-series"

if [ ! -d "$SRC" ]; then
    echo "[FAIL] source skill dir missing: $SRC"
    exit 1
fi

mkdir -p "$DST_DIR"

if [ -L "$DST" ]; then
    echo "[skip] symlink already exists: $DST"
    readlink "$DST"
elif [ -e "$DST" ]; then
    echo "[FAIL] $DST exists and is not a symlink — remove manually first"
    exit 1
else
    ln -s "$SRC" "$DST"
    echo "[OK] linked $DST → $SRC"
fi

echo ""
echo "verify:"
ls -la "$DST_DIR"
cat "$DST/SKILL.md" | head -5
