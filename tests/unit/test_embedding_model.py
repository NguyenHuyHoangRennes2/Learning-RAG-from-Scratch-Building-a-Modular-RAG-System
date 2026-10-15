"""Tests unitaires du module d'embeddings, SANS télécharger de vrai modèle."""

# math.isclose compare deux nombres à virgule avec une tolérance
import math

# Any : type des arguments nommés reçus par le faux encodeur
from typing import Any

# pytest fournit pytest.raises et pytest.approx
import pytest

# Ce que l'on teste
from app.embeddings.embedding_model import (
    EmbeddingModel,
    cosine_similarity,
    prefixes_for_model,
)


class FakeEncoder:
    """Faux encodeur : mémorise ce qu'il reçoit et renvoie des vecteurs prévisibles."""

    def __init__(self) -> None:
        # Historique des appels : (textes, arguments nommés)
        self.calls: list[tuple[list[str], dict[str, Any]]] = []

    def encode(self, sentences: list[str], **kwargs: Any) -> list[list[float]]:
        # Mémorise l'appel pour que le test puisse le vérifier
        self.calls.append((sentences, kwargs))

        # Vecteur [longueur du texte, 1.0] : différent pour chaque texte, facile à prévoir
        return [[float(len(sentence)), 1.0] for sentence in sentences]

    def get_embedding_dimension(self) -> int:
        # Nos faux vecteurs ont 2 composantes
        return 2


def make_model(
    model_name: str = "intfloat/multilingual-e5-small",
) -> tuple[EmbeddingModel, FakeEncoder]:
    """Crée un EmbeddingModel branché sur un faux encodeur."""
    # Faux encodeur injecté : aucun téléchargement, test instantané
    encoder = FakeEncoder()

    # Renvoie le modèle et l'encodeur (pour inspecter ses appels)
    return EmbeddingModel(model_name, batch_size=8, encoder=encoder), encoder


# --- cosine_similarity : exemple numérique des notes ---


def test_cosine_similarity_worked_example() -> None:
    # a = (1, 2, 2), b = (2, 1, 2) : a·b = 2 + 2 + 4 = 8 ; ‖a‖ = ‖b‖ = 3 ; cos = 8 / 9
    assert cosine_similarity([1, 2, 2], [2, 1, 2]) == pytest.approx(8 / 9)


def test_cosine_similarity_extreme_values() -> None:
    # Même direction (b = 2a) : cos = 1, la longueur ne compte pas
    assert cosine_similarity([1, 0], [2, 0]) == pytest.approx(1.0)

    # Directions perpendiculaires : cos = 0 (aucun rapport)
    assert cosine_similarity([1, 0], [0, 3]) == pytest.approx(0.0)

    # Directions opposées : cos = -1
    assert cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)


def test_cosine_similarity_rejects_invalid_vectors() -> None:
    # Dimensions différentes
    with pytest.raises(ValueError, match="dimensions"):
        # Tentative invalide
        cosine_similarity([1, 0], [1, 0, 0])

    # Vecteur nul : pas de direction
    with pytest.raises(ValueError, match="nul"):
        # Tentative invalide
        cosine_similarity([0, 0], [1, 0])


# --- préfixes ---


def test_e5_models_use_query_and_passage_prefixes() -> None:
    # Les modèles E5 attendent "query: " et "passage: "
    assert prefixes_for_model("intfloat/multilingual-e5-small") == (
        "query: ",
        "passage: ",
    )


def test_other_models_use_no_prefix() -> None:
    # Les autres modèles n'utilisent pas de préfixe
    assert prefixes_for_model("paraphrase-multilingual-MiniLM-L12-v2") == ("", "")


# --- EmbeddingModel ---


def test_documents_are_prefixed_and_normalized() -> None:
    # Modèle E5 branché sur le faux encodeur
    model, encoder = make_model()

    # Vectorise deux passages
    vectors = model.embed_documents(["Le RAG.", "Les embeddings."])

    # Un vecteur par texte, dans le même ordre
    assert len(vectors) == 2

    # Le faux encodeur a reçu les textes AVEC le préfixe "passage: "
    texts, kwargs = encoder.calls[0]
    assert texts == ["passage: Le RAG.", "passage: Les embeddings."]

    # La normalisation est demandée, avec la taille de lot configurée
    assert kwargs["normalize_embeddings"] is True
    assert kwargs["batch_size"] == 8


def test_query_is_prefixed_and_returns_one_vector() -> None:
    # Modèle E5 branché sur le faux encodeur
    model, encoder = make_model()

    # Vectorise une question
    vector = model.embed_query("Qu'est-ce que le RAG ?")

    # Le texte encodé porte le préfixe "query: "
    assert encoder.calls[0][0] == ["query: Qu'est-ce que le RAG ?"]

    # Un seul vecteur : [longueur du texte préfixé, 1.0]
    assert vector == [float(len("query: Qu'est-ce que le RAG ?")), 1.0]


def test_empty_document_list_does_not_call_the_encoder() -> None:
    # Modèle branché sur le faux encodeur
    model, encoder = make_model()

    # Aucun texte : liste vide, et l'encodeur n'est jamais appelé
    assert model.embed_documents([]) == []
    assert encoder.calls == []


def test_blank_question_is_rejected() -> None:
    # Modèle branché sur le faux encodeur
    model, _ = make_model()

    # Une question vide doit lever une ValueError
    with pytest.raises(ValueError, match="question"):
        # Tentative invalide
        model.embed_query("   ")


def test_dimension_comes_from_the_encoder() -> None:
    # Le faux encodeur déclare 2 dimensions
    model, _ = make_model()

    # La propriété dimension renvoie la valeur du modèle
    assert model.dimension == 2


def test_vectors_are_plain_python_floats() -> None:
    # Modèle branché sur le faux encodeur
    model, _ = make_model()

    # Les vecteurs sont des listes de float Python (format accepté par ChromaDB et JSON)
    vector = model.embed_documents(["Texte."])[0]
    assert all(isinstance(value, float) for value in vector)

    # Sanity check : la première composante vaut la longueur de "passage: Texte."
    assert math.isclose(vector[0], len("passage: Texte."))
