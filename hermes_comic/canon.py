"""Workspace canon file I/O — 4 files + history snapshots.

Path contract (set by CLI before skill invocations):
  $HERMES_COMIC_WORKSPACE/
    canon/{world-bible,character-bible,style-card,continuity-log}.md
    chapters/<NN>/{spec.json, panels/*.png, chapter.png}
    history/ch<NN>-before.md   (snapshot of canon before chapter N generation)

HERMES_COMIC_WORKSPACE env var defaults to ./workspaces/red-vs-blue.
"""
from __future__ import annotations

import os
from pathlib import Path

CANON_FILES = ["world-bible", "character-bible", "style-card", "continuity-log"]


def get_workspace() -> Path:
    env = os.environ.get("HERMES_COMIC_WORKSPACE")
    if env:
        return Path(env).resolve()
    return Path("workspaces/red-vs-blue").resolve()


def canon_dir() -> Path:
    return get_workspace() / "canon"


def history_dir() -> Path:
    return get_workspace() / "history"


def chapter_dir(chapter_num: int) -> Path:
    return get_workspace() / "chapters" / f"{chapter_num:02d}"


def read_canon(name: str) -> str:
    path = canon_dir() / f"{name}.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_canon(name: str, content: str) -> Path:
    if name not in CANON_FILES:
        raise ValueError(f"unknown canon file: {name!r} (valid: {CANON_FILES})")
    path = canon_dir() / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def read_all_canon() -> dict[str, str]:
    return {n: read_canon(n) for n in CANON_FILES}


def snapshot_before(chapter_num: int) -> Path:
    """Concatenate current canon state into history/ch<NN>-before.md for git diff later."""
    hist = history_dir()
    hist.mkdir(parents=True, exist_ok=True)
    out = hist / f"ch{chapter_num:02d}-before.md"
    parts = [f"# Canon snapshot before chapter {chapter_num:02d}\n"]
    for name in CANON_FILES:
        parts.append(f"## ==== {name} ====\n\n{read_canon(name)}\n")
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def next_chapter_number() -> int:
    """Scan chapters/ dir; return next NN (1 if none)."""
    cdir = get_workspace() / "chapters"
    if not cdir.exists():
        return 1
    nums: list[int] = []
    for p in cdir.iterdir():
        if not p.is_dir():
            continue
        try:
            nums.append(int(p.name))
        except ValueError:
            continue
    return (max(nums) + 1) if nums else 1


def canon_is_initialized() -> bool:
    """All 4 canon files exist + world-bible non-empty."""
    for name in CANON_FILES:
        p = canon_dir() / f"{name}.md"
        if not p.exists():
            return False
    return len(read_canon("world-bible").strip()) > 0
