#!/usr/bin/env bash
# Install/refresh the comic-series skill at ~/.hermes/skills/comic-series/
# by COPYING (not symlinking — Python 3.11 rglob doesn't traverse symlinks).
# Re-run after any SKILL.md or scripts/ changes.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$REPO_ROOT/skills/comic-series"
DST="$HOME/.hermes/skills/comic-series"

if [ ! -d "$SRC" ]; then
    echo "[FAIL] source skill dir missing: $SRC"
    exit 1
fi

# Remove existing (symlink or dir) — safe since DST is our managed path
if [ -L "$DST" ] || [ -e "$DST" ]; then
    rm -rf "$DST"
    echo "[clean] removed old $DST"
fi

mkdir -p "$(dirname "$DST")"
cp -r "$SRC" "$DST"
echo "[OK] copied $SRC → $DST"

echo ""
echo "verify:"
ls -la "$DST"
echo "----"
find "$DST" -name "SKILL.md"
