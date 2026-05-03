"""fal.ai flux-pro/kontext smoke — uses Pillow-generated local fixture.

Why local generation: Wikimedia thumbnails return HTML error pages to some
clients (126 bytes observed). fal kontext requires:
  - valid JPEG/PNG
  - resolution multiple of 16

Pillow gives us a self-contained 512x512 PNG (16×32) with guaranteed validity.
"""
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

LOCAL_REF = Path("scripts/fixtures/kontext_ref.png")
OUT = Path("workspaces/red-vs-blue/gate/smoke_fal_single.png")


def make_fixture() -> None:
    """Generate a 512x512 PNG with simple geometric shapes."""
    if LOCAL_REF.exists() and LOCAL_REF.stat().st_size > 1024:
        print(f"fixture exists: {LOCAL_REF} ({LOCAL_REF.stat().st_size:,} bytes)")
        return
    LOCAL_REF.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (512, 512), (25, 35, 80))  # deep blue bg
    d = ImageDraw.Draw(img)
    # red circle (character stand-in)
    d.ellipse([128, 128, 384, 384], fill=(220, 40, 40))
    # yellow triangle accent
    d.polygon([(256, 180), (210, 320), (302, 320)], fill=(240, 200, 40))
    img.save(LOCAL_REF, "PNG")
    print(f"created fixture: {LOCAL_REF} ({LOCAL_REF.stat().st_size:,} bytes)")


def main() -> int:
    make_fixture()

    print("uploading to fal storage...")
    fal_url = fal_client.upload_file(str(LOCAL_REF))
    print(f"fal storage URL: {fal_url}")

    print("POST https://fal.run/fal-ai/flux-pro/kontext ...")
    r = httpx.post(
        "https://fal.run/fal-ai/flux-pro/kontext",
        headers={"Authorization": f"Key {KEY}", "Content-Type": "application/json"},
        json={
            "prompt": "Transform into bright anime webtoon style, vibrant colors, clean line art",
            "image_url": fal_url,
            "num_images": 1,
            "output_format": "png",
        },
        timeout=240,
    )
    if r.status_code != 200:
        print(f"[FAIL] HTTP {r.status_code}: {r.text[:500]}")
        return 1

    data = r.json()
    url = data["images"][0]["url"]
    print(f"[OK] kontext output: {url}")

    img_bytes = httpx.get(url, timeout=60).content
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(img_bytes)
    print(f"[OK] saved {OUT} ({len(img_bytes):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
