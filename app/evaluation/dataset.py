"""Chargement et vérification du jeu de questions de référence (evaluation/questions.json)."""

# json pour lire le fichier de questions
import json

# dataclass pour représenter une question
from dataclasses import dataclass

# Path représente un chemin de fichier
from pathlib import Path

# Le chemin par défaut est relatif à la racine du projet
from app.core.config import PROJECT_ROOT

# Pour vérifier que chaque preuve existe vraiment dans le corpus
from app.evaluation.metrics import normalize

# Fichier de questions versionné dans Git
DEFAULT_QUESTIONS_PATH = PROJECT_ROOT / "evaluation" / "questions.json"


@dataclass(frozen=True)
class EvalQuestion:
    """Une question de référence."""

    # Identifiant court, ex. "q01"
    id: str

    # "facile", "paraphrase", "multi-documents" ou "sans-réponse"
    category: str

    # La question posée au système
    question: str

    # Extraits exacts du corpus qui contiennent la réponse (vide si sans réponse)
    evidence: tuple[str, ...]

    # Mots attendus dans une bonne réponse du LLM (Phase 11)
    expected_keywords: tuple[str, ...]

    @property
    def answerable(self) -> bool:
        """Vrai si le corpus contient la réponse (au moins une preuve)."""
        # Une question sans preuve est une question « sans réponse »
        return bool(self.evidence)


def load_questions(path: Path = DEFAULT_QUESTIONS_PATH) -> list[EvalQuestion]:
    """Lit le fichier JSON et renvoie les questions."""
    # Lit et décode le fichier (UTF-8 : il contient des accents)
    data = json.loads(path.read_text(encoding="utf-8"))

    # Convertit chaque entrée en EvalQuestion (les listes deviennent des tuples immuables)
    return [
        EvalQuestion(
            id=item["id"],
            category=item["category"],
            question=item["question"],
            evidence=tuple(item["evidence"]),
            expected_keywords=tuple(item["expected_keywords"]),
        )
        for item in data["questions"]
    ]


def find_missing_evidence(
    questions: list[EvalQuestion], corpus_texts: list[str]
) -> list[str]:
    """Renvoie les preuves introuvables dans le corpus (une faute de frappe fausserait l'évaluation)."""
    # Tout le corpus normalisé, pages séparées par un espace
    corpus = normalize(" ".join(corpus_texts))

    # Preuves absentes, préfixées par l'id de leur question
    return [
        f"{question.id}: {proof}"
        for question in questions
        for proof in question.evidence
        if normalize(proof) not in corpus
    ]
