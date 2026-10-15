"""Orchestration du RAG : ingestion des documents (et, en Phase 8, questions-réponses).

Ce module ne contient aucune logique « métier » propre : il ENCHAÎNE les modules
spécialisés, chacun restant indépendant des autres :

    PDF ─► pdf_loader ─► text_cleaner ─► chunker ─► embedding_model ─► chroma_store
"""

# logging pour tracer chaque document traité
import logging

# dataclass pour le compte rendu d'ingestion
from dataclasses import dataclass

# Path représente un chemin de fichier
from pathlib import Path

# Literal : le statut d'ingestion ne peut prendre que quelques valeurs
from typing import Literal

# Le type des stratégies de chunking
from app.core.config import ChunkStrategy

# Vectorisation des chunks
from app.embeddings.embedding_model import EmbeddingModel

# Étape 3 : découpage
from app.ingestion.chunker import chunk_pages

# Étape 1 : lecture des PDF (et son erreur métier)
from app.ingestion.pdf_loader import PDFLoadError, compute_document_id, load_pdf

# Étape 2 : nettoyage
from app.ingestion.text_cleaner import clean_pages

# Stockage des vecteurs
from app.vectorstore.chroma_store import ChromaStore

# Logger nommé d'après le module : "app.rag.pipeline"
logger = logging.getLogger(__name__)

# Statuts possibles d'un document après une tentative d'ingestion
IngestionStatus = Literal["indexed", "skipped", "error"]


@dataclass(frozen=True)
class IngestionReport:
    """Compte rendu de l'ingestion d'UN fichier PDF."""

    # Nom du fichier
    source: str

    # Identifiant du document ("" si le fichier n'a pas pu être lu)
    document_id: str

    # "indexed" (indexé), "skipped" (déjà présent), "error" (illisible ou vide)
    status: IngestionStatus

    # Nombre de pages avec du texte (après nettoyage)
    page_count: int = 0

    # Nombre de chunks indexés
    chunk_count: int = 0

    # Explication lisible (motif d'un saut ou d'une erreur)
    message: str = ""


class IngestionPipeline:
    """Indexe des PDF : lecture → nettoyage → chunking → embeddings → ChromaDB."""

    def __init__(
        self,
        embedder: EmbeddingModel,
        store: ChromaStore,
        chunk_size: int,
        chunk_overlap: int,
        chunk_strategy: ChunkStrategy,
    ) -> None:
        """Reçoit ses composants déjà construits (injection de dépendances)."""
        # Modèle d'embeddings (le MÊME servira pour les questions)
        self.embedder = embedder

        # Base vectorielle
        self.store = store

        # Paramètres de chunking (issus de la configuration)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunk_strategy: ChunkStrategy = chunk_strategy

    def ingest_pdf(self, pdf_path: Path, replace: bool = False) -> IngestionReport:
        """Indexe un PDF.

        - Déjà indexé (même CONTENU) et ``replace=False`` → sauté, rien n'est recalculé.
        - ``replace=True`` → les anciens chunks du document sont SUPPRIMÉS puis recréés
          (utile après un changement des paramètres de chunking).
        """
        # Nom du fichier pour le compte rendu
        source = pdf_path.name

        # Toute erreur de lecture est transformée en compte rendu "error" (pas de plantage)
        try:
            # Identifiant calculé sur le contenu : deux copies ont le même
            document_id = compute_document_id(pdf_path)

            # Évite la double indexation (règle 6.4 de CLAUDE.md)
            if self.store.has_document(document_id) and not replace:
                # Trace et compte rendu
                logger.info("%s déjà indexé (id=%s) : ignoré", source, document_id)
                return IngestionReport(
                    source, document_id, "skipped", message="déjà indexé"
                )

            # Étapes 1 et 2 : lecture puis nettoyage des pages
            pages = clean_pages(load_pdf(pdf_path))
        except PDFLoadError as error:
            # Fichier absent, corrompu ou protégé
            logger.error("%s : %s", source, error)
            return IngestionReport(source, "", "error", message=str(error))

        # Un PDF sans aucun texte (ex. scanné) ne produit rien d'indexable
        if not pages:
            # Compte rendu explicite
            return IngestionReport(
                source, document_id, "error", message="aucun texte extractible"
            )

        # Étape 3 : découpage en chunks
        chunks = chunk_pages(
            pages, self.chunk_size, self.chunk_overlap, self.chunk_strategy
        )

        # Étape 4 : vectorisation (préfixe "passage: " ajouté par EmbeddingModel)
        embeddings = self.embedder.embed_documents([chunk.text for chunk in chunks])

        # En cas de réindexation, on retire d'abord les anciens chunks
        # (avec d'autres paramètres, certains anciens chunk_id n'existeraient plus et resteraient orphelins)
        if replace:
            # Suppression de tous les chunks de ce document
            self.store.delete_document(document_id)

        # Étape 5 : stockage
        self.store.add_chunks(chunks, embeddings)

        # Compte rendu de succès
        return IngestionReport(source, document_id, "indexed", len(pages), len(chunks))

    def ingest_directory(
        self, directory: Path, replace: bool = False
    ) -> list[IngestionReport]:
        """Indexe tous les PDF d'un dossier (ordre alphabétique) ; un échec n'arrête pas les autres."""
        # Un dossier absent est une erreur de configuration
        if not directory.is_dir():
            # Erreur explicite
            raise FileNotFoundError(f"dossier introuvable : {directory}")

        # Indexe chaque PDF et collecte les comptes rendus
        reports = [
            self.ingest_pdf(path, replace) for path in sorted(directory.glob("*.pdf"))
        ]

        # Résumé
        logger.info(
            "Ingestion terminée : %d indexé(s), %d ignoré(s), %d en erreur",
            sum(r.status == "indexed" for r in reports),
            sum(r.status == "skipped" for r in reports),
            sum(r.status == "error" for r in reports),
        )

        # Renvoie tous les comptes rendus
        return reports
