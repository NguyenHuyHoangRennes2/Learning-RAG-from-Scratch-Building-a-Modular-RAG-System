"""Métriques d'évaluation de la RECHERCHE (retrieval), indépendantes du LLM.

Définition de la pertinence utilisée dans ce projet
----------------------------------------------------
Chaque question de référence liste des « preuves » : de courts extraits exacts du
corpus qui contiennent la réponse. Un chunk retrouvé est PERTINENT s'il contient
au moins une preuve. Cette définition ne dépend pas du découpage : elle permet de
comparer équitablement plusieurs stratégies de chunking (une preuve coupée en deux
par une frontière de chunk n'est plus trouvée : c'est une vraie perte d'information).

Métriques (K = nombre de chunks retrouvés) :
    - Precision@K = (chunks pertinents parmi les K) / K
    - Recall@K    = (preuves trouvées dans les K chunks) / (nombre de preuves)
    - RR          = 1 / rang du premier chunk pertinent (0 si aucun) ; MRR = moyenne des RR
"""

# re : réduction des espaces multiples pour comparer les textes
import re

# Sequence : toute liste ou tuple de valeurs
from collections.abc import Sequence

# Suite d'espaces (espaces, sauts de ligne...) à réduire à un seul espace
WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Forme comparable d'un texte : minuscules et espaces simples."""
    # Les sauts de ligne du chunk et les espaces de la preuve ne doivent pas empêcher la correspondance
    return WHITESPACE.sub(" ", text).strip().lower()


def contains_evidence(chunk_text: str, evidence: Sequence[str]) -> bool:
    """Indique si le chunk contient au moins une des preuves."""
    # Texte du chunk normalisé une seule fois
    haystack = normalize(chunk_text)

    # Pertinent dès qu'une preuve est incluse dans le chunk
    return any(normalize(proof) in haystack for proof in evidence)


def precision_at_k(
    retrieved_texts: Sequence[str], evidence: Sequence[str], k: int
) -> float:
    """Proportion de chunks pertinents parmi les K premiers.

    Exemple : 2 pertinents sur 5 → Precision@5 = 2/5 = 0,40.
    """
    # K doit être positif
    if k <= 0:
        # Erreur explicite
        raise ValueError(f"k doit être > 0 (reçu : {k})")

    # Nombre de chunks pertinents parmi les K premiers
    relevant = sum(contains_evidence(text, evidence) for text in retrieved_texts[:k])

    # On divise par K (et non par le nombre de résultats) : un résultat manquant compte comme non pertinent
    return relevant / k


def recall_at_k(
    retrieved_texts: Sequence[str], evidence: Sequence[str], k: int
) -> float:
    """Proportion des preuves retrouvées dans les K premiers chunks.

    Exemple : 4 preuves, 2 retrouvées → Recall@K = 2/4 = 0,50.
    """
    # Sans preuve, le rappel n'est pas défini (question sans réponse dans le corpus)
    if not evidence:
        # Erreur explicite : ces questions doivent être exclues du calcul
        raise ValueError("recall_at_k n'est pas défini sans preuve de référence")

    # Les K premiers chunks, normalisés
    top_texts = [normalize(text) for text in retrieved_texts[:k]]

    # Nombre de preuves présentes dans au moins un des K chunks
    found = sum(
        any(normalize(proof) in text for text in top_texts) for proof in evidence
    )

    # Proportion de preuves retrouvées
    return found / len(evidence)


def reciprocal_rank(retrieved_texts: Sequence[str], evidence: Sequence[str]) -> float:
    """1 / rang du premier chunk pertinent (rang compté à partir de 1), 0 si aucun.

    Exemple : premier pertinent au rang 2 → RR = 1/2 = 0,5.
    """
    # Parcourt les résultats dans l'ordre, rang 1 d'abord
    for rank, text in enumerate(retrieved_texts, start=1):
        # Premier chunk pertinent trouvé
        if contains_evidence(text, evidence):
            # Plus il arrive tôt, plus le score est élevé
            return 1.0 / rank

    # Aucun chunk pertinent
    return 0.0


def mean(values: Sequence[float]) -> float:
    """Moyenne arithmétique (ex. MRR = moyenne des reciprocal ranks)."""
    # La moyenne d'une liste vide n'est pas définie
    if not values:
        # Erreur explicite
        raise ValueError("moyenne d'une liste vide")

    # Somme divisée par le nombre de valeurs
    return sum(values) / len(values)
