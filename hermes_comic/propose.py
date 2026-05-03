"""Creative alternative proposals at each story-building stage.

Used by the Hermes playbook to offer 2-3 variants before committing to any step.
Each function returns a list of alternative dicts.
"""
from __future__ import annotations

from typing import Any

from hermes_comic import canon
from hermes_comic.kimi_client import KimiClient

# ─── series framing proposals ────────────────────────────────────────────

_SERIES_SYSTEM = (
    "You are a creative editor proposing 3 DISTINCT alternative framings for a comic series. "
    "Each alternative must differ meaningfully in tone, genre, angle, or focus — "
    "not just reword the premise. Return STRICT JSON."
)

_SERIES_USER = """Rough premise from user:

{premise}

Propose 3 alternatives in this JSON shape:
{{
  "alternatives": [
    {{
      "title": "<working title>",
      "tagline": "<one-line tonal hook>",
      "framing": "<3-4 sentence expanded premise — a distinct genre/tone/angle take>"
    }},
    ... 3 total
  ]
}}

Ideas for variety (pick any 3 angles):
- dark noir / tragic
- action / epic war
- political intrigue / slow burn
- comedic / lighthearted
- romance / emotional
- cosmic / mythological
- character-study / introspective
- mystery / thriller

Each alternative must be clearly different in genre/tone/focus. Return only JSON.
"""


def propose_series_variants(premise: str) -> list[dict[str, Any]]:
    client = KimiClient()
    messages = [
        {"role": "system", "content": _SERIES_SYSTEM},
        {"role": "user", "content": _SERIES_USER.format(premise=premise)},
    ]
    # Kimi K2.5 is a reasoning model — needs generous budget or output truncates.
    result = client.complete_json(messages, temperature=0.9, max_tokens=8000)
    return result.get("alternatives", [])


# ─── character design proposals ──────────────────────────────────────────

_CHAR_SYSTEM = (
    "You are a comic character designer proposing 3 DISTINCT visual + personality "
    "archetypes for a character. Each must be clearly different — not reworded. "
    "Return STRICT JSON."
)

_CHAR_USER = """Character:
  Name: {name}
  Role: {role}

Story context:
{context}

Propose 3 alternative designs in this JSON shape:
{{
  "alternatives": [
    {{
      "archetype": "<single-phrase archetype, e.g. 'warrior-queen', 'exile-princess', 'cyber-monk'>",
      "visual": "<one sentence: hair, eyes, build, signature clothing and items>",
      "personality": "<one sentence: core personality / trait / motivation>",
      "voice": "<one-line speech pattern or catchphrase style>"
    }},
    ... 3 total
  ]
}}

Each design must be a DIFFERENT archetype (e.g. armored warrior vs scholarly royalty vs street-rogue).
Return only JSON.
"""


def propose_character_designs(
    name: str, role: str = "main character", context: str = ""
) -> list[dict[str, Any]]:
    client = KimiClient()
    messages = [
        {"role": "system", "content": _CHAR_SYSTEM},
        {
            "role": "user",
            "content": _CHAR_USER.format(
                name=name,
                role=role,
                context=context.strip() or "(no canon yet)",
            ),
        },
    ]
    result = client.complete_json(messages, temperature=0.9, max_tokens=8000)
    return result.get("alternatives", [])


# ─── chapter beat proposals ──────────────────────────────────────────────

_CHAPTER_SYSTEM = (
    "You are a story editor proposing 3 DISTINCT chapter beat alternatives. "
    "Each should be a different narrative choice — different focus, different tone, "
    "different dramatic shape. Return STRICT JSON."
)

_CHAPTER_USER = """For chapter {chapter_num} of the series, propose 3 alternative beats.

Series canon:
{canon_context}

User's rough idea for this chapter:
{idea}

Return JSON:
{{
  "alternatives": [
    {{
      "title": "<short chapter title>",
      "hook": "<one-line dramatic hook>",
      "beat": "<3-4 sentence beat — clear sequence of events / character focus / tone>"
    }},
    ... 3 total
  ]
}}

Each alternative must take a DIFFERENT narrative approach (e.g. quiet character focus vs external action vs parallel POVs).
Return only JSON.
"""


def propose_chapter_beats(
    idea: str, chapter_num: int, canon_context: str = ""
) -> list[dict[str, Any]]:
    client = KimiClient()
    messages = [
        {"role": "system", "content": _CHAPTER_SYSTEM},
        {
            "role": "user",
            "content": _CHAPTER_USER.format(
                chapter_num=chapter_num,
                idea=idea,
                canon_context=canon_context.strip() or "(no canon yet)",
            ),
        },
    ]
    result = client.complete_json(messages, temperature=0.9, max_tokens=8000)
    return result.get("alternatives", [])


def current_canon_context(max_chars: int = 3000) -> str:
    """Build a compact canon dump for prompt context (truncated)."""
    parts = []
    for name in ("world-bible", "character-bible", "style-card", "continuity-log"):
        content = canon.read_canon(name).strip()
        if content:
            parts.append(f"## {name}\n{content}")
    joined = "\n\n".join(parts)
    if len(joined) > max_chars:
        joined = joined[:max_chars] + "\n…(truncated)"
    return joined
