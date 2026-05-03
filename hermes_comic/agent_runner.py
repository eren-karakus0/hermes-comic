"""Thin wrapper around Hermes `run_agent.AIAgent` with workspace env injection.

Used when the user wants to invoke the `comic-series` skill interactively via
Hermes itself (e.g. `hermes` then '/comic-series ...'). Phase 1 keeps this light.
"""
from __future__ import annotations

import os
from pathlib import Path

from hermes_comic.canon import get_workspace


def build_agent(
    workspace: str | Path | None = None,
    model: str = "moonshotai/kimi-k2.5",
    provider: str = "openrouter",
):
    """Instantiate Hermes AIAgent with our workspace env var set."""
    from run_agent import AIAgent

    ws = Path(workspace) if workspace else get_workspace()
    os.environ["HERMES_COMIC_WORKSPACE"] = str(ws)

    return AIAgent(
        model=model,
        provider=provider,
        enabled_toolsets=["skills", "file", "terminal"],
        skip_memory=False,
        quiet_mode=True,
    )
