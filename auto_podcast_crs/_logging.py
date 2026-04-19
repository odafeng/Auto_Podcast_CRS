"""Centralized logging setup. Call setup_logging() from CLI entrypoints."""
from __future__ import annotations

import logging
import os
import sys


def setup_logging(level: str | None = None) -> None:
    """Configure root logger once.

    Resolution: explicit arg > AUTOPODCAST_LOG_LEVEL env > INFO.
    Safe to call multiple times (force=True reconfigures).
    """
    resolved = (level or os.environ.get("AUTOPODCAST_LOG_LEVEL") or "INFO").upper()
    logging.basicConfig(
        level=resolved,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
        force=True,
    )
    # Quiet noisy libs
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
