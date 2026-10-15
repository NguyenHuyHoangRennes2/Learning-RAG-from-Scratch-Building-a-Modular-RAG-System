"""Tests unitaires des structures de données (app/models.py)."""

# FrozenInstanceError est levée quand on modifie un objet frozen ; replace crée une copie modifiée
from dataclasses import FrozenInstanceError, replace

# pytest fournit pytest.raises pour vérifier qu'une erreur est bien levée
import pytest

# Les classes que l'on teste
from app.models import Chunk, DocumentPage, SearchResult


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


# --- Chunk ---


def make_chunk(**overrides: object) -> Chunk:
    """Crée un chunk valide ; overrides permet de changer un seul champ par test."""
    # Valeurs par défaut valides pour tous les champs
    values: dict[str, object] = {
        "document_id": "abc123",
        "source": "cours.pdf",
        "page_number": 2,
        "chunk_index": 0,
        "text": "Le RAG associe recherche et génération.",
    }

    # Remplace les champs demandés par le test
    values.update(overrides)

    # Construit l'objet à partir du dictionnaire
    return Chunk(**values)  # type: ignore[arg-type]


def test_chunk_id_combines_document_page_and_index() -> None:
    # Crée le 4e chunk (index 3) de la page 2
    chunk = make_chunk(chunk_index=3)

    # L'identifiant suit le format "<document_id>-p<page>-c<index>"
    assert chunk.chunk_id == "abc123-p2-c3"


def test_chunk_id_is_stable() -> None:
    # Deux chunks créés avec les mêmes valeurs ont le même identifiant
    assert make_chunk().chunk_id == make_chunk().chunk_id


def test_negative_chunk_index_is_rejected() -> None:
    # Un index négatif doit lever une ValueError
    with pytest.raises(ValueError, match="chunk_index"):
        # Tentative de création invalide
        make_chunk(chunk_index=-1)


def test_blank_chunk_text_is_rejected() -> None:
    # Un texte fait uniquement d'espaces doit lever une ValueError
    with pytest.raises(ValueError, match="text"):
        # Tentative de création invalide
        make_chunk(text="   \n ")


def test_chunk_shares_origin_validation_with_page() -> None:
    # La règle commune page_number >= 1 s'applique aussi aux chunks
    with pytest.raises(ValueError, match="page_number"):
        # Tentative de création invalide
        make_chunk(page_number=0)


def test_chunk_is_immutable() -> None:
    # Crée un chunk valide
    chunk = make_chunk()

    # Modifier un champ d'un objet frozen doit lever FrozenInstanceError
    with pytest.raises(FrozenInstanceError):
        # Tentative de modification interdite
        chunk.text = "autre texte"  # type: ignore[misc]


def test_chunk_citation_is_human_readable() -> None:
    # Chunk de la page 2 de "cours.pdf"
    chunk = make_chunk()

    # Citation lisible : nom du fichier et numéro de page
    assert chunk.citation == "cours.pdf, p. 2"


# --- SearchResult ---


def test_search_result_holds_chunk_and_score() -> None:
    # Un résultat de recherche associe un chunk et son score
    result = SearchResult(chunk=make_chunk(), score=0.87)

    # Les deux informations sont accessibles
    assert (result.chunk.chunk_id, result.score) == ("abc123-p2-c0", 0.87)
