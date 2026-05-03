"""Propose 3 plot twist alternatives via Kimi K2-Thinking.

Thinking model = longer reasoning = better multi-chapter arc coherence.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermes_comic import canon, prompts
from hermes_comic.kimi_client import KimiClient


def run(starting_chapter: int) -> dict[str, Any]:
    cfiles = canon.read_all_canon()

    # Load all existing chapter specs
    cdir = canon.get_workspace() / "chapters"
    specs: list[dict] = []
    if cdir.exists():
        for child in sorted(cdir.iterdir()):
            if child.is_dir():
                sp = child / "spec.json"
                if sp.exists():
                    specs.append(json.loads(sp.read_text(encoding="utf-8")))

    # Use thinking model for multi-chapter reasoning
    # NOTE: OpenRouter model id for thinking variant
    client = KimiClient(model="moonshotai/kimi-k2-thinking")
    messages = [
        {"role": "system", "content": prompts.PLOT_TWIST_SYSTEM},
        {
            "role": "user",
            "content": prompts.PLOT_TWIST_USER_TEMPLATE.format(
                world_bible=cfiles["world-bible"],
                character_bible=cfiles["character-bible"],
                continuity_log=cfiles["continuity-log"],
                chapter_specs_json=json.dumps(specs, indent=2, ensure_ascii=False),
                starting_chapter=starting_chapter,
                next_chapter=starting_chapter + 1,
                third_chapter=starting_chapter + 2,
            ),
        },
    ]
    result = client.complete_json(messages, temperature=0.8, max_tokens=12000)

    # persist
    out = canon.get_workspace() / f"twist-proposals-ch{starting_chapter:02d}.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    result["_persisted_to"] = str(out)
    result["_tokens_in"] = client.total_input_tokens
    result["_tokens_out"] = client.total_output_tokens
    return result
