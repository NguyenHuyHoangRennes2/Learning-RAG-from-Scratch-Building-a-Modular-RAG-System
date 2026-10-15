"""Tests du retriever : faux modèle par mots-clés + vraie ChromaDB."""

# Path représente le dossier de persistance
from pathlib import Path

# pytest fournit les fixtures et pytest.raises
import pytest

# Les composants assemblés
from app.embeddings.embedding_model import EmbeddingModel
from app.models import Chunk
from app.retrieval.retriever import Retriever
from app.vectorstore.chroma_store import ChromaStore
from tests.fakes import KeywordEncoder

# Textes indexés : chacun parle d'un sujet du vocabulaire du faux modèle
TEXTS = [
    "Le rag combine recherche et llm.",
    "Les embeddings sont des vecteurs.",
    "Le cosinus compare deux vecteurs.",
    "Le pdf est découpé en chunk.",
]


@pytest.fixture
def components(tmp_path: Path) -> tuple[EmbeddingModel, ChromaStore]:
    """Modèle factice et base remplie avec les 4 textes."""
    # Faux modèle par mots-clés
    embedder = EmbeddingModel("fake-keywords", encoder=KeywordEncoder())

    # Vraie base vectorielle temporaire
    store = ChromaStore(tmp_path / "chroma", "test_chunks", "fake-keywords")

    # Un chunk par texte (document "doc", page 1)
    chunks = [Chunk("doc", "doc.pdf", 1, i, text) for i, text in enumerate(TEXTS)]

    # Indexe les chunks avec le même modèle que celui des questions
    store.add_chunks(chunks, embedder.embed_documents(TEXTS))

    # Renvoie les deux composants
    return embedder, store


def test_most_similar_chunk_comes_first(
    components: tuple[EmbeddingModel, ChromaStore],
) -> None:
    # Retriever Top-2 sans seuil
    retriever = Retriever(*components, top_k=2)

    # Question sur le cosinus et les vecteurs
    results = retriever.retrieve("Que compare le cosinus entre deux vecteurs ?")

    # Le texte sur le cosinus arrive en tête, 2 résultats au maximum
    assert results[0].chunk.text == "Le cosinus compare deux vecteurs."
    assert len(results) == 2

    # Les scores sont triés du plus grand au plus petit
    assert results[0].score >= results[1].score


def test_top_k_can_be_overridden_per_call(
    components: tuple[EmbeddingModel, ChromaStore],
) -> None:
    # Top-K par défaut = 1, mais on en demande 3 pour cet appel
    retriever = Retriever(*components, top_k=1)

    # 3 résultats renvoyés
    assert len(retriever.retrieve("rag et llm", top_k=3)) == 3


def test_min_score_filters_weak_results(
    components: tuple[EmbeddingModel, ChromaStore],
) -> None:
    # Seuil très élevé : seul un chunk presque identique à la question passe
    retriever = Retriever(*components, top_k=4, min_score=0.9)

    # Question qui ne correspond qu'au premier texte
    results = retriever.retrieve("rag llm")

    # Tous les résultats gardés dépassent le seuil, et les plus faibles ont été écartés
    assert all(result.score >= 0.9 for result in results)
    assert len(results) < 4


def test_invalid_top_k_is_rejected(
    components: tuple[EmbeddingModel, ChromaStore],
) -> None:
    # Top-K nul
    with pytest.raises(ValueError, match="top_k"):
        # Tentative invalide
        Retriever(*components, top_k=0)
