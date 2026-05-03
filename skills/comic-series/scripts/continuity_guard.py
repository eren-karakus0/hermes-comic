"""Continuity guard skill script — thin wrapper over hermes_comic.continuity.

Usage:
    HERMES_COMIC_WORKSPACE=./workspaces/red-vs-blue \\
        python continuity_guard.py --chapter 2 --multimodal
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_here = Path(__file__).resolve()
_repo = _here.parents[3]
sys.path.insert(0, str(_repo))

from hermes_comic.continuity import check  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument(
        "--multimodal",
        action="store_true",
        help="Include previous chapter's panel images as visual reference",
    )
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        result = check(chapter_num=args.chapter, multimodal=args.multimodal)
    except FileNotFoundError as e:
        print(f"[FAIL] {e}")
        return 1

    mode = "MULTIMODAL" if result["multimodal"] else "text-only"
    print(
        f"[continuity_guard] chapter {args.chapter:02d} ({mode}, "
        f"{result['images_used']} prior images) via Kimi K2.5"
    )
    print(f"[continuity_guard] report → {result['report_path']}")

    report = result["report"]
    if report.get("clean"):
        print("[OK] no continuity issues detected")
        return 0

    warnings = report.get("warnings", [])
    print(f"[WARN] {len(warnings)} continuity issue(s):")
    for w in warnings:
        panel = w.get("panel")
        prefix = f"panel {panel}" if panel else "global"
        print(f"  - {prefix}: {w.get('issue')}")
        if w.get("fix"):
            print(f"    fix: {w['fix']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
