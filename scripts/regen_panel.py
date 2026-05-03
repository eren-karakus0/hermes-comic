"""One-shot panel regen utility — re-renders a single panel with optional prompt override.

Useful for fixing panels that fal content filter flagged (black images).

Usage:
    HERMES_COMIC_WORKSPACE=./workspaces/red-vs-blue \\
        python scripts/regen_panel.py --chapter 1 --panel 7 --description "softer..."
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hermes_comic import canon  # noqa: E402
from hermes_comic.composer import compose_chapter  # noqa: E402
from hermes_comic.flux_client import FluxClient  # noqa: E402
from hermes_comic.panel_generator import (  # noqa: E402
    PanelJob,
    _panel_prompt,
    _resolve_refs,
    build_jobs,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chapter", type=int, required=True)
    ap.add_argument("--panel", type=int, required=True)
    ap.add_argument("--description", type=str, default=None, help="Override panel description")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--no-recompose", action="store_true")
    args = ap.parse_args()

    spec_path = canon.chapter_dir(args.chapter) / "spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    panel = next((p for p in spec["panels"] if p["n"] == args.panel), None)
    if panel is None:
        print(f"[FAIL] panel {args.panel} not in spec")
        return 1

    if args.description:
        print(f"[regen] overriding description ({len(args.description)} chars)")
        panel["description"] = args.description

    ws = canon.get_workspace()
    refs = _resolve_refs(panel.get("primary_character"), panel.get("reference_pose"), ws)
    out = canon.chapter_dir(args.chapter) / "panels" / f"panel_{args.panel:02d}.png"

    if out.exists():
        old_size = out.stat().st_size
        out.unlink()
        print(f"[regen] removed old {out.name} ({old_size:,} bytes)")

    job = PanelJob(
        n=args.panel,
        description=panel["description"],
        primary_character=panel.get("primary_character"),
        reference_pose=panel.get("reference_pose"),
        references=refs,
        out_path=out,
    )

    print(f"[regen] rendering panel {args.panel} (refs: {job.refs_label})")
    client = FluxClient()
    img = client.render(
        prompt=_panel_prompt(job),
        references=[str(r) for r in refs] if refs else None,
        seed=args.seed,
    )
    out.write_bytes(img)
    print(f"[OK] saved {out} ({len(img):,} bytes)")

    if args.no_recompose:
        return 0

    print("[regen] recomposing chapter.png...")
    jobs = build_jobs(args.chapter)
    dialogues_by_n = {p["n"]: (p.get("dialogue") or []) for p in spec["panels"]}
    panel_paths = [j.out_path for j in jobs]
    dialogues = [dialogues_by_n.get(j.n, []) for j in jobs]
    chapter_out = canon.chapter_dir(args.chapter) / "chapter.png"
    compose_chapter(panel_paths, dialogues, chapter_out)
    print(f"[OK] {chapter_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
