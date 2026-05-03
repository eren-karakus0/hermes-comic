"""Generate a 1200×630 series cover poster.

Used as:
  - `<workspace>/cover.jpg` (persisted)
  - og:image + twitter:image in the published bundle

Pipeline:
  1. fal.ai flux-lora text2image → cover art (1200×640, landscape poster composition)
  2. PIL overlay → title + tagline + dark gradient (text legibility)
  3. Save as JPEG 90 quality
"""
from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from hermes_comic.flux_client import FluxClient
from hermes_comic.style import ART_DIRECTION_CORE, ANTI_GENERIC, get_default_lora_stack

# ─── cover art prompt ─────────────────────────────────────────────────────

COVER_COMPOSITION = (
    "manhwa webtoon cover poster composition, cinematic hero shot, "
    "dramatic rim lighting with volumetric rays, atmospheric depth, "
    "professional Korean webtoon poster in the style of Solo Leveling and Tower of God, "
    "clean lower half composition (low visual density at the bottom third for title overlay), "
    "high production quality digital illustration, cinematic color grading"
)


def build_cover_prompt(
    series_title: str,
    hero_visual: str = "",
    style_override: str = "",
) -> str:
    parts = [COVER_COMPOSITION]
    if hero_visual:
        parts.append(f"hero character: {hero_visual.strip()}")
    parts.append(style_override or ART_DIRECTION_CORE)
    parts.append(ANTI_GENERIC)
    return ". ".join(p for p in parts if p)


def generate_cover_art(
    series_title: str,
    hero_visual: str = "",
    style_override: str = "",
    seed: Optional[int] = None,
) -> bytes:
    """Generate raw cover art via fal.ai flux-lora (no text, just the visual)."""
    client = FluxClient()
    loras = get_default_lora_stack()
    prompt = build_cover_prompt(series_title, hero_visual, style_override)
    return client.render_styled_text2image(
        prompt=prompt,
        loras=loras,
        image_size={"width": 1200, "height": 640},  # ~1.875:1, close to Twitter 1.91:1
        seed=seed,
        guidance_scale=3.5,
    )


# ─── PIL overlay ──────────────────────────────────────────────────────────

_FONT_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]
_FONT_ITALIC_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSans-Italic.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
]


def _load_font(candidates: list[str], size: int) -> Optional[ImageFont.FreeTypeFont]:
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return None


def _wrap(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = f"{cur} {w}".strip() if cur else w
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _apply_bottom_gradient(img: Image.Image, fade_from: float = 0.45) -> Image.Image:
    """Darken lower half with a smooth gradient for text legibility."""
    width, height = img.size
    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    start_y = int(height * fade_from)
    span = height - start_y
    for y in range(start_y, height):
        # 0 → 200 alpha, quadratic for smoother curve
        t = (y - start_y) / span
        alpha = int(200 * (t ** 1.4))
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))
    base = img.convert("RGBA")
    return Image.alpha_composite(base, gradient).convert("RGB")


def compose_cover(
    art_bytes: bytes,
    title: str,
    tagline: str = "",
    final_size: tuple[int, int] = (1200, 630),
) -> bytes:
    """Overlay series title + tagline on cover art."""
    art = Image.open(io.BytesIO(art_bytes)).convert("RGB")
    # Crop to exact final_size (keeps aspect, drops letterbox if mismatched)
    if art.size != final_size:
        art = art.resize(final_size, Image.LANCZOS)

    # Dark gradient bottom half for text readability
    canvas = _apply_bottom_gradient(art, fade_from=0.42)

    title_font = _load_font(_FONT_BOLD_CANDIDATES, 76)
    tagline_font = _load_font(_FONT_ITALIC_CANDIDATES, 28)

    if title_font is None:
        # No font — return art without overlay
        buf = io.BytesIO()
        canvas.save(buf, "JPEG", quality=90, optimize=True)
        return buf.getvalue()

    draw = ImageDraw.Draw(canvas)
    w, h = canvas.size

    # Wrap title to keep it visually balanced
    title_lines = _wrap(title.upper(), max_chars=22)
    tagline_lines = _wrap(tagline, max_chars=58) if tagline else []

    title_line_h = 84
    tagline_line_h = 36
    gap_title_tagline = 22

    total_h = len(title_lines) * title_line_h
    if tagline_lines:
        total_h += gap_title_tagline + len(tagline_lines) * tagline_line_h

    # Anchor text block in the bottom band, 60px above edge
    start_y = h - total_h - 60

    y = start_y
    for line in title_lines:
        lw = draw.textlength(line, font=title_font)
        x = (w - lw) / 2
        # Drop shadow (soft)
        draw.text((x + 3, y + 3), line, fill=(0, 0, 0), font=title_font)
        draw.text((x, y), line, fill=(255, 255, 255), font=title_font)
        y += title_line_h

    if tagline_lines:
        y += gap_title_tagline
        for line in tagline_lines:
            lw = draw.textlength(line, font=tagline_font)
            x = (w - lw) / 2
            # Magenta accent matching the published page's --accent var
            draw.text((x + 2, y + 2), line, fill=(0, 0, 0), font=tagline_font)
            draw.text((x, y), line, fill=(232, 121, 249), font=tagline_font)
            y += tagline_line_h

    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=90, optimize=True)
    return buf.getvalue()


# ─── canon extraction helpers ─────────────────────────────────────────────

_FIRST_CHARACTER_HEAD_RX = re.compile(r"^(?:##+\s+|\*\*)([^\*\n#]+)", re.MULTILINE)


def extract_hero_visual(character_bible: str) -> str:
    """Best-effort extraction of the first character's visual description."""
    if not character_bible:
        return ""
    # Look for lines with "visual" or "appearance" label
    for line in character_bible.splitlines():
        lower = line.lower()
        if ("visual" in lower or "appearance" in lower) and ":" in line:
            parts = line.split(":", 1)
            if len(parts) == 2 and len(parts[1].strip()) > 20:
                return parts[1].strip()[:350]
    # Fallback: first non-frontmatter paragraph after a character header
    sections = character_bible.split("##")
    for section in sections[1:]:  # skip pre-header content
        lines = [l.strip() for l in section.splitlines() if l.strip()]
        if len(lines) >= 2:
            # Join the next 1-3 content lines
            body = " ".join(lines[1:4])
            body = re.sub(r"^[-*•]\s*", "", body)  # strip list markers
            if len(body) > 30:
                return body[:350]
    return ""


def extract_tagline(world_bible: str, max_len: int = 140) -> str:
    """Derive a tagline from the world-bible first substantive line."""
    if not world_bible:
        return ""
    skip_prefixes = ("---", "#", "-", "*", "series:", "kind:", "version:", "history:")
    for raw in world_bible.splitlines():
        line = raw.strip()
        if not line:
            continue
        if any(line.lower().startswith(p) for p in skip_prefixes):
            continue
        # Strip markdown emphasis
        line = re.sub(r"[*_`]+", "", line).strip()
        if len(line) > 20:
            return line[:max_len]
    return ""
