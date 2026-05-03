"""A/B test — old (generic flux/dev) vs new (flux-lora + Civitai LoRA + style stack).

Generates a single Kira panel in both pipelines so we can eyeball the quality jump
before scaling up. Expected cost: ~$0.08 total ($0.04 old + $0.04 new).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hermes_comic.flux_client import FluxClient  # noqa: E402
from hermes_comic.style import (  # noqa: E402
    build_prompt,
    get_default_lora_stack,
    image_size_for,
)

if not os.environ.get("FAL_KEY"):
    print("[FAIL] FAL_KEY not set")
    sys.exit(1)

OUT_DIR = Path("workspaces/style-tests")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Rich Kira description — exercise character detail density
KIRA_DESC = (
    "Kira, 23-year-old female courier, short platinum silver undercut hair with "
    "a single magenta streak over left eye, sharp grey determined eyes, wearing "
    "a black leather biker jacket with glowing electric purple trim along every seam, "
    "red-tinted mirror visor goggles pushed up on forehead, cyan-lit cybernetic left arm "
    "with matte black plating and bright cyan circuit patterns running from elbow to knuckles. "
    "Riding an antique-style motorcycle through a rain-slick neon cyberpunk megacity at night, "
    "vibrant magenta and cyan neon sign reflections on wet pavement, volumetric light through fog, "
    "towering holographic ads in background"
)

SEED = 42


def main() -> int:
    client = FluxClient()

    # ─── TEST 1: OLD pipeline (generic) ───────────────────────────────────
    print("[1/2] OLD pipeline — flux/dev + generic 'anime webtoon' suffix")
    old_prompt = (
        f"{KIRA_DESC}. "
        "Anime webtoon art style, clean line art, vibrant colors, soft cel shading."
    )
    old_bytes = client.render_text2image_basic(
        old_prompt,
        image_size={"width": 1024, "height": 1280},
        seed=SEED,
    )
    old_out = OUT_DIR / "kira_01_old.png"
    old_out.write_bytes(old_bytes)
    print(f"      saved {old_out} ({len(old_bytes):,} bytes)\n")

    # ─── TEST 2: NEW pipeline (LoRA + artist stack) ───────────────────────
    print("[2/2] NEW pipeline — flux-lora + Manhwa/Webtoon LoRA + artist stack")
    new_prompt = build_prompt(KIRA_DESC, camera_framing="action")
    loras = get_default_lora_stack()
    print(f"      LoRA URL: {loras[0].path[:80]}...")
    new_bytes = client.render_styled_text2image(
        prompt=new_prompt,
        loras=loras,
        image_size=image_size_for("action"),
        seed=SEED,
        guidance_scale=3.5,
    )
    new_out = OUT_DIR / "kira_02_new.png"
    new_out.write_bytes(new_bytes)
    print(f"      saved {new_out} ({len(new_bytes):,} bytes)\n")

    print("=" * 60)
    print("Compare side-by-side in Windows Explorer:")
    print(f"  OLD: {old_out}")
    print(f"  NEW: {new_out}")
    print("\nIf NEW looks more professional/manhwa-styled → proceed to full upgrade")
    print("If no difference or worse → we tune LoRA scale + prompt weights")
    return 0


if __name__ == "__main__":
    sys.exit(main())
