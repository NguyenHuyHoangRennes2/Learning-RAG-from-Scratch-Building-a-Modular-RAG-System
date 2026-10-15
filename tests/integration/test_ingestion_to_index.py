"""Test d'intégration de l'indexation : PDF → pages → chunks → vecteurs → ChromaDB.

Tous les vrais modules sont utilisés, sauf le modèle d'embeddings, remplacé par
un faux encodeur par mots-clés (rapide et prévisible).
"""

# shutil.copy crée une copie exacte d'un fichier (pour tester les doublons)
import shutil

# Path représente un chemin de fichier
from pathlib import Path

# PyMuPDF sert à fabriquer les PDF de test
import pymupdf

# pytest fournit les fixtures
import pytest

# Les composants assemblés
from app.embeddings.embedding_model import EmbeddingModel
from app.rag.pipeline import IngestionPipeline
from app.vectorstore.chroma_store import ChromaStore
from tests.fakes import KeywordEncoder


def create_pdf(path: Path, pages: list[str]) -> None:
    """Crée un PDF simple, une chaîne de texte par page."""
    # Document vide, en mémoire
    doc = pymupdf.open()

    # Une page par texte
    for text in pages:
        # Écrit le texte en haut à gauche
        doc.new_page().insert_text((72, 72), text)

    # Enregistre puis libère le document
    doc.save(path)
    doc.close()


@pytest.fixture
def pipeline(tmp_path: Path) -> IngestionPipeline:
    """Pipeline d'ingestion avec une vraie ChromaDB et un faux encodeur."""
    # Faux modèle : le nom "fake-keywords" est enregistré dans la collection
    embedder = EmbeddingModel("fake-keywords", encoder=KeywordEncoder())

    # Vraie base vectorielle dans un dossier temporaire
    store = ChromaStore(tmp_path / "chroma", "test_chunks", "fake-keywords")

    # Petits chunks (200 / 40) pour obtenir plusieurs chunks par page
    return IngestionPipeline(embedder, store, 200, 40, "sentence")


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    """Dossier contenant deux PDF valides et un fichier corrompu."""
    # Dossier d'entrée
    raw = tmp_path / "raw"
    raw.mkdir()

    # Document sur le RAG
    create_pdf(raw / "rag.pdf", ["Le RAG utilise un LLM.\nLe RAG cite ses sources."])

    # Document sur les embeddings
    create_pdf(
        raw / "vecteurs.pdf",
        ["Les embeddings sont des vecteurs.\nLe cosinus compare deux vecteurs."],
    )

    # Faux PDF : du texte qui n'est pas un PDF
    (raw / "casse.pdf").write_text("ceci n'est pas un PDF", encoding="utf-8")

    # Renvoie le dossier prêt
    return raw


def test_directory_is_indexed_and_bad_file_reported(
    pipeline: IngestionPipeline, raw_dir: Path
) -> None:
    # Indexe tout le dossier
    reports = pipeline.ingest_directory(raw_dir)

    # Un compte rendu par fichier, dans l'ordre alphabétique
    assert [(r.source, r.status) for r in reports] == [
        ("casse.pdf", "error"),
        ("rag.pdf", "indexed"),
        ("vecteurs.pdf", "indexed"),
    ]

    # Les chunks des deux documents valides sont dans l'index
    assert pipeline.store.count() == sum(r.chunk_count for r in reports) > 0


def test_second_run_skips_already_indexed_documents(
    pipeline: IngestionPipeline, raw_dir: Path
) -> None:
    # Première indexation
    pipeline.ingest_directory(raw_dir)
    count_after_first_run = pipeline.store.count()

    # Une copie identique (même contenu, autre nom) est ajoutée au dossier
    shutil.copy(raw_dir / "rag.pdf", raw_dir / "rag_copie.pdf")

    # Seconde indexation
    reports = pipeline.ingest_directory(raw_dir)

    # Rien n'est réindexé : les documents (et la copie) sont reconnus par leur contenu
    assert {r.status for r in reports if r.source != "casse.pdf"} == {"skipped"}
    assert pipeline.store.count() == count_after_first_run


def test_replace_reindexes_without_duplicates(
    pipeline: IngestionPipeline, raw_dir: Path
) -> None:
    # Première indexation, puis réindexation forcée
    pipeline.ingest_directory(raw_dir)
    count_after_first_run = pipeline.store.count()
    reports = pipeline.ingest_directory(raw_dir, replace=True)

    # Les documents sont réindexés, sans doublon
    assert [r.status for r in reports] == ["error", "indexed", "indexed"]
    assert pipeline.store.count() == count_after_first_run


def test_indexed_chunks_are_searchable(
    pipeline: IngestionPipeline, raw_dir: Path
) -> None:
    # Indexe le dossier
    pipeline.ingest_directory(raw_dir)

    # Une question sur le cosinus et les vecteurs (vectorisée par le même faux modèle)
    question = pipeline.embedder.embed_query(
        "Que compare le cosinus entre deux vecteurs ?"
    )

    # Le chunk le plus proche vient du document sur les embeddings
    best = pipeline.store.search(question, top_k=1)[0]
    assert best.chunk.source == "vecteurs.pdf"


def test_missing_directory_is_an_error(
    pipeline: IngestionPipeline, tmp_path: Path
) -> None:
    # Un dossier inexistant doit lever une erreur claire
    with pytest.raises(FileNotFoundError, match="introuvable"):
        # Tentative invalide
        pipeline.ingest_directory(tmp_path / "absent")
