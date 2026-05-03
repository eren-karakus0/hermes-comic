"""Compose panel PNGs into a vertical webtoon with professional speech bubbles.

Canvas: 800px wide, panels stacked vertically, 60px gutter.
Bubbles: rounded white fill + black outline + downward-pointing triangle tail,
bold Noto font, smart placement (first speaker top-left, second top-right).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

CANVAS_WIDTH = 800
GUTTER = 60
BUBBLE_PAD = 18
BUBBLE_RADIUS = 22
BUBBLE_FONT_SIZE = 26
MAX_BUBBLES_PER_PANEL = 2
MAX_LINE_CHARS = 22
TAIL_W = 18
TAIL_H = 22

# Prefer bold fonts for that comic feel
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]


def _find_font(size: int = BUBBLE_FONT_SIZE) -> ImageFont.FreeTypeFont | None:
    for p in _FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    logger.warning("no TTF font found; speech bubbles will be omitted")
    return None


def _wrap(text: str, max_chars: int = MAX_LINE_CHARS) -> list[str]:
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


def _resize_to_width(img: Image.Image, target: int) -> Image.Image:
    if img.width == target:
        return img
    ratio = target / img.width
    new_h = int(img.height * ratio)
    return img.resize((target, new_h), Image.LANCZOS)


def _draw_bubble_with_tail(
    panel: Image.Image,
    x: int,
    y: int,
    speaker: str,
    text: str,
    font: ImageFont.FreeTypeFont,
    tail_side: str = "right",  # "left" or "right" — where tail sits on bubble bottom
) -> None:
    full = f"{speaker.upper()}: {text}" if speaker else text
    lines = _wrap(full)
    line_h = font.size + 5
    text_h = len(lines) * line_h
    text_w = max(int(font.getlength(line)) for line in lines)

    bubble_w = min(text_w + BUBBLE_PAD * 2, panel.width - 40)
    bubble_h = text_h + BUBBLE_PAD * 2

    # Clamp bubble inside panel (leave room for tail below)
    x = max(12, min(x, panel.width - bubble_w - 12))
    y = max(12, min(y, panel.height - bubble_h - TAIL_H - 12))

    draw = ImageDraw.Draw(panel)

    # Rounded rect body
    draw.rounded_rectangle(
        [(x, y), (x + bubble_w, y + bubble_h)],
        radius=BUBBLE_RADIUS,
        fill=(255, 255, 255),
        outline=(0, 0, 0),
        width=3,
    )

    # Triangle tail pointing down into panel — positioned left or right side
    if tail_side == "left":
        tail_anchor_x = x + bubble_w // 4
    else:
        tail_anchor_x = x + (bubble_w * 3) // 4
    tail_y_top = y + bubble_h - 2
    tail_tip_y = tail_y_top + TAIL_H
    tail_tip_x = tail_anchor_x + (10 if tail_side == "right" else -10)

    # White fill triangle (seamless with bubble)
    triangle_fill = [
        (tail_anchor_x - TAIL_W // 2, tail_y_top),
        (tail_anchor_x + TAIL_W // 2, tail_y_top),
        (tail_tip_x, tail_tip_y),
    ]
    draw.polygon(triangle_fill, fill=(255, 255, 255))

    # Black outline — two sides of triangle (not the top, which is covered by bubble)
    draw.line(
        [(tail_anchor_x - TAIL_W // 2, tail_y_top), (tail_tip_x, tail_tip_y)],
        fill=(0, 0, 0),
        width=3,
    )
    draw.line(
        [(tail_tip_x, tail_tip_y), (tail_anchor_x + TAIL_W // 2, tail_y_top)],
        fill=(0, 0, 0),
        width=3,
    )

    # Text
    for li, line in enumerate(lines):
        draw.text(
            (x + BUBBLE_PAD, y + BUBBLE_PAD + li * line_h),
            line,
            fill=(0, 0, 0),
            font=font,
        )


def _add_bubbles(panel: Image.Image, dialogue: list[dict[str, Any]]) -> Image.Image:
    if not dialogue:
        return panel
    font = _find_font()
    if font is None:
        return panel

    # Placement: first bubble top-left (tail right → points toward scene center),
    # second bubble top-right (tail left → points toward scene center).
    slots = [
        {"x": 30, "y": 30, "tail": "right"},
        {"x": panel.width // 2 + 20, "y": 30, "tail": "left"},
    ]

    for i, d in enumerate(dialogue[:MAX_BUBBLES_PER_PANEL]):
        speaker = (d.get("speaker", "") or "").strip()
        text = (d.get("text", "") or "").strip()
        if not text:
            continue
        slot = slots[i]
        _draw_bubble_with_tail(
            panel,
            x=slot["x"],
            y=slot["y"],
            speaker=speaker,
            text=text,
            font=font,
            tail_side=slot["tail"],
        )
    return panel


def compose_chapter(
    panel_paths: list[Path],
    dialogues: list[list[dict[str, Any]]],
    out_path: Path,
    canvas_width: int = CANVAS_WIDTH,
    gutter: int = GUTTER,
) -> Path:
    """Stitch panels vertically, overlay dialogue bubbles, save single PNG."""
    if len(panel_paths) != len(dialogues):
        raise ValueError(
            f"panel/dialogue count mismatch: {len(panel_paths)} vs {len(dialogues)}"
        )

    processed: list[Image.Image] = []
    total_h = 0
    for path, dlg in zip(panel_paths, dialogues):
        img = Image.open(path).convert("RGB")
        img = _resize_to_width(img, canvas_width)
        img = _add_bubbles(img, dlg)
        processed.append(img)
        total_h += img.height

    total_h += gutter * max(0, len(processed) - 1)
    canvas = Image.new("RGB", (canvas_width, total_h), (18, 18, 24))  # dark gutter
    y = 0
    for img in processed:
        canvas.paste(img, (0, y))
        y += img.height + gutter

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, "PNG")
    logger.info("composed %s (%sx%s)", out_path, canvas_width, total_h)
    return out_path


def compose_series(
    chapter_paths: list[Path],
    out_path: Path,
    canvas_width: int = CANVAS_WIDTH,
    chapter_gap: int = 160,
    title_font_size: int = 42,
) -> Path:
    """Stack multiple chapter.png files into a single series PNG with titled separators."""
    font = _find_font(title_font_size) or _find_font(BUBBLE_FONT_SIZE)
    processed: list[tuple[Image.Image, str]] = []
    total_h = 0
    for i, cp in enumerate(chapter_paths, 1):
        img = Image.open(cp).convert("RGB")
        img = _resize_to_width(img, canvas_width)
        label = f"— CHAPTER {i:02d} —"
        processed.append((img, label))
        total_h += img.height
    total_h += chapter_gap * len(processed)

    canvas = Image.new("RGB", (canvas_width, total_h), (12, 12, 18))
    draw = ImageDraw.Draw(canvas)
    y = 0
    for img, label in processed:
        if font:
            text_w = int(font.getlength(label))
            tx = (canvas_width - text_w) // 2
            ty = y + chapter_gap // 2 - title_font_size // 2
            draw.text((tx, ty), label, fill=(220, 220, 230), font=font)
        y += chapter_gap
        canvas.paste(img, (0, y))
        y += img.height

    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path, "PNG")
    logger.info("composed series %s (%sx%s)", out_path, canvas_width, total_h)
    return out_path
