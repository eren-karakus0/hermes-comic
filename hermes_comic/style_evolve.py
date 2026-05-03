"""Patch canon/style-card.md from user feedback via Kimi K2.5.

Snapshots current style-card to history/ before patching; bumps version.
"""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from hermes_comic import canon, prompts
from hermes_comic.kimi_client import KimiClient


def run(feedback: str) -> dict[str, Any]:
    current = canon.read_canon("style-card")
    if not current.strip():
        raise RuntimeError("style-card.md is empty — initialize series first")

    # history snapshot (timestamped)
    hist = canon.get_workspace() / "history"
    hist.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    snap = hist / f"style-card-{stamp}.md"
    snap.write_text(current, encoding="utf-8")

    client = KimiClient()
    messages = [
        {"role": "system", "content": prompts.STYLE_EVOLVER_SYSTEM},
        {
            "role": "user",
            "content": prompts.STYLE_EVOLVER_USER_TEMPLATE.format(
                current_style_card=current,
                feedback=feedback,
                today=date.today().isoformat(),
            ),
        },
    ]
    result = client.complete_json(messages, temperature=0.3, max_tokens=4000)

    new_sc = result.get("new_style_card")
    if not new_sc:
        raise RuntimeError("Kimi response missing 'new_style_card'")

    canon.write_canon("style-card", new_sc)
    return {
        "snapshot": str(snap),
        "change_summary": result.get("change_summary", ""),
        "tokens_in": client.total_input_tokens,
        "tokens_out": client.total_output_tokens,
    }
