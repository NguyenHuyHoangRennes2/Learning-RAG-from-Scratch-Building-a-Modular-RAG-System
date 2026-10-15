"""Tests des métriques de recherche, avec les exemples chiffrés du document 03_evaluation_rag.pdf."""

# pytest fournit pytest.approx et pytest.raises
import pytest

# Ce que l'on teste
from app.evaluation.metrics import (
    contains_evidence,
    mean,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)

# Une preuve et des chunks dont on sait s'ils la contiennent
PROOF = "la réponse est 42"
RELEVANT = "Après calcul, la réponse   est 42."
IRRELEVANT = "Ce passage parle d'autre chose."


def test_evidence_matching_ignores_case_and_spacing() -> None:
    # Majuscules et espaces multiples ne doivent pas empêcher la correspondance
    assert contains_evidence("LA RÉPONSE\nest 42", [PROOF])

    # Un passage sans la preuve n'est pas pertinent
    assert not contains_evidence(IRRELEVANT, [PROOF])


def test_precision_example_from_the_corpus() -> None:
    # « Si deux des cinq passages retournés sont pertinents, Precision@5 = 2/5 = 0,40 »
    retrieved = [RELEVANT, IRRELEVANT, RELEVANT, IRRELEVANT, IRRELEVANT]

    # 2 pertinents sur 5
    assert precision_at_k(retrieved, [PROOF], k=5) == pytest.approx(0.40)


def test_precision_counts_missing_results_as_irrelevant() -> None:
    # Un seul résultat (pertinent) alors que K = 3
    assert precision_at_k([RELEVANT], [PROOF], k=3) == pytest.approx(1 / 3)


def test_recall_example_from_the_corpus() -> None:
    # « Si quatre passages pertinents existent et que deux sont récupérés, Recall = 2/4 = 0,50 »
    proofs = ["preuve un", "preuve deux", "preuve trois", "preuve quatre"]
    retrieved = ["ici preuve un", "là preuve trois", IRRELEVANT]

    # 2 preuves trouvées sur 4
    assert recall_at_k(retrieved, proofs, k=5) == pytest.approx(0.50)


def test_recall_only_looks_at_the_first_k_results() -> None:
    # La preuve n'apparaît qu'au rang 3
    retrieved = [IRRELEVANT, IRRELEVANT, RELEVANT]

    # Avec K = 2 elle n'est pas comptée ; avec K = 3 elle l'est
    assert recall_at_k(retrieved, [PROOF], k=2) == 0.0
    assert recall_at_k(retrieved, [PROOF], k=3) == 1.0


def test_reciprocal_rank_example_from_the_corpus() -> None:
    # « Si le premier passage pertinent apparaît au rang 2, le reciprocal rank vaut 0,5 »
    assert reciprocal_rank([IRRELEVANT, RELEVANT], [PROOF]) == pytest.approx(0.5)

    # Aucun pertinent : 0
    assert reciprocal_rank([IRRELEVANT], [PROOF]) == 0.0


def test_mrr_example_from_the_corpus() -> None:
    # « Rangs 1, 2 et 4 : MRR = (1 + 0,5 + 0,25)/3 = 0,5833 environ »
    ranks = [
        reciprocal_rank([RELEVANT], [PROOF]),
        reciprocal_rank([IRRELEVANT, RELEVANT], [PROOF]),
        reciprocal_rank([IRRELEVANT, IRRELEVANT, IRRELEVANT, RELEVANT], [PROOF]),
    ]

    # Moyenne des trois reciprocal ranks
    assert mean(ranks) == pytest.approx(0.5833, abs=1e-4)


def test_undefined_cases_are_rejected() -> None:
    # Recall sans preuve (question sans réponse) : non défini
    with pytest.raises(ValueError, match="preuve"):
        # Tentative invalide
        recall_at_k([RELEVANT], [], k=3)

    # K nul
    with pytest.raises(ValueError, match="k"):
        # Tentative invalide
        precision_at_k([RELEVANT], [PROOF], k=0)

    # Moyenne d'une liste vide
    with pytest.raises(ValueError, match="vide"):
        # Tentative invalide
        mean([])
