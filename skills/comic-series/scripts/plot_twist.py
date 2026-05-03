"""Plot twist proposer skill script — thin wrapper over hermes_comic.plot_twist.

Usage:
    HERMES_COMIC_WORKSPACE=./workspaces/red-vs-blue \\
        python plot_twist.py --starting-chapter 3
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_here = Path(__file__).resolve()
_repo = _here.parents[3]
sys.path.insert(0, str(_repo))

from hermes_comic.plot_twist import run  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--starting-chapter", type=int, required=True)
    args = ap.parse_args()

    try:
        result = run(starting_chapter=args.starting_chapter)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    alternatives = result.get("alternatives", [])
    print(
        f"[plot_twist] {len(alternatives)} alternatives for chapter "
        f"{args.starting_chapter}+ generated via Kimi K2-Thinking"
    )
    for i, alt in enumerate(alternatives, 1):
        print(f"\n── [{i}] {alt.get('title', 'untitled')} ──")
        print(f"  twist: {alt.get('twist')}")
        for co in alt.get("chapter_outlines", []):
            print(f"    Ch {co.get('n')}: {co.get('beat', '')[:120]}")

    print(f"\n[plot_twist] saved → {result.get('_persisted_to')}")
    print(f"[plot_twist] tokens: in={result.get('_tokens_in')} out={result.get('_tokens_out')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
