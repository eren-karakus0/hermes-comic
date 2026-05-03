"""Hermes Comic — AI comic series companion.

Auto-loads .env from the repo root so subprocess callers (Hermes, CI, scripts)
don't need to `source .env` before invoking `uv run comic …`. This is the one
invariant we want: the CLI works the moment it's installed.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

__version__ = "0.1.0"


def _autoload_dotenv() -> None:
    """Load .env from the repo root, walking up from this file."""
    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        candidate = parent / ".env"
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            os.environ.setdefault("HERMES_COMIC_ENV_LOADED", str(candidate))
            return


_autoload_dotenv()
