"""Configuration centralisée de l'application.

Toutes les valeurs paramétrables (chemins, niveau de log, etc.) sont définies ici,
avec une valeur par défaut. Chacune peut être surchargée sans toucher au code :

1. par une variable d'environnement préfixée par ``RAG_`` (ex. ``RAG_LOG_LEVEL=DEBUG``) ;
2. ou par une ligne équivalente dans le fichier ``.env`` à la racine du projet.

Priorité : variable d'environnement > fichier .env > valeur par défaut.

Les autres modules ne lisent jamais ``os.environ`` directement : ils appellent
``get_settings()``.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py -> parents[0] = app/core, parents[1] = app, parents[2] = racine
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Paramètres de l'application, validés et typés par Pydantic."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="RAG_",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "RAG Student Project"
    log_level: LogLevel = "INFO"

    # --- Chemins des données ---
    raw_data_dir: Path = PROJECT_ROOT / "data" / "raw"
    processed_data_dir: Path = PROJECT_ROOT / "data" / "processed"
    chroma_dir: Path = PROJECT_ROOT / "storage" / "chroma"

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> object:
        """Accepte 'debug' comme 'DEBUG'."""
        return value.upper() if isinstance(value, str) else value

    @field_validator("raw_data_dir", "processed_data_dir", "chroma_dir")
    @classmethod
    def _resolve_from_project_root(cls, path: Path) -> Path:
        """Interprète un chemin relatif depuis la racine du projet.

        Sans cela, ``RAG_CHROMA_DIR=storage/chroma`` dépendrait du dossier
        depuis lequel on lance le programme.
        """
        return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache
def get_settings() -> Settings:
    """Retourne l'instance unique des paramètres (créée au premier appel)."""
    return Settings()
