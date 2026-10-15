"""Schémas Pydantic de l'API : le CONTRAT des requêtes et des réponses HTTP.

Pydantic est utilisé ici, à la frontière de l'application (données venues de
l'extérieur), et non pour les objets internes (dataclasses de app/models.py) :
il valide les entrées, convertit les types et génère la documentation OpenAPI (/docs).
"""

# Literal : valeurs autorisées du statut d'ingestion
from typing import Literal

# BaseModel : classe de base des schémas ; Field : contraintes et descriptions
from pydantic import BaseModel, Field

# Les objets internes convertis en réponses HTTP
from app.models import RAGAnswer
from app.rag.pipeline import IngestionReport


class AskRequest(BaseModel):
    """Corps de POST /ask."""

    # Question de l'utilisateur : ni vide, ni démesurée (protège le prompt du LLM)
    question: str = Field(
        min_length=1, max_length=1000, examples=["Qu'est-ce que le RAG ?"]
    )


class SourceOut(BaseModel):
    """Un passage fourni au LLM, avec tout ce qu'il faut pour le vérifier."""

    # Numéro utilisé dans la réponse : [1], [2]...
    number: int

    # Identifiants pour la traçabilité
    document_id: str
    chunk_id: str

    # Origine lisible
    source: str
    page_number: int

    # Similarité cosinus avec la question
    score: float

    # Texte du passage
    text: str

    # Vrai si la réponse cite ce passage
    cited: bool


class AskResponse(BaseModel):
    """Réponse de POST /ask."""

    question: str
    answer: str
    abstained: bool
    sources: list[SourceOut]
    retrieval_ms: float
    generation_ms: float

    @classmethod
    def from_answer(cls, result: RAGAnswer) -> "AskResponse":
        """Convertit la réponse interne du pipeline en réponse HTTP."""
        # Une entrée par source, numérotée à partir de 1, en signalant les sources citées
        sources = [
            SourceOut(
                number=number,
                document_id=item.chunk.document_id,
                chunk_id=item.chunk.chunk_id,
                source=item.chunk.source,
                page_number=item.chunk.page_number,
                score=round(item.score, 4),
                text=item.chunk.text,
                cited=number in result.cited,
            )
            for number, item in enumerate(result.sources, start=1)
        ]

        # Réponse complète
        return cls(
            question=result.question,
            answer=result.answer,
            abstained=result.abstained,
            sources=sources,
            retrieval_ms=round(result.retrieval_ms, 1),
            generation_ms=round(result.generation_ms, 1),
        )


class IngestResponse(BaseModel):
    """Réponse de POST /documents (compte rendu d'ingestion)."""

    source: str
    document_id: str
    status: Literal["indexed", "skipped", "error"]
    page_count: int
    chunk_count: int
    message: str

    @classmethod
    def from_report(cls, report: IngestionReport) -> "IngestResponse":
        """Convertit le compte rendu interne en réponse HTTP."""
        # Mêmes champs, un à un
        return cls(
            source=report.source,
            document_id=report.document_id,
            status=report.status,
            page_count=report.page_count,
            chunk_count=report.chunk_count,
            message=report.message,
        )


class DocumentOut(BaseModel):
    """Un document présent dans l'index (GET /documents)."""

    document_id: str
    source: str
    chunk_count: int


class DeleteResponse(BaseModel):
    """Réponse de DELETE /documents/{document_id}."""

    document_id: str
    deleted_chunks: int


class HealthResponse(BaseModel):
    """Réponse de GET /health : l'état de chaque brique."""

    # "ok" si l'API répond
    status: Literal["ok"]

    # Contenu de l'index
    documents: int
    chunks: int

    # Le LLM est-il joignable, avec son modèle installé ?
    llm_available: bool
    llm_model: str
