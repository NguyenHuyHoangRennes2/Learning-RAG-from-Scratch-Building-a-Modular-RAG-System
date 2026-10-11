"""Tests unitaires des structures de données (app/models.py)."""

# FrozenInstanceError est levée quand on modifie un objet frozen ; replace crée une copie modifiée
from dataclasses import FrozenInstanceError, replace

# pytest fournit pytest.raises pour vérifier qu'une erreur est bien levée
import pytest

# La classe que l'on teste
from app.models import DocumentPage


def make_page(**overrides: object) -> DocumentPage:
    """Crée une page valide ; overrides permet de changer un seul champ par test."""
    # Valeurs par défaut valides pour tous les champs
    values: dict[str, object] = {
        "document_id": "abc123",
        "source": "cours.pdf",
        "page_number": 1,
        "text": "Bonjour",
    }

    # Remplace les champs demandés par le test (ex. page_number=0)
    values.update(overrides)

    # Construit l'objet à partir du dictionnaire (** déplie les clés en arguments nommés)
    return DocumentPage(**values)  # type: ignore[arg-type]


def test_valid_page_keeps_its_values() -> None:
    # Crée une page avec les valeurs par défaut
    page = make_page()

    # Vérifie que chaque champ contient bien la valeur donnée
    assert page.document_id == "abc123"
    assert page.source == "cours.pdf"
    assert page.page_number == 1
    assert page.text == "Bonjour"


def test_page_number_zero_is_rejected() -> None:
    # La création d'une page numéro 0 doit lever une ValueError
    with pytest.raises(ValueError, match="page_number"):
        # Tentative de création invalide
        make_page(page_number=0)


def test_empty_document_id_is_rejected() -> None:
    # Un identifiant vide doit lever une ValueError
    with pytest.raises(ValueError, match="document_id"):
        # Tentative de création invalide
        make_page(document_id="")


def test_empty_source_is_rejected() -> None:
    # Une source vide doit lever une ValueError
    with pytest.raises(ValueError, match="source"):
        # Tentative de création invalide
        make_page(source="")


def test_page_is_immutable() -> None:
    # Crée une page valide
    page = make_page()

    # Modifier un champ d'un objet frozen doit lever FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        # Tentative de modification interdite
        page.text = "autre texte"  # type: ignore[misc]


def test_replace_creates_a_modified_copy() -> None:
    # Crée la page d'origine
    original = make_page(text="  texte brut  ")

    # replace() crée une NOUVELLE page avec un champ modifié (c'est ainsi qu'on « nettoiera »)
    cleaned = replace(original, text="texte brut")

    # La copie contient le nouveau texte
    assert cleaned.text == "texte brut"

    # L'original n'a pas changé
    assert original.text == "  texte brut  "

    # Les autres champs sont conservés à l'identique
    assert cleaned.page_number == original.page_number
