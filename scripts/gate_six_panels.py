"""D2: 6-panel character consistency gate.

Tests whether fal.ai Flux Kontext preserves character DNA across:
  - Ignara single-ref (3 panels: portrait close-up, action, dialogue close-up)
  - Theros single-ref (2 panels: portrait, action pose)
  - Multi-character panel (1 panel: Ignara + Theros via kontext/multi)

Total cost: 5 × $0.04 + 1 × $0.04 = ~$0.24
"""
from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import fal_client

KEY = os.environ.get("FAL_KEY")
if not KEY:
    print("[FAIL] FAL_KEY not set")
    sys.exit(1)

CHAR_DIR = Path("workspaces/red-vs-blue/characters")
OUT_DIR = Path("workspaces/red-vs-blue/gate")


@dataclass
class Panel:
    pid: str            # A, B, C, D, E, F
    label: str          # human-readable
    prompt: str
    refs: list[str]     # local paths; singular = kontext, 2+ = kontext/multi
    fal_urls: list[str] = field(default_factory=list)
    out: Path = field(init=False)

    def __post_init__(self) -> None:
        self.out = OUT_DIR / f"panel_{self.pid.lower()}.png"


PANELS = [
    Panel(
        pid="A",
        label="Ignara portrait close-up",
        prompt=(
            "Ignara smiling with determination, close-up head and shoulders, "
            "crown and gold wrist gauntlet clearly visible, "
            "anime webtoon style, soft lighting, looking at camera"
        ),
        refs=[str(CHAR_DIR / "ignara" / "portrait.png")],
    ),
    Panel(
        pid="B",
        label="Ignara mid-flight action",
        prompt=(
            "Ignara mid-flight over Pyraleth red plains at dusk, "
            "gold wrist gauntlet glowing, crown visible, cape flowing, "
            "red laser light radiating from eyes, dynamic composition, "
            "anime webtoon style"
        ),
        refs=[str(CHAR_DIR / "ignara" / "action.png")],
    ),
    Panel(
        pid="C",
        label="Theros portrait",
        prompt=(
            "Theros determined expression, close-up, "
            "glowing cyan psi-blade hilt visible in left hand, "
            "cobalt tunic with silver psi-armor plates, "
            "anime webtoon style, soft lighting"
        ),
        refs=[str(CHAR_DIR / "theros" / "portrait.png")],
    ),
    Panel(
        pid="D",
        label="Theros leaping with blade",
        prompt=(
            "Theros leaping with glowing cyan psi-blade raised overhead in left hand, "
            "cobalt tunic and blue hair flowing, silver psi-armor plates catching light, "
            "dynamic battle stance, anime webtoon style"
        ),
        refs=[str(CHAR_DIR / "theros" / "action.png")],
    ),
    Panel(
        pid="E",
        label="Ignara + Theros dialogue (MULTI)",
        prompt=(
            "Ignara with red hair and gold armor facing Theros with blue hair and cobalt tunic, "
            "tense dialogue on Pyraleth cliff at dusk, both characters in same frame, "
            "three-quarter view, anime webtoon style, cinematic composition"
        ),
        refs=[
            str(CHAR_DIR / "ignara" / "portrait.png"),
            str(CHAR_DIR / "theros" / "portrait.png"),
        ],
    ),
    Panel(
        pid="F",
        label="Ignara dialogue close-up (bubble space)",
        prompt=(
            "Ignara speaking with determination, mouth slightly open mid-word, "
            "head and upper torso framed with empty space above for speech bubble, "
            "crown and gold gauntlet visible, amber eyes glowing, "
            "anime webtoon style"
        ),
        refs=[str(CHAR_DIR / "ignara" / "portrait.png")],
    ),
]


def render(panel: Panel) -> tuple[Panel, bool, str]:
    is_multi = len(panel.fal_urls) > 1
    endpoint = (
        "https://fal.run/fal-ai/flux-pro/kontext/multi"
        if is_multi
        else "https://fal.run/fal-ai/flux-pro/kontext"
    )
    payload = {
        "prompt": panel.prompt,
        "num_images": 1,
        "output_format": "png",
    }
    if is_multi:
        payload["image_urls"] = panel.fal_urls
    else:
        payload["image_url"] = panel.fal_urls[0]

    try:
        r = httpx.post(
            endpoint,
            headers={"Authorization": f"Key {KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=240,
        )
        if r.status_code != 200:
            return panel, False, f"HTTP {r.status_code}: {r.text[:200]}"
        url = r.json()["images"][0]["url"]
        img_bytes = httpx.get(url, timeout=60).content
        panel.out.parent.mkdir(parents=True, exist_ok=True)
        panel.out.write_bytes(img_bytes)
        return panel, True, f"saved {len(img_bytes):,} bytes"
    except Exception as e:
        return panel, False, f"exception: {e}"


def main() -> int:
    # 1. Sanity: verify all reference files exist
    for p in PANELS:
        for ref in p.refs:
            if not Path(ref).exists():
                print(f"[FAIL] missing reference: {ref}")
                return 1

    # 2. Upload unique references to fal storage (cached)
    print("uploading references to fal storage...")
    unique_refs = sorted({ref for p in PANELS for ref in p.refs})
    url_cache: dict[str, str] = {}
    for ref in unique_refs:
        url = fal_client.upload_file(ref)
        url_cache[ref] = url
        print(f"  {Path(ref).name} → {url}")

    # 3. Populate fal_urls per panel
    for p in PANELS:
        p.fal_urls = [url_cache[r] for r in p.refs]

    # 4. Render in parallel (concurrency=3)
    print("\nrendering 6 panels...")
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(render, p): p for p in PANELS}
        failed: list[tuple[Panel, str]] = []
        for f in as_completed(futures):
            p, ok, msg = f.result()
            status = "OK" if ok else "FAIL"
            tag = "MULTI" if len(p.fal_urls) > 1 else "single"
            print(f"  [{p.pid}] {status} ({tag}) {p.label} — {msg}")
            if not ok:
                failed.append((p, msg))

    print()
    if failed:
        print(f"[WARN] {len(failed)} failures")
        return 1

    print("[done] 6 panels saved to workspaces/red-vs-blue/gate/")
    print()
    print("Review each panel + check consistency vs references:")
    for p in PANELS:
        print(f"  panel_{p.pid.lower()}.png — {p.label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
