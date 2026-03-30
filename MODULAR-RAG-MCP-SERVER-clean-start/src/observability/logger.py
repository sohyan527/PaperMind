"""Observability logging helpers.

For DEV_SPEC A3, we only need a minimal `get_logger()` that logs to `stderr`.
Later phases extend this to JSON Lines + trace persistence.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


def get_logger(name: str = "modular-rag-mcp-server", *, level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Get a stderr logger (and optionally a file logger).

    Args:
        name: Logger name.
        level: Logging level string (e.g., "INFO", "DEBUG").
        log_file: Optional path to append logs.

    Returns:
        A configured `logging.Logger`.
    """

    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when called multiple times.
    if getattr(logger, "_configured_by_get_logger", False):
        return logger

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(numeric_level)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    if log_file:
        log_path = Path(log_file)
        if log_path.parent and not log_path.parent.exists():
            log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    setattr(logger, "_configured_by_get_logger", True)
    return logger
