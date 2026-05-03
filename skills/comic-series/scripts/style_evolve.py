"""Style evolver skill script — thin wrapper over hermes_comic.style_evolve.

Usage:
    HERMES_COMIC_WORKSPACE=./workspaces/red-vs-blue \\
        python style_evolve.py --feedback "less dialogue, bigger action panels"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_here = Path(__file__).resolve()
_repo = _here.parents[3]
sys.path.insert(0, str(_repo))

from hermes_comic.style_evolve import run  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feedback", type=str, required=True)
    args = ap.parse_args()

    try:
        out = run(feedback=args.feedback)
    except Exception as e:
        print(f"[FAIL] {e}")
        return 1

    print(f"[style_evolve] snapshot → {out['snapshot']}")
    print(f"[style_evolve] change summary: {out['change_summary']}")
    print(f"[style_evolve] tokens: in={out['tokens_in']} out={out['tokens_out']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
