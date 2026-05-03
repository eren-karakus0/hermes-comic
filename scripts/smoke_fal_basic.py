"""fal.ai basic text2image diagnostic — no reference, cheap (~$0.003).

Isolates: "is fal.run generally up?" from "is kontext endpoint specifically down?"
If this passes and kontext 504s, it's likely a kontext-specific outage.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

KEY = os.environ.get("FAL_KEY")
if not KEY:
    print("[FAIL] FAL_KEY not set")
    sys.exit(1)

OUT = Path("workspaces/red-vs-blue/gate/smoke_fal_basic.png")

print("POST https://fal.run/fal-ai/flux/schnell ...")
r = httpx.post(
    "https://fal.run/fal-ai/flux/schnell",
    headers={"Authorization": f"Key {KEY}", "Content-Type": "application/json"},
    json={
        "prompt": "A cheerful anime character waving, vibrant colors, webtoon style",
        "num_images": 1,
        "image_size": "square_hd",
    },
    timeout=180,
)
if r.status_code != 200:
    print(f"[FAIL] HTTP {r.status_code}: {r.text[:500]}")
    print("if 504 here too → fal.run general outage, wait 10 min and retry")
    sys.exit(1)

data = r.json()
url = data["images"][0]["url"]
print(f"[OK] fal basic output url: {url}")

img_bytes = httpx.get(url, timeout=60).content
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_bytes(img_bytes)
print(f"[OK] saved {OUT} ({len(img_bytes):,} bytes)")
