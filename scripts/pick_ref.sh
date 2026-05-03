#!/usr/bin/env bash
# Usage: bash scripts/pick_ref.sh <character> <pose> <candidate_number>
# Uses HERMES_COMIC_WORKSPACE env var (default: workspaces/red-vs-blue) to locate candidates.
set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "usage: $0 <character> <pose> <N>"
    echo "  example: $0 kira portrait 2"
    echo "  (export HERMES_COMIC_WORKSPACE=./workspaces/neon-and-ash first)"
    exit 1
fi

WS="${HERMES_COMIC_WORKSPACE:-workspaces/red-vs-blue}"
CHAR=$1
POSE=$2
N=$3

SRC="$WS/characters/${CHAR}/_candidates/${POSE}_${N}.png"
DST="$WS/characters/${CHAR}/${POSE}.png"

if [ ! -f "$SRC" ]; then
    echo "[FAIL] candidate missing: $SRC"
    exit 1
fi

cp "$SRC" "$DST"
echo "[OK] $CHAR/$POSE → candidate $N ($(stat -c%s "$DST") bytes)"
echo "  $SRC → $DST"
