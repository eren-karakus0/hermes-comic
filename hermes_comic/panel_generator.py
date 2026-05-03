"""Turn a chapter spec.json into panel PNGs via the styled Flux pipeline.

Routing per panel:
  - primary_character resolves to a reference image  →  flux-lora/image-to-image
      (single-character panel, LoRA style stack, strength-anchored character DNA)
  - primary_character == "both"                      →  kontext/multi
      (no LoRA available on multi endpoint, style tradeoff accepted)
  - no character                                     →  flux-lora text2image
      (pure atmospheric / environmental panel with LoRA style)

Prompt construction uses hermes_comic.style.build_prompt, which stacks:
  panel description → camera framing → manhwa art direction → quality anchors → anti-generic
"""
from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from hermes_comic import canon
from hermes_comic.flux_client import FluxClient, LoraRef
from hermes_comic.style import (
    build_prompt,
    get_default_lora_stack,
    image_size_for,
    pick_framing,
)

logger = logging.getLogger(__name__)


@dataclass
class PanelJob:
    n: int
    description: str
    primary_character: Optional[str]
    reference_pose: Optional[str]
    camera_framing: str
    references: list[Path]
    is_multi: bool
    out_path: Path
    loras: list[LoraRef] = field(default_factory=list)

    @property
    def refs_label(self) -> str:
        if not self.references:
            return "(text2image + LoRA)"
        names = ", ".join(r.parent.name + "/" + r.name for r in self.references)
        suffix = " [MULTI no-LoRA]" if self.is_multi else " + LoRA"
        return f"{names}{suffix}"


def _normalize_char_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    low = name.lower().strip()
    if low in ("null", "none"):
        return None
    if low == "both":
        return "both"
    for prefix in ("princess", "prince", "queen", "king", "lord", "lady",
                   "warrior", "sir", "the", "first shield"):
        if low.startswith(prefix + " "):
            low = low[len(prefix) + 1:]
    first = re.split(r"[\s\-]", low, maxsplit=1)[0]
    return first or None


def _resolve_refs(
    primary_character: Optional[str],
    reference_pose: Optional[str],
    workspace: Path,
) -> tuple[list[Path], bool]:
    """Returns (refs, is_multi). is_multi → use kontext/multi (no LoRA)."""
    chars_dir = workspace / "characters"
    norm = _normalize_char_name(primary_character)
    if not norm:
        return [], False

    if norm == "both":
        refs: list[Path] = []
        if chars_dir.exists():
            for d in sorted(chars_dir.iterdir()):
                if d.is_dir():
                    p = d / "portrait.png"
                    if p.exists():
                        refs.append(p)
        return refs[:2], True

    char_dir = chars_dir / norm
    if not char_dir.exists():
        logger.warning("character dir missing: %s (primary=%r)", char_dir, primary_character)
        return [], False

    pose = (reference_pose or "portrait").lower().replace("-", "_")
    ref = char_dir / f"{pose}.png"
    if ref.exists():
        return [ref], False
    fallback = char_dir / "portrait.png"
    if fallback.exists():
        logger.info("pose %r missing for %s; falling back to portrait", pose, norm)
        return [fallback], False
    return [], False


def build_jobs(chapter_num: int) -> list[PanelJob]:
    ws = canon.get_workspace()
    spec_path = canon.chapter_dir(chapter_num) / "spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    panels_dir = canon.chapter_dir(chapter_num) / "panels"
    panels_dir.mkdir(parents=True, exist_ok=True)

    loras = get_default_lora_stack()

    jobs: list[PanelJob] = []
    for p in spec["panels"]:
        refs, is_multi = _resolve_refs(
            p.get("primary_character"), p.get("reference_pose"), ws
        )
        camera = pick_framing(p.get("camera"), p.get("reference_pose"))
        # LoRAs are skipped on kontext/multi (endpoint doesn't accept them)
        panel_loras = [] if is_multi else list(loras)
        jobs.append(
            PanelJob(
                n=p["n"],
                description=p["description"],
                primary_character=p.get("primary_character"),
                reference_pose=p.get("reference_pose"),
                camera_framing=camera,
                references=refs,
                is_multi=is_multi,
                loras=panel_loras,
                out_path=panels_dir / f"panel_{p['n']:02d}.png",
            )
        )
    return jobs


def _render_one(
    client: FluxClient,
    job: PanelJob,
    base_seed: Optional[int],
    strength: float,
) -> tuple[PanelJob, bool, str]:
    if job.out_path.exists() and job.out_path.stat().st_size > 100_000:
        return job, True, f"[skip] exists ({job.out_path.stat().st_size:,} bytes)"

    prompt = build_prompt(job.description, camera_framing=job.camera_framing)
    size = image_size_for(job.camera_framing)
    # Per-panel seed variance keeps scenes distinct while base anchors style
    seed = None if base_seed is None else base_seed + job.n

    try:
        if job.is_multi and len(job.references) >= 2:
            # Multi-char panel: fall back to Kontext multi (no LoRA)
            ref_paths = [str(r) for r in job.references]
            img = client.render(
                prompt=prompt,
                reference_paths=ref_paths,
                seed=seed,
            )
        elif job.loras and job.references:
            # Styled img2img — single char reference + LoRA stack
            img = client.render(
                prompt=prompt,
                loras=job.loras,
                reference_path=str(job.references[0]),
                strength=strength,
                seed=seed,
            )
        elif job.loras:
            # Styled text2image — no reference, pure LoRA aesthetic
            img = client.render(
                prompt=prompt,
                loras=job.loras,
                image_size=size,
                seed=seed,
            )
        else:
            # Ultimate fallback — basic text2image
            img = client.render(prompt=prompt, image_size=size, seed=seed)

        job.out_path.write_bytes(img)
        return job, True, f"saved {len(img):,} bytes"
    except Exception as e:
        return job, False, f"error: {type(e).__name__}: {str(e)[:160]}"


def render_all(
    jobs: list[PanelJob],
    concurrency: int = 3,
    seed: Optional[int] = None,
    strength: float = 0.78,
    no_references: bool = False,
) -> list[tuple[PanelJob, bool, str]]:
    if no_references:
        for j in jobs:
            j.references = []
            j.is_multi = False
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )

    client = FluxClient()
    results: list[tuple[PanelJob, bool, str]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total} panels"),
        TextColumn("·"),
        TimeElapsedColumn(),
    ) as progress:
        task = progress.add_task(
            f"rendering ({concurrency} parallel)",
            total=len(jobs),
        )
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures = [
                ex.submit(_render_one, client, j, seed, strength) for j in jobs
            ]
            for f in as_completed(futures):
                job, ok, msg = f.result()
                results.append((job, ok, msg))
                status = "ok" if ok else "fail"
                progress.update(
                    task,
                    advance=1,
                    description=f"panel {job.n} {status}",
                )

    results.sort(key=lambda t: t[0].n)
    return results


# Back-compat: some earlier scripts import _panel_prompt / _resolve_refs directly
def _panel_prompt(job: PanelJob) -> str:
    return build_prompt(job.description, camera_framing=job.camera_framing)
