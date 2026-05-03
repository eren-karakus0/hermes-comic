"""Kimi K2.5 smoke test with full diagnostics.

Verifies auth, balance, and round-trip.
On content=None, dumps full response body for debugging.
"""
from __future__ import annotations

import json
import os
import sys

import httpx

OR_KEY = os.environ.get("OPENROUTER_API_KEY")
KIMI_KEY = os.environ.get("KIMI_API_KEY")

if OR_KEY:
    KEY = OR_KEY
    BASE = "https://openrouter.ai/api/v1"
    MODEL = "moonshotai/kimi-k2.5"
    PROVIDER = "openrouter"
    EXTRA_HEADERS = {
        "HTTP-Referer": "https://github.com/eren-karakus0/hermes-comic",
        "X-Title": "Hermes Comic",
    }
elif KIMI_KEY:
    KEY = KIMI_KEY
    BASE = "https://api.moonshot.ai/v1"
    MODEL = "kimi-k2.5"
    PROVIDER = "moonshot-direct"
    EXTRA_HEADERS = {}
else:
    print("[FAIL] neither OPENROUTER_API_KEY nor KIMI_API_KEY set")
    sys.exit(1)

print(f"provider: {PROVIDER} | model: {MODEL} | base: {BASE}")

HEADERS = {
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    **EXTRA_HEADERS,
}


def check_credits_openrouter() -> None:
    """Verify OR auth + show balance."""
    if PROVIDER != "openrouter":
        return
    r = httpx.get(f"{BASE}/credits", headers=HEADERS, timeout=30)
    if r.status_code != 200:
        print(f"[WARN] /credits HTTP {r.status_code}: {r.text[:300]}")
        return
    body = r.json()
    print(f"[info] OR credits: {json.dumps(body, indent=2)}")


def _parse_content(body: dict) -> str | None:
    """Robustly extract assistant content from OR/Moonshot response."""
    choices = body.get("choices") or []
    if not choices:
        return None
    msg = choices[0].get("message") or {}
    # primary
    content = msg.get("content")
    # some OR routes put text in reasoning
    if not content:
        content = msg.get("reasoning")
    return content


def _dump(body: dict) -> None:
    """Pretty-print full response body to stderr for diagnosis."""
    print("--- full response body ---")
    print(json.dumps(body, indent=2, ensure_ascii=False)[:2000])
    print("---")


def test_text() -> bool:
    print("\n[test_text] POST /chat/completions...")
    r = httpx.post(
        f"{BASE}/chat/completions",
        headers=HEADERS,
        json={
            "model": MODEL,
            "messages": [
                {"role": "user", "content": "Reply with exactly: hermes-comic-phase-0-ok"}
            ],
            "temperature": 0,
            "max_tokens": 30,
        },
        timeout=60,
    )
    if r.status_code != 200:
        print(f"[FAIL] text HTTP {r.status_code}: {r.text[:500]}")
        return False
    body = r.json()
    out = _parse_content(body)
    if out is None:
        print(f"[FAIL] content is null")
        finish = (body.get("choices") or [{}])[0].get("finish_reason")
        print(f"finish_reason: {finish}")
        if body.get("error"):
            print(f"error field: {body['error']}")
        _dump(body)
        return False
    if "hermes-comic-phase-0-ok" in out.lower():
        print(f"[OK] text: {out.strip()}")
        return True
    print(f"[WARN] unexpected text (but response arrived): {out.strip()[:200]}")
    return True  # response exists → route works; phrase mismatch is not a blocker


def test_multimodal() -> bool:
    print("\n[test_multimodal] POST /chat/completions (image_url)...")
    img_url = (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/"
        "PNG_transparency_demonstration_1.png/320px-PNG_transparency_demonstration_1.png"
    )
    r = httpx.post(
        f"{BASE}/chat/completions",
        headers=HEADERS,
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in one short sentence."},
                        {"type": "image_url", "image_url": {"url": img_url}},
                    ],
                }
            ],
            "temperature": 0.3,
            "max_tokens": 100,
        },
        timeout=90,
    )
    if r.status_code != 200:
        print(f"[WARN] multimodal HTTP {r.status_code}: {r.text[:300]}")
        return False
    body = r.json()
    out = _parse_content(body)
    if not out:
        print(f"[WARN] multimodal content empty")
        finish = (body.get("choices") or [{}])[0].get("finish_reason")
        print(f"finish_reason: {finish}")
        _dump(body)
        return False
    print(f"[OK] multimodal: {out.strip()[:200]}")
    return True


if __name__ == "__main__":
    print("=== Kimi smoke test (diagnostic) ===")
    check_credits_openrouter()
    text_ok = test_text()
    mm_ok = test_multimodal()
    print("\n=== summary ===")
    print(f"text: {'OK' if text_ok else 'FAIL'}")
    print(f"multimodal: {'OK' if mm_ok else 'WARN (non-blocking)'}")
    sys.exit(0 if text_ok else 1)
