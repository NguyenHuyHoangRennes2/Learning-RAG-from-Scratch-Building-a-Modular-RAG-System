"""Point d'entrée de l'API FastAPI.

Lancement (depuis la racine du projet, venv activé) :
    uvicorn app.main:app --reload
Documentation interactive : http://127.0.0.1:8000/docs
"""

# AsyncIterator : type de la fonction de cycle de vie
from collections.abc import AsyncIterator

# asynccontextmanager : transforme une fonction en gestionnaire de démarrage / arrêt
from contextlib import asynccontextmanager

# FastAPI : l'application web
from fastapi import FastAPI

# Les routes de l'API
from app.api.routes import router

# Configuration centralisée
from app.core.config import Settings, get_settings

# Configuration du logging : l'API est un POINT D'ENTRÉE
from app.core.logging_config import setup_logging

# Construction du pipeline RAG
from app.rag.pipeline import RAGPipeline, build_pipeline


def create_app(
    settings: Settings | None = None,
    pipeline: RAGPipeline | None = None,
) -> FastAPI:
    """Crée l'application ; ``pipeline`` permet d'injecter un pipeline de test."""
    # Configuration fournie, sinon celle du .env / de l'environnement
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Exécuté au démarrage (avant yield) et à l'arrêt (après yield) du serveur."""
        # Configure le logging une seule fois, au démarrage
        setup_logging(app_settings.log_level)

        # Range la configuration et le pipeline dans l'état de l'application
        app.state.settings = app_settings
        app.state.pipeline = pipeline or build_pipeline(app_settings)

        # Préchauffage : charge le modèle d'embeddings MAINTENANT (~15 s) plutôt qu'à la
        # première question d'un utilisateur (1er /ask mesuré à 20 s sans préchauffage)
        _ = app.state.pipeline.ingestion.embedder.dimension

        # Le serveur tourne pendant ce yield
        yield

    # Application avec titre et description (affichés dans /docs)
    app = FastAPI(
        title=app_settings.app_name,
        description="RAG local : questions sur vos PDF, réponses citées (ChromaDB + E5 + Ollama).",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Branche les routes
    app.include_router(router)

    # Renvoie l'application prête
    return app


# Instance utilisée par uvicorn : « uvicorn app.main:app »
app = create_app()
