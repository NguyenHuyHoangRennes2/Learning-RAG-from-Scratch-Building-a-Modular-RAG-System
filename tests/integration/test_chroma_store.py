"""Tests de la base vectorielle avec une VRAIE ChromaDB, dans un dossier temporaire.

Les vecteurs sont fabriqués à la main (3 dimensions) : pas besoin du modèle
d'embeddings, et les distances attendues se calculent de tête.
"""

# math.sqrt pour normaliser les vecteurs de test
import math

# Path représente le dossier de persistance
from pathlib import Path

# pytest fournit les fixtures, pytest.raises et pytest.approx
import pytest

# Les structures de données manipulées
from app.models import Chunk

# Ce que l'on teste
from app.vectorstore.chroma_store import ChromaStore, EmbeddingModelMismatchError

# Nom de modèle fictif enregistré dans la collection
MODEL = "fake-model"


def unit(*values: float) -> list[float]:
    """Normalise un vecteur (norme = 1), comme le fait EmbeddingModel."""
    # Norme du vecteur
    norm = math.sqrt(sum(v * v for v in values))

    # Chaque composante divisée par la norme
    return [v / norm for v in values]


def make_chunk(document_id: str, page: int, index: int, text: str) -> Chunk:
    """Crée un chunk de test (source dérivée du document_id)."""
    # Source lisible, ex. "doc_a.pdf"
    return Chunk(document_id, f"{document_id}.pdf", page, index, text)


# Trois chunks et leurs vecteurs : chacun pointe vers un axe différent
CHUNKS = [
    make_chunk("doc_a", 1, 0, "Le RAG combine recherche et génération."),
    make_chunk("doc_a", 2, 0, "Les embeddings représentent le sens."),
    make_chunk("doc_b", 1, 0, "ChromaDB stocke les vecteurs."),
]
VECTORS = [unit(1, 0, 0), unit(0, 1, 0), unit(0, 0, 1)]


@pytest.fixture
def store(tmp_path: Path) -> ChromaStore:
    """Une base vectorielle neuve, remplie avec les 3 chunks de test."""
    # Base persistée dans un dossier temporaire propre à ce test
    chroma = ChromaStore(tmp_path / "chroma", "test_chunks", MODEL)

    # Indexe les 3 chunks
    chroma.add_chunks(CHUNKS, VECTORS)

    # Renvoie la base prête à l'emploi
    return chroma


def test_chunks_are_stored(store: ChromaStore) -> None:
    # Les 3 chunks sont présents
    assert store.count() == 3


def test_reindexing_the_same_chunks_does_not_duplicate(store: ChromaStore) -> None:
    # Réindexe exactement les mêmes chunks (mêmes chunk_id)
    store.add_chunks(CHUNKS, VECTORS)

    # upsert remplace au lieu d'ajouter : toujours 3 chunks
    assert store.count() == 3


def test_search_returns_closest_first_with_cosine_score(store: ChromaStore) -> None:
    # Question proche de l'axe 1 (doc_a p.1), un peu de l'axe 2
    results = store.search(unit(1, 0.5, 0), top_k=2)

    # Le plus proche est le chunk de l'axe 1, puis celui de l'axe 2
    assert [r.chunk.chunk_id for r in results] == ["doc_a-p1-c0", "doc_a-p2-c0"]

    # Score = cosinus : (1, 0.5, 0)/‖·‖ · (1, 0, 0) = 1 / √1.25 ≈ 0.894
    assert results[0].score == pytest.approx(1 / math.sqrt(1.25), abs=1e-3)

    # Le chunk est reconstruit à l'identique (texte et métadonnées)
    assert results[0].chunk == CHUNKS[0]


def test_top_k_larger_than_collection_returns_everything(store: ChromaStore) -> None:
    # On demande 10 résultats alors qu'il n'y a que 3 chunks
    assert len(store.search(unit(1, 1, 1), top_k=10)) == 3


def test_empty_store_returns_no_result(tmp_path: Path) -> None:
    # Base neuve, vide
    empty = ChromaStore(tmp_path / "empty", "test_chunks", MODEL)

    # Aucune erreur, simplement aucun résultat
    assert empty.search(unit(1, 0, 0), top_k=3) == []


def test_data_persists_on_disk(tmp_path: Path) -> None:
    # Première « session » : on indexe
    ChromaStore(tmp_path / "chroma", "test_chunks", MODEL).add_chunks(CHUNKS, VECTORS)

    # Seconde « session » : on rouvre la même base depuis le disque
    reopened = ChromaStore(tmp_path / "chroma", "test_chunks", MODEL)

    # Les chunks sont toujours là, et la recherche fonctionne
    assert reopened.count() == 3
    assert reopened.search(unit(0, 0, 1), top_k=1)[0].chunk.document_id == "doc_b"


def test_other_embedding_model_is_rejected(tmp_path: Path) -> None:
    # Collection créée avec le modèle "fake-model"
    ChromaStore(tmp_path / "chroma", "test_chunks", MODEL)

    # La rouvrir avec un autre modèle doit échouer (vecteurs incompatibles)
    with pytest.raises(EmbeddingModelMismatchError, match="réindexez"):
        # Tentative invalide
        ChromaStore(tmp_path / "chroma", "test_chunks", "another-model")


def test_documents_can_be_listed_checked_and_deleted(store: ChromaStore) -> None:
    # Deux documents : doc_a (2 chunks) et doc_b (1 chunk)
    assert store.list_documents() == [
        {"document_id": "doc_a", "source": "doc_a.pdf", "chunk_count": 2},
        {"document_id": "doc_b", "source": "doc_b.pdf", "chunk_count": 1},
    ]

    # doc_a est présent, un document inconnu ne l'est pas
    assert store.has_document("doc_a")
    assert not store.has_document("inconnu")

    # Supprime doc_a : 2 chunks retirés, il en reste 1
    assert store.delete_document("doc_a") == 2
    assert store.count() == 1
    assert not store.has_document("doc_a")


def test_invalid_arguments_are_rejected(store: ChromaStore) -> None:
    # Nombre de chunks et de vecteurs différent
    with pytest.raises(ValueError, match="vecteur"):
        # Tentative invalide
        store.add_chunks(CHUNKS, VECTORS[:2])

    # top_k nul
    with pytest.raises(ValueError, match="top_k"):
        # Tentative invalide
        store.search(unit(1, 0, 0), top_k=0)
