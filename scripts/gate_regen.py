"""D3: Regen determinism test — re-render panel A and B with same prompt + same seed.

Visually compares to panel_a.png and panel_b.png from D2. If character DNA holds
across seeds, kontext pipeline is deterministic enough for production.

Cost: 2 × $0.04 = ~$0.08
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx
import fal_client

# Reuse panel definitions from D2
from gate_six_panels import PANELS, OUT_DIR, CHAR_DIR, KEY


def render_regen(pid: str, seed: int = 42) -> tuple[bool, str]:
    panel = next(p for p in PANELS if p.pid == pid)
    ref_url = fal_client.upload_file(panel.refs[0])
    out = OUT_DIR / f"panel_{pid.lower()}_regen.png"

    try:
        r = httpx.post(
            "https://fal.run/fal-ai/flux-pro/kontext",
            headers={"Authorization": f"Key {KEY}", "Content-Type": "application/json"},
            json={
                "prompt": panel.prompt,
                "image_url": ref_url,
                "num_images": 1,
                "output_format": "png",
                "seed": seed,
            },
            timeout=240,
        )
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}: {r.text[:200]}"
        url = r.json()["images"][0]["url"]
        out.write_bytes(httpx.get(url, timeout=60).content)
        return True, f"saved {out.stat().st_size:,} bytes → {out.name}"
    except Exception as e:
        return False, f"exception: {e}"


def main() -> int:
    print("regenerating panels A and B with seed=42 for determinism check...")
    failed = 0
    for pid in ("A", "B"):
        ok, msg = render_regen(pid, seed=42)
        status = "OK" if ok else "FAIL"
        print(f"  [{pid}_regen] {status} — {msg}")
        if not ok:
            failed += 1

    print()
    if failed:
        return 1

    print("[done] compare side-by-side in Windows Explorer:")
    print("  panel_a.png   vs  panel_a_regen.png")
    print("  panel_b.png   vs  panel_b_regen.png")
    print("(DNA — hair, eyes, accessories — should match closely)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
