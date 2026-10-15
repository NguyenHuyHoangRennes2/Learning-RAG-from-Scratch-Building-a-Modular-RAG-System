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

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# app/core/config.py -> parents[0] = app/core, parents[1] = app, parents[2] = racine
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Stratégies de découpage disponibles : "fixed" (taille fixe) ou "sentence" (respecte les phrases)
ChunkStrategy = Literal["fixed", "sentence"]


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

    # --- Chunking (Phase 3) ---
    # Taille maximale d'un chunk, en caractères ; gt=0 interdit 0 et les valeurs négatives
    chunk_size: int = Field(default=800, gt=0)

    # Nombre de caractères repris du chunk précédent ; ge=0 autorise 0 (pas de chevauchement)
    chunk_overlap: int = Field(default=150, ge=0)

    # Stratégie de découpage utilisée par défaut
    chunk_strategy: ChunkStrategy = "sentence"

    # --- Embeddings (Phase 4) ---
    # Modèle multilingue (nos PDF sont en français) : 384 dimensions, 512 tokens max
    embedding_model_name: str = "intfloat/multilingual-e5-small"

    # Matériel de calcul : "cpu" (le GPU de 4 Go est réservé à Ollama)
    embedding_device: str = "cpu"

    # Nombre de textes vectorisés en une seule passe du modèle
    embedding_batch_size: int = Field(default=32, gt=0)

    @model_validator(mode="after")
    def _check_chunk_overlap(self) -> "Settings":
        """Vérifie une règle qui porte sur DEUX champs : overlap < size."""
        # Un chevauchement >= à la taille ferait reculer (ou piétiner) le découpage indéfiniment
        if self.chunk_overlap >= self.chunk_size:
            # Configuration refusée dès le démarrage (fail fast)
            raise ValueError(
                f"chunk_overlap ({self.chunk_overlap}) doit être < chunk_size ({self.chunk_size})"
            )

        # Configuration valide : on renvoie l'objet
        return self

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
