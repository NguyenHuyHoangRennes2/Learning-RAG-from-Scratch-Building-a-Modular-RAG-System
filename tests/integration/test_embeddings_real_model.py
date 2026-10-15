"""Tests d'intégration avec le VRAI modèle d'embeddings (lents : marqués "slow").

Lancer avec : python -m pytest -m slow -v
Le modèle est téléchargé depuis Hugging Face au premier lancement (environ 470 Mo).
"""

# math.isclose compare deux nombres à virgule avec une tolérance
import math

# pytest fournit les fixtures et les marqueurs
import pytest

# La configuration donne le nom du modèle
from app.core.config import get_settings

# Ce que l'on teste
from app.embeddings.embedding_model import EmbeddingModel, cosine_similarity

# Tous les tests de ce fichier sont lents (exclus par défaut, voir pytest.ini)
pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def model() -> EmbeddingModel:
    """Un seul chargement du modèle pour tout le fichier (scope="module")."""
    # Lit le nom du modèle dans la configuration
    settings = get_settings()

    # Crée le modèle (il sera chargé au premier usage)
    return EmbeddingModel(settings.embedding_model_name, device="cpu")


def test_vectors_have_the_documented_dimension_and_unit_norm(
    model: EmbeddingModel,
) -> None:
    # Vectorise un passage
    vector = model.embed_documents(["Le RAG associe recherche et génération."])[0]

    # multilingual-e5-small produit des vecteurs de 384 composantes
    assert len(vector) == model.dimension == 384

    # Le vecteur est normalisé : sa norme vaut 1
    assert math.isclose(math.sqrt(sum(x * x for x in vector)), 1.0, abs_tol=1e-4)


def test_question_is_closer_to_the_relevant_passage(model: EmbeddingModel) -> None:
    # Un passage qui répond à la question, et un passage hors sujet
    relevant, unrelated = model.embed_documents(
        [
            "La similarité cosinus mesure l'angle entre deux vecteurs d'embeddings.",
            "La recette de la tarte aux pommes demande du beurre et de la farine.",
        ]
    )

    # Vectorise la question
    question = model.embed_query("Comment compare-t-on deux embeddings ?")

    # Le passage pertinent est plus proche de la question que le passage hors sujet
    assert cosine_similarity(question, relevant) > cosine_similarity(
        question, unrelated
    )
