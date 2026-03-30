"""Smoke import tests (DEV_SPEC A2).

Validates that top-level packages under ``src/`` remain importable.
"""

from __future__ import annotations

import pytest


@pytest.mark.unit
def test_import_mcp_server() -> None:
    import mcp_server  # noqa: F401


@pytest.mark.unit
def test_import_core() -> None:
    import core  # noqa: F401


@pytest.mark.unit
def test_import_ingestion() -> None:
    import ingestion  # noqa: F401


@pytest.mark.unit
def test_import_libs() -> None:
    import libs  # noqa: F401


@pytest.mark.unit
def test_import_observability() -> None:
    import observability  # noqa: F401
