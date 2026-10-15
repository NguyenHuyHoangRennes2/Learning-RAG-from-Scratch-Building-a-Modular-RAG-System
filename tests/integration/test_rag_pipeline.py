"""Tests du pipeline RAG complet : PDF → index → question → prompt → (faux) LLM → réponse citée."""

# Path représente un chemin de fichier
from pathlib import Path

# PyMuPDF sert à fabriquer le PDF de test
import pymupdf

# pytest fournit les fixtures et pytest.raises
import pytest

# Les composants assemblés
from app.core.config import Settings
from app.generation.prompts import NO_ANSWER_MESSAGE, SYSTEM_PROMPT
from app.rag.pipeline import RAGPipeline, build_pipeline
from tests.fakes import FakeLLM, make_fake_pipeline


def make_pipeline(tmp_path: Path, llm: FakeLLM) -> RAGPipeline:
    """Pipeline complet avec faux modèle d'embeddings, vraie ChromaDB et faux LLM."""
    # Constructeur partagé avec les tests de l'API (tests/fakes.py)
    return make_fake_pipeline(tmp_path, llm)


def index_demo_pdf(pipeline: RAGPipeline) -> None:
    """Crée et indexe un PDF de 2 pages (une sur le RAG, une sur le cosinus)."""
    # Dossier des PDF
    pipeline.raw_data_dir.mkdir()

    # PDF de démonstration
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Le rag associe recherche et llm.")
    doc.new_page().insert_text((72, 72), "Le cosinus compare deux vecteurs.")
    doc.save(pipeline.raw_data_dir / "cours.pdf")
    doc.close()

    # Indexe le dossier
    pipeline.ingest_directory()


def test_answer_is_generated_from_retrieved_sources(tmp_path: Path) -> None:
    # Faux LLM qui cite la source 1
    llm = FakeLLM("Le cosinus compare deux vecteurs [1].")
    pipeline = make_pipeline(tmp_path, llm)
    index_demo_pdf(pipeline)

    # Question sur le cosinus
    result = pipeline.ask("Que compare le cosinus ?")

    # Le LLM a reçu les consignes système et un prompt contenant la question et la bonne source
    system_prompt, user_prompt = llm.calls[0]
    assert system_prompt == SYSTEM_PROMPT
    assert "QUESTION : Que compare le cosinus ?" in user_prompt
    assert "Le cosinus compare deux vecteurs." in user_prompt

    # La source [1] est le chunk de la page 2 (le cosinus), et elle est citée
    assert result.sources[0].chunk.citation == "cours.pdf, p. 2"
    assert result.cited == (1,)
    assert result.cited_sources[0].chunk.page_number == 2

    # Pas d'abstention, latences mesurées
    assert not result.abstained
    assert result.retrieval_ms > 0 and result.generation_ms >= 0


def test_llm_abstention_is_detected(tmp_path: Path) -> None:
    # Faux LLM qui applique la règle d'abstention
    pipeline = make_pipeline(tmp_path, FakeLLM(NO_ANSWER_MESSAGE))
    index_demo_pdf(pipeline)

    # Question hors corpus
    result = pipeline.ask("Quelle est la capitale de l'Australie ?")

    # L'abstention est reconnue, aucune source n'est citée
    assert result.abstained
    assert result.cited == ()


def test_empty_index_abstains_without_calling_the_llm(tmp_path: Path) -> None:
    # Pipeline sans aucun document indexé
    llm = FakeLLM()
    pipeline = make_pipeline(tmp_path, llm)

    # Question posée sur un index vide
    result = pipeline.ask("Qu'est-ce que le RAG ?")

    # Abstention immédiate, et le LLM n'a jamais été appelé
    assert result.abstained and result.answer == NO_ANSWER_MESSAGE
    assert llm.calls == []


def test_invented_citations_are_not_reported(tmp_path: Path) -> None:
    # Le faux LLM cite [9] alors qu'il n'y a que 2 sources
    pipeline = make_pipeline(tmp_path, FakeLLM("Réponse [1] et [9]."))
    index_demo_pdf(pipeline)

    # Seule la citation valide est retenue
    assert pipeline.ask("rag et llm").cited == (1,)


def test_blank_question_is_rejected(tmp_path: Path) -> None:
    # Pipeline quelconque
    pipeline = make_pipeline(tmp_path, FakeLLM())

    # Une question vide doit lever une ValueError
    with pytest.raises(ValueError, match="question"):
        # Tentative invalide
        pipeline.ask("   ")


def test_documents_can_be_listed_and_deleted(tmp_path: Path) -> None:
    # Pipeline avec un document indexé
    pipeline = make_pipeline(tmp_path, FakeLLM())
    index_demo_pdf(pipeline)

    # Un document listé
    documents = pipeline.list_documents()
    assert [doc["source"] for doc in documents] == ["cours.pdf"]

    # Suppression : ses chunks disparaissent de l'index
    assert pipeline.delete_document(str(documents[0]["document_id"])) > 0
    assert pipeline.list_documents() == []


def test_build_pipeline_shares_one_embedding_model(tmp_path: Path) -> None:
    # Configuration pointant vers des dossiers temporaires (sans lire le .env)
    settings = Settings(
        _env_file=None, chroma_dir=tmp_path / "chroma", raw_data_dir=tmp_path / "raw"
    )

    # Construit le pipeline réel (le modèle n'est PAS chargé : chargement paresseux)
    pipeline = build_pipeline(settings, llm=FakeLLM())

    # L'ingestion et la recherche utilisent le MÊME objet modèle (règle d'or)
    assert pipeline.ingestion.embedder is pipeline.qa.retriever.embedder

    # Les paramètres viennent bien de la configuration
    assert pipeline.qa.retriever.top_k == settings.retrieval_top_k
    assert pipeline.ingestion.chunk_size == settings.chunk_size
