"""Continuity check — text-only or multimodal (with previous chapter panel images).

Multimodal mode uploads previous chapter's panel PNGs to fal storage, then passes
those URLs to Kimi K2.5 alongside canon + new chapter spec. This is the flagship
"Kimi sees previous panels" demo scenario.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermes_comic import canon, prompts
from hermes_comic.kimi_client import KimiClient, _parse_json_lenient
from hermes_comic.flux_client import FluxClient


def check(
    chapter_num: int,
    multimodal: bool = False,
    max_prev_images: int = 4,
) -> dict[str, Any]:
    """Run continuity check on chapter <chapter_num>.

    Returns parsed Kimi report + metadata.
    """
    spec_path = canon.chapter_dir(chapter_num) / "spec.json"
    if not spec_path.exists():
        raise FileNotFoundError(f"spec missing: {spec_path}")

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    cfiles = canon.read_all_canon()

    client = KimiClient()

    # Collect previous chapter panel images if multimodal + earlier chapter exists
    image_urls: list[str] = []
    if multimodal and chapter_num > 1:
        prev_panels_dir = canon.chapter_dir(chapter_num - 1) / "panels"
        if prev_panels_dir.exists():
            prev_pngs = sorted(prev_panels_dir.glob("panel_*.png"))[:max_prev_images]
            if prev_pngs:
                fc = FluxClient()
                image_urls = [fc.upload(str(p)) for p in prev_pngs]

    image_note = (
        f"\nPrevious chapter ({chapter_num - 1}) panel images are provided as visual reference. "
        "Verify new chapter preserves visual details (hair, accessories, costumes) shown in those images."
        if image_urls
        else ""
    )

    user_text = prompts.CONTINUITY_CHECK_USER_TEMPLATE.format(
        character_bible=cfiles["character-bible"],
        continuity_log=cfiles["continuity-log"],
        chapter_spec_json=json.dumps(spec, indent=2, ensure_ascii=False),
        image_note=image_note,
    )

    if image_urls:
        response = client.complete_multimodal(
            text=user_text,
            image_urls=image_urls,
            system=prompts.CONTINUITY_CHECK_SYSTEM,
            temperature=0.2,
            max_tokens=6000,
        )
        report = _parse_json_lenient(response.strip()) if response.strip() else {
            "clean": False,
            "warnings": [{"panel": None, "issue": "kimi multimodal returned empty", "fix": "retry"}],
        }
    else:
        messages = [
            {"role": "system", "content": prompts.CONTINUITY_CHECK_SYSTEM},
            {"role": "user", "content": user_text},
        ]
        report = client.complete_json(messages, temperature=0.2, max_tokens=6000)

    out = canon.chapter_dir(chapter_num) / "continuity_report.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "report": report,
        "report_path": str(out),
        "multimodal": bool(image_urls),
        "images_used": len(image_urls),
        "tokens_in": client.total_input_tokens,
        "tokens_out": client.total_output_tokens,
    }
