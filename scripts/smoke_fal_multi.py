"""fal.ai flux-pro/kontext/multi smoke — two Pillow-generated fixtures."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import fal_client
from PIL import Image, ImageDraw

KEY = os.environ.get("FAL_KEY")
if not KEY:
    print("[FAIL] FAL_KEY not set")
    sys.exit(1)

FIX_DIR = Path("scripts/fixtures")
REF_A = FIX_DIR / "kontext_multi_a.png"
REF_B = FIX_DIR / "kontext_multi_b.png"
OUT = Path("workspaces/red-vs-blue/gate/smoke_fal_multi.png")


def make_fixture(path: Path, bg: tuple[int, int, int], shape_color: tuple[int, int, int]) -> None:
    if path.exists() and path.stat().st_size > 1024:
        print(f"fixture exists: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (512, 512), bg)
    d = ImageDraw.Draw(img)
    d.rectangle([100, 100, 412, 412], fill=shape_color)
    img.save(path, "PNG")
    print(f"created: {path} ({path.stat().st_size:,} bytes)")


def main() -> int:
    # Two simple distinct fixtures
    make_fixture(REF_A, bg=(60, 20, 30), shape_color=(220, 40, 80))
    make_fixture(REF_B, bg=(20, 30, 80), shape_color=(80, 180, 220))

    print("uploading both to fal storage...")
    url_a = fal_client.upload_file(str(REF_A))
    url_b = fal_client.upload_file(str(REF_B))
    print(f"  A: {url_a}")
    print(f"  B: {url_b}")

    print("POST https://fal.run/fal-ai/flux-pro/kontext/multi ...")
    r = httpx.post(
        "https://fal.run/fal-ai/flux-pro/kontext/multi",
        headers={"Authorization": f"Key {KEY}", "Content-Type": "application/json"},
        json={
            "prompt": "Two elements composed together in anime webtoon style, clean art",
            "image_urls": [url_a, url_b],
            "num_images": 1,
            "output_format": "png",
        },
        timeout=240,
    )
    if r.status_code != 200:
        print(f"[FAIL] HTTP {r.status_code}: {r.text[:500]}")
        print("note: kontext/multi is experimental")
        return 1

    data = r.json()
    url = data["images"][0]["url"]
    print(f"[OK] kontext/multi output: {url}")

    img_bytes = httpx.get(url, timeout=60).content
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(img_bytes)
    print(f"[OK] saved {OUT} ({len(img_bytes):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
