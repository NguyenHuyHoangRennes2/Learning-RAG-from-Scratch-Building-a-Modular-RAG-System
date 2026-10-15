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


def test_chunking_default_values() -> None:
    # Crée la configuration sans .env ni variable d'environnement
    settings = make_settings()

    # Vérifie les valeurs par défaut du chunking
    assert (settings.chunk_size, settings.chunk_overlap) == (800, 150)
    assert settings.chunk_strategy == "sentence"


def test_overlap_greater_or_equal_to_size_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Chevauchement égal à la taille : le découpage n'avancerait jamais
    monkeypatch.setenv("RAG_CHUNK_SIZE", "100")
    monkeypatch.setenv("RAG_CHUNK_OVERLAP", "100")

    # La configuration doit être refusée, avec un message qui cite chunk_overlap
    with pytest.raises(ValidationError, match="chunk_overlap"):
        # Tentative de création invalide
        make_settings()


def test_non_positive_chunk_size_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    # Une taille de 0 caractère n'a pas de sens
    monkeypatch.setenv("RAG_CHUNK_SIZE", "0")

    # Field(gt=0) doit refuser la valeur
    with pytest.raises(ValidationError):
        # Tentative de création invalide
        make_settings()


def test_embedding_default_values() -> None:
    # Crée la configuration sans .env ni variable d'environnement
    settings = make_settings()

    # Modèle multilingue, sur CPU, lots de 32
    assert settings.embedding_model_name == "intfloat/multilingual-e5-small"
    assert (settings.embedding_device, settings.embedding_batch_size) == ("cpu", 32)


def test_unknown_chunk_strategy_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    # "semantic" ne fait pas partie des stratégies autorisées (Literal)
    monkeypatch.setenv("RAG_CHUNK_STRATEGY", "semantic")

    # La configuration doit être refusée
    with pytest.raises(ValidationError):
        # Tentative de création invalide
        make_settings()
