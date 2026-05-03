"""Plan B helper — upload a locally-saved LoRA .safetensors to fal storage.

Use when Civitai rate-limits / auth-gates the direct download URL.

Flow:
  1. Download the LoRA .safetensors manually in your browser (Civitai model page).
  2. Save it locally, e.g. ~/loras/manhwa.safetensors
  3. Run:  uv run python scripts/upload_lora.py ~/loras/manhwa.safetensors
  4. Copy the printed fal URL into .env as e.g. MANHWA_LORA_URL=...
  5. Re-run scripts/test_styled_render.py

The fal.media URL is stable across calls as long as the file stays in fal storage.
"""
from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

import fal_client

MAX_ATTEMPTS = 4


def _upload_with_retry(path: str) -> str:
    last_err: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"  attempt {attempt}/{MAX_ATTEMPTS}...")
            return fal_client.upload_file(path)
        except Exception as e:
            last_err = e
            wait = 5 * attempt
            print(f"    failed: {type(e).__name__}: {str(e)[:160]}")
            if attempt < MAX_ATTEMPTS:
                print(f"    retrying in {wait}s...")
                time.sleep(wait)
    raise RuntimeError(f"upload failed after {MAX_ATTEMPTS} attempts") from last_err


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: upload_lora.py <path-to-safetensors>")
        return 1

    src = Path(sys.argv[1]).expanduser().resolve()
    if not src.exists():
        print(f"[FAIL] file not found: {src}")
        return 1
    if src.stat().st_size < 1_000_000:
        print(f"[WARN] file very small ({src.stat().st_size:,} bytes) — is this a real LoRA?")

    # Stage to WSL native fs if the file is on /mnt/c (Windows bridge is slow)
    work = src
    if str(src).startswith("/mnt/"):
        stage = Path.home() / "loras" / src.name
        stage.parent.mkdir(parents=True, exist_ok=True)
        if not stage.exists() or stage.stat().st_size != src.stat().st_size:
            print(f"staging to WSL native fs: {stage}")
            shutil.copy2(src, stage)
        work = stage

    print(
        f"uploading {work.name} "
        f"({work.stat().st_size / 1_000_000:.1f} MB) to fal storage..."
    )
    url = _upload_with_retry(str(work))

    print(f"\n[OK] LoRA URL: {url}")
    print("\nAdd to .env (pick the key matching which LoRA this is):")
    print(f"  MANHWA_LORA_URL={url}")
    print(f"  SOLO_LEVELING_LORA_URL={url}")
    print("\nThen re-run:")
    print("  set -a && source .env && set +a")
    print("  uv run python scripts/test_styled_render.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
