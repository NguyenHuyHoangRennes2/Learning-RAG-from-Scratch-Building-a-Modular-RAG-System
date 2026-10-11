"""Tests unitaires de la configuration centralisée (app/core/config.py)."""

import pytest
from pydantic import ValidationError

from app.core.config import PROJECT_ROOT, Settings


def make_settings() -> Settings:
    """Crée des Settings sans lire le fichier .env réel du projet."""
    return Settings(_env_file=None)


def test_default_values() -> None:
    settings = make_settings()
    assert settings.log_level == "INFO"
    assert settings.chroma_dir == PROJECT_ROOT / "storage" / "chroma"


def test_environment_variable_overrides_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RAG_LOG_LEVEL", "debug")
    assert make_settings().log_level == "DEBUG"


def test_relative_path_is_resolved_from_project_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RAG_CHROMA_DIR", "storage/test_chroma")
    assert make_settings().chroma_dir == PROJECT_ROOT / "storage" / "test_chroma"


def test_invalid_log_level_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_LOG_LEVEL", "VERBOSE")
    with pytest.raises(ValidationError):
        make_settings()
