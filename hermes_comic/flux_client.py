"""fal.ai Flux endpoints — unified wrapper with LoRA + reference chain support.

Primary endpoints:
  - fal-ai/flux-lora                   → text2image + LoRA stack
  - fal-ai/flux-lora/image-to-image    → reference + LoRA stack
  - fal-ai/flux-pro/kontext            → character reference (no LoRA)
  - fal-ai/flux-pro/kontext/multi      → multi-character reference
  - fal-ai/flux/dev                    → text2image fallback (no LoRA)

Pricing: $0.035/MP for flux-lora variants, $0.04 for Kontext.

Mode selection:
  - STYLED=True (default) → LoRA pipeline (flux-lora[/image-to-image])
  - STYLED=False          → legacy Kontext pipeline (phase 2 behavior)
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import fal_client
import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@dataclass
class LoraRef:
    path: str
    scale: float = 0.8


class FluxClient:
    """fal.ai Flux wrapper with LoRA + reference chain support."""

    def __init__(self, timeout: float = 300.0) -> None:
        key = os.environ.get("FAL_KEY")
        if not key:
            raise RuntimeError("FAL_KEY env var not set")
        self.key = key
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Key {key}",
            "Content-Type": "application/json",
        }
        self._upload_cache: dict[str, str] = {}

    def upload(self, local_path: str | Path) -> str:
        lp = str(Path(local_path).resolve())
        if lp in self._upload_cache:
            return self._upload_cache[lp]
        url = fal_client.upload_file(lp)
        self._upload_cache[lp] = url
        logger.info("uploaded %s → %s", Path(lp).name, url)
        return url

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=3, max=20),
        reraise=True,
    )
    def _post(self, endpoint: str, payload: dict[str, Any]) -> str:
        r = httpx.post(endpoint, headers=self.headers, json=payload, timeout=self.timeout)
        if r.status_code != 200:
            logger.error("fal %s → %s: %s", endpoint, r.status_code, r.text[:500])
            r.raise_for_status()
        return r.json()["images"][0]["url"]

    def _download(self, url: str) -> bytes:
        return httpx.get(url, timeout=60).content

    # ─── styled pipeline (LoRA-enabled) ───────────────────────────────────

    def render_styled_text2image(
        self,
        prompt: str,
        loras: list[LoraRef],
        image_size: dict[str, int] | str = "square_hd",
        seed: Optional[int] = None,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 28,
    ) -> bytes:
        """fal-ai/flux-lora text2image with LoRA stack."""
        payload: dict[str, Any] = {
            "prompt": prompt,
            "image_size": image_size,
            "loras": [{"path": l.path, "scale": l.scale} for l in loras],
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps,
            "num_images": 1,
            "output_format": "png",
        }
        if seed is not None:
            payload["seed"] = seed
        logger.info(
            "flux-lora t2i size=%s loras=%d steps=%d",
            image_size,
            len(loras),
            num_inference_steps,
        )
        url = self._post("https://fal.run/fal-ai/flux-lora", payload)
        return self._download(url)

    def render_styled_img2img(
        self,
        prompt: str,
        reference_url: str,
        loras: list[LoraRef],
        strength: float = 0.75,
        seed: Optional[int] = None,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 28,
    ) -> bytes:
        """fal-ai/flux-lora/image-to-image with LoRA stack + reference anchor."""
        payload: dict[str, Any] = {
            "image_url": reference_url,
            "prompt": prompt,
            "loras": [{"path": l.path, "scale": l.scale} for l in loras],
            "strength": strength,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps,
            "num_images": 1,
            "output_format": "png",
        }
        if seed is not None:
            payload["seed"] = seed
        logger.info(
            "flux-lora i2i strength=%.2f loras=%d",
            strength,
            len(loras),
        )
        url = self._post("https://fal.run/fal-ai/flux-lora/image-to-image", payload)
        return self._download(url)

    # ─── legacy Kontext pipeline (no LoRA) ────────────────────────────────

    def render_kontext(
        self,
        prompt: str,
        references: list[str],
        seed: Optional[int] = None,
    ) -> bytes:
        """fal-ai/flux-pro/kontext (single/multi) — reference-preserving, no LoRA."""
        ref_urls = [self.upload(p) for p in references]
        is_multi = len(ref_urls) > 1
        endpoint = (
            "https://fal.run/fal-ai/flux-pro/kontext/multi"
            if is_multi
            else "https://fal.run/fal-ai/flux-pro/kontext"
        )
        payload: dict[str, Any] = {
            "prompt": prompt,
            "num_images": 1,
            "output_format": "png",
        }
        if is_multi:
            payload["image_urls"] = ref_urls
        else:
            payload["image_url"] = ref_urls[0]
        if seed is not None:
            payload["seed"] = seed
        url = self._post(endpoint, payload)
        return self._download(url)

    def render_text2image_basic(
        self,
        prompt: str,
        image_size: dict[str, int] | str = "square_hd",
        seed: Optional[int] = None,
    ) -> bytes:
        """fal-ai/flux/dev — no LoRA fallback."""
        payload: dict[str, Any] = {
            "prompt": prompt,
            "num_images": 1,
            "image_size": image_size,
            "num_inference_steps": 28,
        }
        if seed is not None:
            payload["seed"] = seed
        url = self._post("https://fal.run/fal-ai/flux/dev", payload)
        return self._download(url)

    # ─── unified router ───────────────────────────────────────────────────

    def render(
        self,
        prompt: str,
        loras: Optional[list[LoraRef]] = None,
        reference_path: Optional[str] = None,
        reference_paths: Optional[list[str]] = None,
        image_size: dict[str, int] | str = "square_hd",
        seed: Optional[int] = None,
        strength: float = 0.75,
        guidance_scale: float = 3.5,
    ) -> bytes:
        """Routes to the best endpoint based on inputs.

        Priority:
          1. loras + reference_path       → flux-lora/image-to-image
          2. loras (no ref)               → flux-lora text2image
          3. reference_paths (2+)         → Kontext multi
          4. reference_path               → Kontext single
          5. prompt only                  → flux/dev basic
        """
        if loras and reference_path:
            ref_url = self.upload(reference_path)
            return self.render_styled_img2img(
                prompt=prompt,
                reference_url=ref_url,
                loras=loras,
                strength=strength,
                seed=seed,
                guidance_scale=guidance_scale,
            )
        if loras:
            return self.render_styled_text2image(
                prompt=prompt,
                loras=loras,
                image_size=image_size,
                seed=seed,
                guidance_scale=guidance_scale,
            )
        if reference_paths and len(reference_paths) > 1:
            return self.render_kontext(prompt=prompt, references=reference_paths, seed=seed)
        if reference_path:
            return self.render_kontext(prompt=prompt, references=[reference_path], seed=seed)
        return self.render_text2image_basic(prompt=prompt, image_size=image_size, seed=seed)
