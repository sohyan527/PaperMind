"""MCP Server 启动入口.

DEV_SPEC A3: At startup, load and validate `config/settings.yaml` with
fail-fast behavior. Full MCP server bootstrapping happens in later phases.
"""

from __future__ import annotations

from pathlib import Path

from core.settings import load_settings
from observability.logger import get_logger


def main() -> None:
    """Load configuration and validate it."""

    repo_root = Path(__file__).resolve().parent
    settings_path = repo_root / "config" / "settings.yaml"

    # Use a minimal stderr logger for startup diagnostics.
    logger = get_logger()
    settings = load_settings(str(settings_path))
    logger.info("Settings loaded: %s", settings.project.get("name"))

    # Full server startup will be implemented in Phase E.
    _ = settings


if __name__ == "__main__":
    main()
