"""Prompt templates for Kimi calls."""
from __future__ import annotations

# ─── series bible generation ──────────────────────────────────────────────

SERIES_SYSTEM = (
    "You create canonical comic series bibles for webtoon-style stories. "
    "You always return STRICT JSON. No markdown fences, no extra prose."
)

SERIES_USER_TEMPLATE = """Create a canonical bible for this comic series premise:

PREMISE:
{premise}

IMPORTANT: If the premise names specific characters (e.g. "Princess Ignara", "warrior Theros"),
you MUST use those EXACT names in the character_bible. Do NOT invent replacement names for
characters already mentioned. Invent names only for characters NOT named in the premise.

Return a JSON object with exactly these four keys:

{{
  "world_bible": "<markdown with YAML frontmatter>",
  "character_bible": "<markdown with YAML frontmatter>",
  "style_card": "<markdown with YAML frontmatter>",
  "continuity_log": "<markdown with YAML frontmatter>"
}}

Each value must be a markdown string that starts with YAML frontmatter:
---
series: {series_slug}
kind: world-bible
version: 1.0
---

Content rules:
- world_bible: world mechanics, factions, politics, hard rules. ≤400 words.
- character_bible: 2-4 main characters. For each: Name, Age, Role, Visual DNA (hair/eyes/build/signature colors), Key accessories (must-preserve items: weapons/crowns/armor), Voice. ≤500 words total.
- style_card: art direction (medium, palette, line work), paneling defaults, pacing preferences. ≤300 words.
- continuity_log: "# Continuity Log\\n\\n(empty — populated per chapter)" placeholder with frontmatter.

Target audience: webtoon/manga readers. Art style: anime webtoon. Return only JSON.
"""

# ─── chapter spec generation ──────────────────────────────────────────────

CHAPTER_SYSTEM = (
    "You author webtoon chapters from existing canon. "
    "You always return STRICT JSON. No markdown fences, no extra prose."
)

CHAPTER_USER_TEMPLATE = """You have this canon context:

## WORLD BIBLE
{world_bible}

## CHARACTER BIBLE
{character_bible}

## STYLE CARD
{style_card}

## CONTINUITY LOG
{continuity_log}

Generate chapter {chapter_num} from this beat:

BEAT:
{beat}

Return JSON:
{{
  "chapter_number": {chapter_num},
  "title": "<short title>",
  "summary": "<2-3 sentence summary>",
  "panels": [
    {{
      "n": 1,
      "description": "<visual description for image-gen, specific about action/setting/lighting>",
      "primary_character": "<canonical name from character_bible, or 'both', or null>",
      "reference_pose": "<portrait|full_body|action|null>",
      "dialogue": [{{"speaker": "<canonical name>", "text": "<≤60 chars>"}}],
      "continuity_notes": "<which existing canon details must appear>"
    }}
  ],
  "continuity_updates": "<markdown section to append to continuity-log.md>"
}}

Rules:
- **Target panel count: {target_panels} panels** (may vary ±2 if narrative demands, but aim for {target_panels}).
- Pace the story properly — don't rush. Use establishing shots, silent beats, reaction shots, dramatic close-ups to fill the panel budget with genuine narrative purpose. Avoid padding with redundant panels.
- Obey style_card's dialogue density preference (bubbles per panel).
- Use EXACT character names from character_bible in primary_character and dialogue.speaker.
- Every panel's description MUST preserve the character's signature accessories.

Return only JSON.
"""

# ─── continuity check ─────────────────────────────────────────────────────

CONTINUITY_CHECK_SYSTEM = (
    "You are a continuity editor. Given canon + optional previous panel images + new chapter spec, "
    "flag consistency issues. Return STRICT JSON."
)

CONTINUITY_CHECK_USER_TEMPLATE = """Canon:

## CHARACTER BIBLE
{character_bible}

## CONTINUITY LOG (prior state)
{continuity_log}

New chapter spec:
{chapter_spec_json}

{image_note}

Check for continuity issues:
1. Any panel omitting a character's signature accessories (from character_bible)?
2. Any contradiction with continuity_log (location/state/event)?
3. Any wrong hair/eye color or unexplained outfit change?
4. Any dialogue contradicting prior story beats?

Return JSON:
{{
  "clean": true|false,
  "warnings": [
    {{"panel": <panel number or null>, "issue": "<description>", "fix": "<suggested fix>"}}
  ]
}}

Return only JSON.
"""

# ─── style evolver ────────────────────────────────────────────────────────

STYLE_EVOLVER_SYSTEM = (
    "You update a comic series style-card.md from user feedback. "
    "Preserve all existing sections and frontmatter; bump version; append an updates section. "
    "Return STRICT JSON."
)

STYLE_EVOLVER_USER_TEMPLATE = """Current style-card.md:

{current_style_card}

User feedback ({today}):
{feedback}

Return JSON:
{{
  "new_style_card": "<full updated markdown including frontmatter with bumped version>",
  "change_summary": "<one-line summary of what changed>"
}}

Rules:
- Bump version (1.0 → 1.1 → 1.2 ...)
- Keep all prior sections verbatim
- Append a new "## Updates" section if missing, or new dated entry under it
- Translate feedback into SPECIFIC art/pacing rules (not vague)
- Example concrete rules: "≤2 bubbles per panel", "action panels ≥70% canvas", "dialogue density ≤3 lines/panel"

Return only JSON.
"""

# ─── plot twist proposer (thinking mode) ──────────────────────────────────

PLOT_TWIST_SYSTEM = (
    "You are a senior story editor. Given complete series canon + all chapters so far, "
    "propose 3 alternative plot twists starting from a given chapter. "
    "Each alternative must include a 3-chapter outline. Return STRICT JSON."
)

PLOT_TWIST_USER_TEMPLATE = """Canon:

## WORLD BIBLE
{world_bible}

## CHARACTER BIBLE
{character_bible}

## CONTINUITY LOG
{continuity_log}

## ALL CHAPTER SPECS SO FAR
{chapter_specs_json}

Propose 3 alternative plot twists starting from chapter {starting_chapter}.
Each must be surprising, thematically coherent with existing canon, and not contradict established character accessories/powers.

Return JSON:
{{
  "alternatives": [
    {{
      "title": "<twist title>",
      "twist": "<one-sentence twist description>",
      "chapter_outlines": [
        {{"n": {starting_chapter}, "beat": "<chapter beat description, 2-3 sentences>"}},
        {{"n": {next_chapter}, "beat": "..."}},
        {{"n": {third_chapter}, "beat": "..."}}
      ]
    }},
    {{ ... second alternative ... }},
    {{ ... third alternative ... }}
  ]
}}

Return only JSON.
"""
