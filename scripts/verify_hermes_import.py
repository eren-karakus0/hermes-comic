"""Verify run_agent.AIAgent is importable with expected signature.

Runs after `uv sync` installs hermes-agent via git+https.
"""
from __future__ import annotations

import inspect
import sys

try:
    from run_agent import AIAgent
except ImportError as e:
    print(f"[FAIL] import run_agent.AIAgent: {e}")
    print("hint: did `uv sync` complete? check `uv pip list | grep hermes`")
    sys.exit(1)

sig = inspect.signature(AIAgent.__init__)
params = list(sig.parameters.keys())
print(f"[OK] imported run_agent.AIAgent")
print(f"signature param count: {len(params)}")
print(f"first 20 params: {params[:20]}")

expected = {"model", "provider", "enabled_toolsets", "skip_memory", "base_url", "api_key"}
missing = expected - set(params)
if missing:
    print(f"[FAIL] missing expected params: {missing}")
    sys.exit(1)

print("[OK] all expected params present")
