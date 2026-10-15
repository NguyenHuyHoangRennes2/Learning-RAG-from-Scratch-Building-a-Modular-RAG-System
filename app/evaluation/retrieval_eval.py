"""Évaluation de la recherche sur le jeu de questions de référence.

Pour chaque question AVEC réponse : Precision@K, Recall@K et reciprocal rank.
Pour chaque question SANS réponse : seul le meilleur score est relevé, afin de
voir si un seuil peut distinguer « le corpus répond » de « le corpus ne répond pas ».
"""

# Sequence : liste de valeurs de K
from collections.abc import Sequence

# dataclass pour les résultats
from dataclasses import dataclass, field

# Questions de référence
from app.evaluation.dataset import EvalQuestion

# Métriques de recherche
from app.evaluation.metrics import mean, precision_at_k, recall_at_k, reciprocal_rank

# Le composant évalué
from app.retrieval.retriever import Retriever


@dataclass(frozen=True)
class QuestionResult:
    """Mesures pour une question."""

    # Identifiant de la question
    question_id: str

    # Catégorie (facile, paraphrase...)
    category: str

    # Score du meilleur chunk (0.0 si aucun résultat)
    top_score: float

    # Precision@K et Recall@K pour chaque K évalué (vides pour une question sans réponse)
    precision: dict[int, float] = field(default_factory=dict)
    recall: dict[int, float] = field(default_factory=dict)

    # Reciprocal rank (None pour une question sans réponse)
    reciprocal_rank: float | None = None


@dataclass(frozen=True)
class RetrievalEvaluation:
    """Résultats agrégés sur tout le jeu de questions."""

    # Valeurs de K évaluées, ex. (3, 5)
    ks: tuple[int, ...]

    # Détail question par question
    per_question: list[QuestionResult]

    def _answerable(self) -> list[QuestionResult]:
        """Résultats des questions qui ont une réponse dans le corpus."""
        # Ce sont celles qui ont un reciprocal rank
        return [r for r in self.per_question if r.reciprocal_rank is not None]

    def mean_precision(self, k: int) -> float:
        """Precision@K moyenne sur les questions avec réponse."""
        # Moyenne des précisions
        return mean([r.precision[k] for r in self._answerable()])

    def mean_recall(self, k: int, category: str | None = None) -> float:
        """Recall@K moyen, éventuellement restreint à une catégorie."""
        # Filtre éventuel par catégorie
        results = [r for r in self._answerable() if category in (None, r.category)]

        # Moyenne des rappels
        return mean([r.recall[k] for r in results])

    def mrr(self) -> float:
        """Mean Reciprocal Rank sur les questions avec réponse."""
        # Moyenne des reciprocal ranks (jamais None ici)
        return mean([r.reciprocal_rank or 0.0 for r in self._answerable()])

    def top_scores(self, answerable: bool) -> list[float]:
        """Meilleurs scores des questions avec (True) ou sans (False) réponse."""
        # Une question sans réponse n'a pas de reciprocal rank
        return [
            r.top_score
            for r in self.per_question
            if (r.reciprocal_rank is not None) == answerable
        ]


def evaluate_retrieval(
    retriever: Retriever,
    questions: Sequence[EvalQuestion],
    ks: Sequence[int] = (3, 5),
) -> RetrievalEvaluation:
    """Pose chaque question au retriever et calcule les métriques."""
    # On récupère une seule fois le plus grand K : les K plus petits en sont des préfixes
    max_k = max(ks)

    # Résultats question par question
    per_question: list[QuestionResult] = []

    # Évalue chaque question
    for question in questions:
        # Chunks retrouvés, du plus au moins similaire
        results = retriever.retrieve(question.question, top_k=max_k)

        # Leurs textes (les métriques ne regardent que le texte)
        texts = [result.chunk.text for result in results]

        # Meilleur score (0.0 si la base est vide)
        top_score = results[0].score if results else 0.0

        # Question sans réponse : on ne garde que le meilleur score
        if not question.answerable:
            # Pas de précision, rappel ni RR
            per_question.append(
                QuestionResult(question.id, question.category, top_score)
            )
            continue

        # Question avec réponse : toutes les métriques
        per_question.append(
            QuestionResult(
                question_id=question.id,
                category=question.category,
                top_score=top_score,
                precision={k: precision_at_k(texts, question.evidence, k) for k in ks},
                recall={k: recall_at_k(texts, question.evidence, k) for k in ks},
                reciprocal_rank=reciprocal_rank(texts, question.evidence),
            )
        )

    # Regroupe le tout
    return RetrievalEvaluation(tuple(ks), per_question)
