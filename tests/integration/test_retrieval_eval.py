"""Test de la boucle d'évaluation de la recherche (faux modèle + vraie ChromaDB)."""

# Path représente le dossier de persistance
from pathlib import Path

# pytest fournit pytest.approx
import pytest

# Les composants assemblés
from app.embeddings.embedding_model import EmbeddingModel
from app.evaluation.dataset import EvalQuestion
from app.evaluation.retrieval_eval import evaluate_retrieval
from app.models import Chunk
from app.retrieval.retriever import Retriever
from app.vectorstore.chroma_store import ChromaStore
from tests.fakes import KeywordEncoder


def test_metrics_are_computed_for_answerable_questions_only(tmp_path: Path) -> None:
    # Faux modèle par mots-clés et vraie base temporaire
    embedder = EmbeddingModel("fake-keywords", encoder=KeywordEncoder())
    store = ChromaStore(tmp_path / "chroma", "test_chunks", "fake-keywords")

    # Deux chunks : un sur le cosinus, un sur le pdf
    texts = ["Le cosinus compare deux vecteurs.", "Le pdf est lu page par page."]
    store.add_chunks(
        [Chunk("doc", "doc.pdf", 1, i, t) for i, t in enumerate(texts)],
        embedder.embed_documents(texts),
    )

    # Une question avec réponse (preuve dans le chunk 0) et une question sans réponse
    questions = [
        EvalQuestion("a", "facile", "cosinus vecteurs", ("compare deux vecteurs",), ()),
        EvalQuestion("b", "sans-réponse", "rag llm", (), ()),
    ]

    # Évalue avec K = 1 et K = 2
    evaluation = evaluate_retrieval(
        Retriever(embedder, store, top_k=2), questions, ks=(1, 2)
    )

    # Question a : la preuve est au rang 1 → P@1 = 1, P@2 = 1/2, R@1 = 1, RR = 1
    assert evaluation.mean_precision(1) == 1.0
    assert evaluation.mean_precision(2) == pytest.approx(0.5)
    assert evaluation.mean_recall(1) == 1.0
    assert evaluation.mrr() == 1.0

    # Question b : seul son meilleur score est relevé, à part
    assert len(evaluation.top_scores(answerable=False)) == 1
    assert len(evaluation.top_scores(answerable=True)) == 1
