from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from core.settings import load_settings


def test_load_settings_success() -> None:
    """Should parse the project's default config without error."""
    settings = load_settings(str(Path("config") / "settings.yaml"))
    assert settings.embedding.provider
    assert settings.embedding.model
    assert settings.vector_store.backend
    assert settings.observability.enabled is True


def test_load_settings_missing_embedding_provider(tmp_path: Path) -> None:
    """Missing a critical field should raise a readable error with field path."""
    config_path = Path("config") / "settings.yaml"
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    # Remove the required key.
    data["embedding"].pop("provider", None)

    bad_path = tmp_path / "settings.yaml"
    bad_path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")

    with pytest.raises(ValueError) as exc:
        load_settings(str(bad_path))

    assert "embedding.provider" in str(exc.value)

