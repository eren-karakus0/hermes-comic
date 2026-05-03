"""Style architecture for professional webtoon prompts.

Replaces the generic "anime webtoon style" suffix with:
  - Specific artist/studio references (Kentaro Miura, Solo Leveling, Tower of God)
  - Technical art terminology (cross-hatching, screentone, ink wash, cel shading weight)
  - Per-panel camera/framing hints
  - Civitai LoRA stack configuration
"""
from __future__ import annotations

import os
from typing import Optional

from hermes_comic.flux_client import LoraRef

# ─── Civitai Flux LoRA stack ──────────────────────────────────────────────
# Only use Flux.1 [dev] trained LoRAs — SDXL LoRAs will fail on flux endpoints.
#
# URL resolution (lazy, per call, in order of priority):
#   1. Explicit <NAME>_LORA_URL env var (e.g. MANHWA_LORA_URL=https://fal.media/…)
#      → Use this if you uploaded the .safetensors to fal storage yourself.
#   2. Civitai direct URL + optional ?token=$CIVITAI_TOKEN query param
#      → Set CIVITAI_TOKEN in .env for auth-gated Civitai downloads.

_MANHWA_BASE = "https://civitai.com/api/download/models/716348?type=Model&format=SafeTensor"
_SOLO_LEVELING_BASE = "https://civitai.com/api/download/models/1407029?type=Model&format=SafeTensor"


def _with_civitai_token(url: str) -> str:
    token = os.environ.get("CIVITAI_TOKEN")
    if not token:
        return url
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}token={token}"


def _resolve_lora_url(env_override: str, civitai_url: str) -> str:
    override = os.environ.get(env_override)
    if override:
        return override
    return _with_civitai_token(civitai_url)


def get_manhwa_lora_url() -> str:
    """Manwha/Webtoon Style (Civitai 716348) — general Korean webtoon aesthetic."""
    return _resolve_lora_url("MANHWA_LORA_URL", _MANHWA_BASE)


def get_solo_leveling_lora_url() -> str:
    """Solo Leveling style (Civitai 1407029) — dark epic high-contrast."""
    return _resolve_lora_url("SOLO_LEVELING_LORA_URL", _SOLO_LEVELING_BASE)


def get_default_lora_stack() -> list[LoraRef]:
    """Default LoRA stack for Neon & Ash (cyberpunk manhwa).

    Built lazily so env var changes reflect immediately (no stale imports).
    """
    return [LoraRef(get_manhwa_lora_url(), scale=0.85)]


# ─── Style stack components ───────────────────────────────────────────────

ART_DIRECTION_CORE = (
    "Korean manhwa webtoon style in the vein of Solo Leveling and Tower of God, "
    "professional digital illustration, manwha_style, "
    "dramatic cinematic composition, strong atmospheric perspective, "
    "high-contrast cel shading with rich color grading, "
    "detailed character linework with variable weight line art, "
    "dramatic lighting with volumetric rim light and deep shadow work, "
    "rich saturated color palette with filmic tone mapping, "
    "professional manhwa studio production quality"
)

QUALITY_ANCHORS = (
    "masterpiece, best quality, highly detailed, intricate, cinematic lighting, "
    "professional color grading, sharp focus, ultra detailed character design"
)

ANTI_GENERIC = (
    "NOT generic anime, NOT flat shading, NOT plastic cel look, NOT amateur digital art"
)


# Camera / framing library — append one per panel for compositional variety
CAMERA_FRAMINGS = {
    "extreme_close_up":
        "extreme close-up shot, face fills frame, shallow depth of field, intense emotion",
    "close_up":
        "close-up portrait, head and shoulders, soft dramatic lighting, three-quarter view",
    "medium":
        "medium shot, waist-up framing, subject centered, clean background",
    "full_body":
        "full body shot, head to toe visible, three-quarter view, environmental context",
    "wide_establishing":
        "wide establishing shot, tiny figures in vast environment, atmospheric scale, "
        "epic landscape, cinematic widescreen",
    "dutch_tilt":
        "dutch tilt camera angle, dynamic diagonal composition, tension and unease",
    "low_angle":
        "extreme low angle hero shot, subject towering above camera, dramatic sky behind",
    "high_angle":
        "high angle overhead shot, subject vulnerable below, dramatic overhead perspective",
    "over_shoulder":
        "over-the-shoulder shot, dialogue framing, facing subject visible in distance",
    "action":
        "dynamic action pose, motion blur trails, dramatic speed lines, "
        "impact lighting, mid-motion freeze frame",
    "silent_beat":
        "silent cinematic beat panel, minimal composition, atmospheric mood, "
        "focus on environment and emotion, wordless scene",
    "two_shot":
        "two-shot composition, both subjects in frame, eye-line match, "
        "balanced visual weight across frame",
    "split":
        "split panel composition, left half one subject right half other subject, "
        "symbolic parallel, center gutter divides worlds",
}


# Webtoon aspect ratio presets matched to camera framings
# (W, H) in pixels — all multiples of 16 for Flux
ASPECT_PRESETS = {
    "extreme_close_up": (1024, 1024),      # square — face focus
    "close_up":         (1024, 1024),      # square
    "medium":           (1024, 1280),      # 4:5 portrait
    "full_body":        (768, 1280),       # 3:5 tall — fit character
    "wide_establishing":(1536, 1024),      # 3:2 landscape wide
    "dutch_tilt":       (1024, 1280),      # 4:5
    "low_angle":        (1024, 1536),      # 2:3 tall hero
    "high_angle":       (1280, 1024),      # 5:4 wider
    "over_shoulder":    (1024, 1280),      # 4:5
    "action":           (1280, 1024),      # 5:4 — horizontal motion
    "silent_beat":      (1536, 1024),      # 3:2 atmospheric wide
    "two_shot":         (1280, 1024),      # 5:4
    "split":            (1536, 1024),      # 3:2 — wide split
}


DEFAULT_FRAMING = "medium"


def pick_framing(camera_hint: Optional[str], reference_pose: Optional[str]) -> str:
    """Resolve a panel's camera framing key from spec hints."""
    if camera_hint and camera_hint in CAMERA_FRAMINGS:
        return camera_hint
    # Fallback map from reference_pose
    pose = (reference_pose or "").lower().replace("-", "_")
    if pose == "portrait":
        return "close_up"
    if pose == "action":
        return "action"
    if pose == "full_body":
        return "full_body"
    return DEFAULT_FRAMING


def build_prompt(
    panel_description: str,
    camera_framing: str = DEFAULT_FRAMING,
    extra_style: Optional[str] = None,
) -> str:
    """Compose a professional webtoon panel prompt.

    Stack order (most specific first):
      1. Panel-specific visual description
      2. Camera / framing directive
      3. Art direction core (artist refs + technical terms)
      4. Quality anchors
      5. Anti-generic reminder
    """
    framing = CAMERA_FRAMINGS.get(camera_framing, CAMERA_FRAMINGS[DEFAULT_FRAMING])
    parts = [
        panel_description.strip(),
        framing,
        ART_DIRECTION_CORE,
    ]
    if extra_style:
        parts.append(extra_style.strip())
    parts.extend([QUALITY_ANCHORS, ANTI_GENERIC])
    return ". ".join(parts)


def image_size_for(camera_framing: str) -> dict[str, int] | str:
    """Return an image_size spec compatible with fal-ai/flux-lora.

    Returns a dict {"width": W, "height": H} for custom sizes.
    """
    w, h = ASPECT_PRESETS.get(camera_framing, ASPECT_PRESETS[DEFAULT_FRAMING])
    return {"width": w, "height": h}
