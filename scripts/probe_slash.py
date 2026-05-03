"""Debug skill discovery — why isn't /comic-series registered?"""
import sys
from pathlib import Path


def main() -> None:
    from tools.skills_tool import SKILLS_DIR, _parse_frontmatter, skill_matches_platform, _get_disabled_skill_names

    print(f"SKILLS_DIR = {SKILLS_DIR}")
    print(f"  exists: {SKILLS_DIR.exists()}")
    print(f"  is_dir: {SKILLS_DIR.is_dir()}")
    print()

    print("── iterdir() ──")
    for item in sorted(SKILLS_DIR.iterdir()):
        kind = "symlink" if item.is_symlink() else "dir" if item.is_dir() else "file"
        print(f"  {item.name}  ({kind})  resolve={item.resolve()}")
    print()

    print("── rglob('SKILL.md') — what scan_skill_commands uses ──")
    found = list(SKILLS_DIR.rglob("SKILL.md"))
    print(f"  {len(found)} match(es)")
    for p in found:
        print(f"    {p}")
    print()

    print("── glob via symlink resolve ──")
    for item in sorted(SKILLS_DIR.iterdir()):
        if item.is_symlink() and item.resolve().is_dir():
            resolved_skill = item.resolve() / "SKILL.md"
            print(f"  {item.name} → {resolved_skill.exists()} ({resolved_skill})")
    print()

    print("── disabled skills ──")
    try:
        disabled = _get_disabled_skill_names()
        print(f"  disabled = {disabled}")
    except Exception as e:
        print(f"  error: {e}")
    print()

    # Manually parse our skill
    skill_md = SKILLS_DIR / "comic-series" / "SKILL.md"
    print(f"── manual parse: {skill_md} ──")
    print(f"  exists: {skill_md.exists()}")
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(content)
        print(f"  frontmatter name: {fm.get('name')}")
        print(f"  platform match: {skill_matches_platform(fm)}")
        print(f"  description (first 100): {fm.get('description', '')[:100]}")


if __name__ == "__main__":
    main()
