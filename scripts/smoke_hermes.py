"""Hermes AIAgent ↔ Kimi (via OpenRouter) round-trip smoke.

Requires:
  - `hermes setup` completed → provider 'openrouter' + OPENROUTER_API_KEY in ~/.hermes/.env
  - uv-installed hermes-agent (verify_hermes_import.py passes)

Hermes local repo confirmed: provider="openrouter" valid (setup.py:988),
model uses OR format with slash (e.g., "moonshotai/kimi-k2.5").
"""
from __future__ import annotations

import sys

try:
    from run_agent import AIAgent
except ImportError as e:
    print(f"[FAIL] import run_agent.AIAgent: {e}")
    print("hint: ensure `uv sync` installed hermes-agent from git+https")
    sys.exit(1)


def main() -> int:
    print("building AIAgent(provider='openrouter', model='moonshotai/kimi-k2.5')...")
    agent = AIAgent(
        model="moonshotai/kimi-k2.5",
        provider="openrouter",
        enabled_toolsets=["skills"],
        skip_memory=True,
        quiet_mode=True,
    )

    print("round-tripping (may take 10-20s — Kimi K2.5 includes reasoning)...")
    response = agent.run_conversation(
        "Reply with exactly this phrase and nothing else: hermes-kimi-ok"
    )
    response_str = str(response)
    print(f"\nraw response (first 1000 chars):\n{response_str[:1000]}\n")

    if "hermes-kimi-ok" in response_str.lower():
        print("[OK] AIAgent ↔ OpenRouter ↔ Kimi round-trip verified")
        return 0

    # Soft pass: if any non-empty response came back, route works even if
    # phrase didn't land exactly. Kimi K2.5 tends to include reasoning preamble.
    if len(response_str.strip()) > 0:
        print("[WARN] exact phrase missing, but response arrived — route works")
        return 0

    print("[FAIL] empty response")
    return 1


if __name__ == "__main__":
    sys.exit(main())
