"""Thin Kimi K2.5 client — direct HTTP with retries.

Auto-detects provider from env:
  OPENROUTER_API_KEY (sk-or-*)  → https://openrouter.ai/api/v1, model=moonshotai/kimi-k2.5
  KIMI_API_KEY (sk-*)           → https://api.moonshot.ai/v1, model=kimi-k2.5
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


def _pick_provider() -> tuple[str, str, str, str]:
    """Returns (base_url, default_model, api_key, provider_name)."""
    or_key = os.environ.get("OPENROUTER_API_KEY")
    kimi_key = os.environ.get("KIMI_API_KEY")
    if or_key:
        return (
            "https://openrouter.ai/api/v1",
            "moonshotai/kimi-k2.5",
            or_key,
            "openrouter",
        )
    if kimi_key:
        return ("https://api.moonshot.ai/v1", "kimi-k2.5", kimi_key, "moonshot-direct")
    raise RuntimeError(
        "No Kimi API key — set OPENROUTER_API_KEY or KIMI_API_KEY in .env"
    )


class KimiClient:
    """Direct HTTP wrapper around Kimi K2.5 via OpenRouter or Moonshot."""

    def __init__(self, model: str | None = None, timeout: float = 180.0) -> None:
        self.base_url, default_model, self.api_key, self.provider = _pick_provider()
        self.model = model or default_model
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.provider == "openrouter":
            self.headers.update(
                {
                    "HTTP-Referer": "https://github.com/eren-karakus0/hermes-comic",
                    "X-Title": "Hermes Comic",
                }
            )
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    @retry(
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=2, max=15),
        reraise=True,
    )
    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        r = httpx.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def complete(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[dict[str, str]] = None,
    ) -> str:
        """One-shot non-streaming completion. Returns content (or reasoning fallback)."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        body = self._post(payload)
        choice = body["choices"][0]
        msg = choice.get("message") or {}
        content = msg.get("content") or msg.get("reasoning") or ""
        usage = body.get("usage") or {}
        finish = choice.get("finish_reason")
        self.total_input_tokens += usage.get("prompt_tokens", 0)
        self.total_output_tokens += usage.get("completion_tokens", 0)
        logger.info(
            "kimi call: in=%s out=%s reasoning=%s finish=%s",
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
            usage.get("reasoning_tokens", 0),
            finish,
        )
        if not content:
            logger.warning(
                "kimi returned EMPTY content (finish=%s, message keys=%s)",
                finish, list(msg.keys())
            )
        return content

    def complete_json(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.3,
        max_tokens: int = 8000,
        max_attempts: int = 3,
    ) -> dict[str, Any]:
        """Complete + parse as JSON with retry on parse failure.

        Kimi K2.5 at high temperature (0.8+) occasionally falls into a
        degenerate repetition loop and outputs unparseable garbage. On
        JSON parse failure we retry with temperature dropped by 0.2 each
        time (e.g. 0.9 → 0.7 → 0.5), which reliably recovers.
        """
        last_text = ""
        last_err: Exception | None = None
        for attempt in range(max_attempts):
            current_temp = max(0.1, temperature - (attempt * 0.2))
            try:
                text = self.complete(
                    messages,
                    temperature=current_temp,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"},
                )
                last_text = text
                if not text.strip():
                    raise RuntimeError("empty content")
                return _parse_json_lenient(text)
            except (json.JSONDecodeError, RuntimeError) as e:
                last_err = e
                logger.warning(
                    "complete_json attempt %d/%d failed (temp=%.2f): %s",
                    attempt + 1, max_attempts, current_temp, str(e)[:120],
                )
                if attempt + 1 < max_attempts:
                    continue
                break

        # All attempts exhausted
        raise RuntimeError(
            f"Kimi response was not parseable JSON after {max_attempts} attempts.\n"
            f"Last error: {last_err}\n"
            f"Last raw text (first 400 chars): {last_text[:400]!r}\n"
            f"Hints: (1) reduce temperature, (2) bump max_tokens, (3) check Kimi status"
        ) from last_err

    def complete_multimodal(
        self,
        text: str,
        image_urls: list[str],
        temperature: float = 0.3,
        max_tokens: int = 4000,
        system: Optional[str] = None,
    ) -> str:
        """Vision call: text + image URLs (http(s) or data:image/png;base64,...)."""
        content: list[dict[str, Any]] = [{"type": "text", "text": text}]
        for u in image_urls:
            content.append({"type": "image_url", "image_url": {"url": u}})
        messages: list[dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})
        return self.complete(messages, temperature=temperature, max_tokens=max_tokens)


def _parse_json_lenient(text: str) -> dict[str, Any]:
    """Parse JSON from a model response, tolerating ```json fences and stray prose."""
    t = text.strip()
    if t.startswith("```"):
        # ```json\n...\n```
        lines = t.split("\n")
        # drop first fence line
        lines = lines[1:]
        # drop trailing fence if present
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        # Best-effort: find the first `{` and last `}`
        start = t.find("{")
        end = t.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(t[start : end + 1])
        raise
