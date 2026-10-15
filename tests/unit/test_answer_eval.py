"""Tests des métriques de réponse et de la référence extractive."""

# pytest fournit pytest.approx
import pytest

# Ce que l'on teste
from app.evaluation.answer_eval import (
    citation_precision,
    evaluate_answer,
    keyword_coverage,
    lexical_faithfulness,
    summarize_answers,
)
from app.evaluation.baselines import ExtractiveBaseline
from app.evaluation.dataset import EvalQuestion
from app.generation.prompts import NO_ANSWER_MESSAGE, build_user_prompt
from app.models import Chunk, RAGAnswer, SearchResult

# Deux sources : la 1re contient la preuve, la 2nde non
SOURCES = (
    SearchResult(
        Chunk("d", "a.pdf", 1, 0, "Le reranking ajoute de la latence au système."), 0.9
    ),
    SearchResult(
        Chunk("d", "b.pdf", 2, 0, "La tarte aux pommes demande du beurre."), 0.5
    ),
)

# Question avec réponse : preuve dans la source 1, mot-clé attendu « latence »
QUESTION = EvalQuestion(
    "q", "paraphrase", "Coût du reranking ?", ("ajoute de la latence",), ("latence",)
)

# Question sans réponse
NO_ANSWER_QUESTION = EvalQuestion("n", "sans-réponse", "Capitale ?", (), ())


def make_answer(
    text: str, cited: tuple[int, ...], abstained: bool = False
) -> RAGAnswer:
    """Réponse factice construite sur les deux sources."""
    # Latences arbitraires
    return RAGAnswer(
        "?", text, SOURCES, cited, abstained, retrieval_ms=10.0, generation_ms=100.0
    )


def test_keyword_coverage() -> None:
    # 1 mot-clé sur 2 présent, insensible à la casse
    assert keyword_coverage("Il ajoute de la LATENCE.", ["latence", "précision"]) == 0.5

    # Pas de mot-clé défini : non applicable
    assert keyword_coverage("peu importe", []) is None


def test_citation_precision() -> None:
    # Cite la bonne source puis la mauvaise : 1 citation correcte sur 2
    assert citation_precision(make_answer("x [1][2]", (1, 2)), QUESTION.evidence) == 0.5

    # Aucune citation : non applicable
    assert citation_precision(make_answer("x", ()), QUESTION.evidence) is None


def test_lexical_faithfulness_spots_invented_sentences() -> None:
    # Phrase 1 reprise des sources ; phrase 2 inventée (mots absents des sources)
    answer = make_answer(
        "Le reranking ajoute de la latence [1]. Il fonctionne grâce aux ordinateurs quantiques.",
        (1,),
    )

    # Une phrase soutenue sur deux
    assert lexical_faithfulness(answer) == pytest.approx(0.5)

    # Une abstention n'a rien à vérifier
    assert (
        lexical_faithfulness(make_answer(NO_ANSWER_MESSAGE, (), abstained=True)) is None
    )


def test_abstention_correctness() -> None:
    # Répondre à une question avec réponse : correct
    assert evaluate_answer(
        QUESTION, make_answer("latence [1]", (1,))
    ).abstention_correct

    # S'abstenir sur une question sans réponse : correct
    abstention = make_answer(NO_ANSWER_MESSAGE, (), abstained=True)
    assert evaluate_answer(NO_ANSWER_QUESTION, abstention).abstention_correct

    # Répondre à une question sans réponse : FAUX (risque d'invention)
    assert not evaluate_answer(
        NO_ANSWER_QUESTION, make_answer("Canberra.", ())
    ).abstention_correct


def test_summary_aggregates_only_applicable_values() -> None:
    # Une bonne réponse et une abstention correcte
    results = [
        evaluate_answer(QUESTION, make_answer("Il ajoute de la latence [1].", (1,))),
        evaluate_answer(
            NO_ANSWER_QUESTION, make_answer(NO_ANSWER_MESSAGE, (), abstained=True)
        ),
    ]
    summary = summarize_answers(results)

    # Tout est correct ; les métriques de contenu ne portent que sur la question avec réponse
    assert summary["abstention_accuracy"] == 1.0
    assert summary["abstained_when_unanswerable"] == 1.0
    assert summary["keyword_coverage"] == 1.0
    assert summary["citation_precision"] == 1.0
    assert summary["retrieval_ms_mean"] == 10.0


def test_extractive_baseline_copies_and_cites_the_first_source() -> None:
    # Prompt réel construit avec les deux sources
    prompt = build_user_prompt("Coût du reranking ?", list(SOURCES))

    # La référence recopie la source [1] et la cite
    assert ExtractiveBaseline().generate("consignes", prompt) == (
        "Le reranking ajoute de la latence au système. [1]"
    )
