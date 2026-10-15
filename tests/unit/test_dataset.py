"""Tests du chargement du jeu de questions de référence."""

# Path représente un chemin de fichier
from pathlib import Path

# Ce que l'on teste
from app.evaluation.dataset import EvalQuestion, find_missing_evidence, load_questions


def test_reference_questions_file_is_valid() -> None:
    # Charge le vrai fichier versionné evaluation/questions.json
    questions = load_questions()

    # 20 questions, identifiants uniques
    assert len(questions) == 20
    assert len({q.id for q in questions}) == 20

    # Les 4 catégories du protocole (document 3 du corpus) sont représentées
    assert {q.category for q in questions} == {
        "facile",
        "paraphrase",
        "multi-documents",
        "sans-réponse",
    }

    # Une question est « sans réponse » si et seulement si elle n'a pas de preuve
    assert all(q.answerable == (q.category != "sans-réponse") for q in questions)


def test_missing_evidence_is_detected(tmp_path: Path) -> None:
    # Une question dont la preuve contient une faute de frappe
    question = EvalQuestion("x1", "facile", "?", ("le RAG combine",), ())
    typo = EvalQuestion("x2", "facile", "?", ("le RAG conbine",), ())

    # Corpus minuscule
    corpus = ["Le   RAG combine recherche et génération."]

    # Seule la preuve mal orthographiée est signalée
    assert find_missing_evidence([question, typo], corpus) == ["x2: le RAG conbine"]
