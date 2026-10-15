"""Évaluation des RÉPONSES du RAG (génération), séparée de l'évaluation de la recherche.

Métriques calculées pour chaque question (règle 6.7 de CLAUDE.md) :

    - abstention correcte : le système répond quand le corpus contient la réponse,
      et s'abstient quand il ne la contient pas ;
    - couverture des mots-clés (indicateur de pertinence de la réponse) :
      part des mots-clés attendus présents dans la réponse ;
    - exactitude des citations : part des sources citées qui contiennent une preuve ;
    - fidélité approximative (heuristique LEXICALE, pas un juge LLM) : part des phrases
      de la réponse dont la plupart des mots porteurs de sens figurent dans les sources ;
    - latence : recherche et génération.

Ces indicateurs automatiques sont simples et reproductibles, mais imparfaits : une
réponse correcte peut employer d'autres mots que ceux attendus. Ils complètent, sans
la remplacer, une relecture humaine.
"""

# re : découpage en phrases et en mots
import re

# Sequence : liste de questions
from collections.abc import Sequence

# dataclass pour les résultats
from dataclasses import dataclass

# Questions de référence
from app.evaluation.dataset import EvalQuestion

# Même définition de la pertinence que pour la recherche (preuves)
from app.evaluation.metrics import contains_evidence, mean, normalize

# Structure de réponse du pipeline
from app.models import RAGAnswer

# Citation [n] à retirer avant d'analyser le texte
CITATION = re.compile(r"\[\d+\]")

# Fin de phrase (point, ! ou ? suivi d'espaces)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")

# Mot : suite de lettres (accents compris) ou de chiffres
WORD = re.compile(r"[\wÀ-ÿ]+")

# Un mot « porteur de sens » fait au moins 4 caractères (on ignore le, de, est, une...)
MIN_CONTENT_WORD_LENGTH = 4

# Une phrase est jugée « soutenue » si au moins 60 % de ses mots porteurs sont dans les sources
SUPPORT_THRESHOLD = 0.6


def keyword_coverage(answer: str, keywords: Sequence[str]) -> float | None:
    """Part des mots-clés attendus présents dans la réponse (None s'il n'y en a pas)."""
    # Pas de mot-clé défini pour cette question : métrique non applicable
    if not keywords:
        # Non applicable
        return None

    # Réponse normalisée (minuscules, espaces simples)
    text = normalize(answer)

    # Part des mots-clés retrouvés
    return sum(normalize(keyword) in text for keyword in keywords) / len(keywords)


def citation_precision(result: RAGAnswer, evidence: Sequence[str]) -> float | None:
    """Part des sources citées qui contiennent une preuve (None si rien n'est cité)."""
    # Aucune citation : métrique non applicable (compté à part)
    if not result.cited:
        # Non applicable
        return None

    # Sources citées contenant au moins une preuve
    correct = sum(
        contains_evidence(s.chunk.text, evidence) for s in result.cited_sources
    )

    # Proportion de citations correctes
    return correct / len(result.cited)


def lexical_faithfulness(result: RAGAnswer) -> float | None:
    """Part des phrases de la réponse « soutenues » par le texte des sources (heuristique).

    Une phrase est soutenue si au moins 60 % de ses mots de 4 lettres ou plus
    apparaissent dans les sources fournies. Cette heuristique repère les phrases
    INVENTÉES de toutes pièces, mais pas une négation ou une inversion de sens.
    """
    # Sans source ou en cas d'abstention, il n'y a rien à vérifier
    if not result.sources or result.abstained:
        # Non applicable
        return None

    # Vocabulaire de toutes les sources fournies au LLM
    source_words = set(
        WORD.findall(normalize(" ".join(s.chunk.text for s in result.sources)))
    )

    # Phrases de la réponse, sans les citations [n]
    sentences = [
        s for s in SENTENCE_END.split(CITATION.sub("", result.answer)) if s.strip()
    ]

    # Nombre de phrases soutenues
    supported = 0

    # Analyse chaque phrase
    for sentence in sentences:
        # Mots porteurs de sens de la phrase
        words = [
            w
            for w in WORD.findall(normalize(sentence))
            if len(w) >= MIN_CONTENT_WORD_LENGTH
        ]

        # Phrase sans mot porteur (ex. « Oui. ») : considérée comme soutenue
        if not words:
            # Rien à vérifier
            supported += 1
            continue

        # Part des mots présents dans les sources
        if sum(w in source_words for w in words) / len(words) >= SUPPORT_THRESHOLD:
            # Phrase soutenue
            supported += 1

    # Proportion de phrases soutenues (None si la réponse est vide)
    return supported / len(sentences) if sentences else None


@dataclass(frozen=True)
class AnswerResult:
    """Mesures pour une question."""

    question_id: str
    category: str
    answerable: bool
    abstained: bool
    keyword_coverage: float | None
    citation_precision: float | None
    faithfulness: float | None
    retrieval_ms: float
    generation_ms: float

    @property
    def abstention_correct(self) -> bool:
        """Vrai si le système répond quand il le faut et s'abstient quand il le faut."""
        # Il faut s'abstenir exactement quand le corpus ne contient pas la réponse
        return self.abstained != self.answerable


def evaluate_answer(question: EvalQuestion, result: RAGAnswer) -> AnswerResult:
    """Calcule toutes les métriques d'une réponse."""
    # Les métriques de contenu n'ont de sens que pour une vraie réponse à une question avec réponse
    scored = question.answerable and not result.abstained

    # Regroupe les mesures
    return AnswerResult(
        question_id=question.id,
        category=question.category,
        answerable=question.answerable,
        abstained=result.abstained,
        keyword_coverage=keyword_coverage(result.answer, question.expected_keywords)
        if scored
        else None,
        citation_precision=citation_precision(result, question.evidence)
        if scored
        else None,
        faithfulness=lexical_faithfulness(result),
        retrieval_ms=result.retrieval_ms,
        generation_ms=result.generation_ms,
    )


def summarize_answers(results: Sequence[AnswerResult]) -> dict[str, float | None]:
    """Agrège les résultats ; une métrique sans aucune valeur applicable vaut None."""

    def mean_or_none(values: list[float | None]) -> float | None:
        # Moyenne des seules valeurs applicables
        present = [v for v in values if v is not None]
        return mean(present) if present else None

    # Questions avec et sans réponse
    answerable = [r for r in results if r.answerable]
    unanswerable = [r for r in results if not r.answerable]

    # Indicateurs agrégés
    return {
        "abstention_accuracy": mean([float(r.abstention_correct) for r in results]),
        "answered_when_answerable": mean_or_none(
            [float(not r.abstained) for r in answerable]
        ),
        "abstained_when_unanswerable": mean_or_none(
            [float(r.abstained) for r in unanswerable]
        ),
        "keyword_coverage": mean_or_none([r.keyword_coverage for r in results]),
        "citation_precision": mean_or_none([r.citation_precision for r in results]),
        "answers_without_citation": mean_or_none(
            [float(r.citation_precision is None) for r in answerable if not r.abstained]
        ),
        "faithfulness_lexical": mean_or_none([r.faithfulness for r in results]),
        "retrieval_ms_mean": mean([r.retrieval_ms for r in results]),
        "generation_ms_mean": mean([r.generation_ms for r in results]),
    }
