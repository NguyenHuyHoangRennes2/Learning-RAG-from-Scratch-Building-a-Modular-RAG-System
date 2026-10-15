"""Orchestration du RAG : ingestion des documents et questions-réponses.

Ce module ne contient aucune logique « métier » propre : il ENCHAÎNE les modules
spécialisés, chacun restant indépendant des autres.

Ingestion (Phase 5) :
    PDF ─► pdf_loader ─► text_cleaner ─► chunker ─► embedding_model ─► chroma_store

Question-réponse (Phase 8) :
    question ─► retriever ─► prompts ─► LLM ─► citations ─► RAGAnswer
"""

# logging pour tracer chaque document traité et chaque question
import logging

# time.perf_counter : mesure de la latence de chaque étape
import time

# dataclass pour le compte rendu d'ingestion
from dataclasses import dataclass

# Path représente un chemin de fichier
from pathlib import Path

# Literal : le statut d'ingestion ne peut prendre que quelques valeurs
from typing import Literal

# Configuration : type des stratégies et paramètres de construction du pipeline
from app.core.config import ChunkStrategy, Settings

# Vectorisation des chunks et des questions
from app.embeddings.embedding_model import EmbeddingModel

# Génération : client LLM et construction des prompts
from app.generation.llm import LLMClient, OllamaClient
from app.generation.prompts import (
    NO_ANSWER_MESSAGE,
    SYSTEM_PROMPT,
    build_user_prompt,
    extract_citations,
    is_no_answer,
)

# Étape 3 : découpage
from app.ingestion.chunker import chunk_pages

# Étape 1 : lecture des PDF (et son erreur métier)
from app.ingestion.pdf_loader import PDFLoadError, compute_document_id, load_pdf

# Étape 2 : nettoyage
from app.ingestion.text_cleaner import clean_pages

# Structure de la réponse finale
from app.models import RAGAnswer

# Recherche sémantique
from app.retrieval.retriever import Retriever

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


class QuestionAnsweringPipeline:
    """Répond à une question : recherche → prompt → LLM → citations."""

    def __init__(self, retriever: Retriever, llm: LLMClient) -> None:
        """Reçoit le retriever et le client LLM déjà construits (injection de dépendances)."""
        # Recherche sémantique (même modèle d'embeddings que l'indexation)
        self.retriever = retriever

        # N'importe quel objet qui respecte le protocole LLMClient (Ollama, ou un faux en test)
        self.llm = llm

    def ask(self, question: str) -> RAGAnswer:
        """Produit une réponse citée, ou une abstention explicite."""
        # Une question vide n'a pas de sens
        if not question.strip():
            # Erreur explicite (l'API la traduira en HTTP 422)
            raise ValueError("la question ne doit pas être vide")

        # Étape 1 : recherche des chunks pertinents (chronométrée)
        start = time.perf_counter()
        sources = self.retriever.retrieve(question)
        retrieval_ms = 1000 * (time.perf_counter() - start)

        # Aucun chunk (index vide, ou tous sous le seuil) : abstention SANS appeler le LLM
        if not sources:
            # Inutile (et risqué) de demander au LLM de répondre sans aucune source
            logger.info("Aucune source pour %r : abstention", question)
            return RAGAnswer(
                question, NO_ANSWER_MESSAGE, (), (), True, retrieval_ms, 0.0
            )

        # Étape 2 : prompt explicite (sources numérotées puis question)
        user_prompt = build_user_prompt(question, sources)

        # Étape 3 : génération (chronométrée) ; les erreurs LLM remontent à l'appelant
        start = time.perf_counter()
        answer = self.llm.generate(SYSTEM_PROMPT, user_prompt)
        generation_ms = 1000 * (time.perf_counter() - start)

        # Étape 4 : traçabilité, avec les numéros de sources réellement cités (les inventés sont ignorés)
        cited = extract_citations(answer, len(sources))

        # Abstention détectée grâce à la phrase imposée par le prompt
        abstained = is_no_answer(answer)

        # Trace un résumé de la réponse
        logger.info(
            "Question %r : %d source(s), citées %s, abstention=%s, %.0f + %.0f ms",
            question,
            len(sources),
            cited,
            abstained,
            retrieval_ms,
            generation_ms,
        )

        # Réponse complète
        return RAGAnswer(
            question=question,
            answer=answer,
            sources=tuple(sources),
            cited=tuple(cited),
            abstained=abstained,
            retrieval_ms=retrieval_ms,
            generation_ms=generation_ms,
        )


class RAGPipeline:
    """Façade unique de l'application : ingestion + questions-réponses + gestion de l'index.

    C'est le SEUL objet que l'API (Phase 9) manipule.
    """

    def __init__(
        self,
        ingestion: IngestionPipeline,
        qa: QuestionAnsweringPipeline,
        raw_data_dir: Path,
    ) -> None:
        """Assemble les deux sous-pipelines."""
        # Indexation des documents
        self.ingestion = ingestion

        # Questions-réponses
        self.qa = qa

        # Dossier où sont rangés les PDF (ceux envoyés par l'API y sont enregistrés)
        self.raw_data_dir = raw_data_dir

    def ask(self, question: str) -> RAGAnswer:
        """Répond à une question (voir QuestionAnsweringPipeline.ask)."""
        # Délègue au pipeline de questions-réponses
        return self.qa.ask(question)

    def ingest_pdf(self, pdf_path: Path, replace: bool = False) -> IngestionReport:
        """Indexe un PDF (voir IngestionPipeline.ingest_pdf)."""
        # Délègue au pipeline d'ingestion
        return self.ingestion.ingest_pdf(pdf_path, replace)

    def ingest_directory(self, replace: bool = False) -> list[IngestionReport]:
        """Indexe tous les PDF du dossier configuré."""
        # Délègue au pipeline d'ingestion
        return self.ingestion.ingest_directory(self.raw_data_dir, replace)

    def list_documents(self) -> list[dict[str, str | int]]:
        """Documents présents dans l'index."""
        # Lecture directe dans la base vectorielle
        return self.ingestion.store.list_documents()

    def delete_document(self, document_id: str) -> int:
        """Retire un document de l'index ; renvoie le nombre de chunks supprimés."""
        # Suppression dans la base vectorielle
        return self.ingestion.store.delete_document(document_id)


def build_pipeline(settings: Settings, llm: LLMClient | None = None) -> RAGPipeline:
    """Construit le pipeline complet à partir de la configuration.

    Un SEUL objet EmbeddingModel est partagé par l'ingestion et la recherche :
    c'est la garantie que chunks et questions sont vectorisés par le même modèle.
    ``llm`` permet d'injecter un autre client (ex. un faux LLM en test).
    """
    # Modèle d'embeddings unique (chargé au premier usage seulement)
    embedder = EmbeddingModel(
        settings.embedding_model_name,
        settings.embedding_device,
        settings.embedding_batch_size,
    )

    # Base vectorielle persistante
    store = ChromaStore(
        settings.chroma_dir,
        settings.chroma_collection_name,
        settings.embedding_model_name,
    )

    # Client LLM : celui fourni, sinon Ollama configuré
    llm_client = llm or OllamaClient(
        settings.ollama_base_url,
        settings.ollama_model,
        settings.llm_temperature,
        settings.llm_num_ctx,
        settings.llm_timeout_seconds,
    )

    # Assemble les deux sous-pipelines autour des mêmes composants
    return RAGPipeline(
        ingestion=IngestionPipeline(
            embedder,
            store,
            settings.chunk_size,
            settings.chunk_overlap,
            settings.chunk_strategy,
        ),
        qa=QuestionAnsweringPipeline(
            Retriever(
                embedder,
                store,
                settings.retrieval_top_k,
                settings.retrieval_min_score,
            ),
            llm_client,
        ),
        raw_data_dir=settings.raw_data_dir,
    )
