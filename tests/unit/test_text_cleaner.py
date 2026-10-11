"""Tests unitaires du nettoyage de texte (app/ingestion/text_cleaner.py)."""

# logging pour vérifier le niveau des messages capturés
import logging

# pytest fournit caplog
import pytest

# Les fonctions testées
from app.ingestion.text_cleaner import (
    clean_pages,
    clean_text,
    join_wrapped_lines,
    normalize_unicode,
    remove_repeated_lines,
)

# La structure de données manipulée
from app.models import DocumentPage


def make_page(
    text: str, page_number: int = 1, document_id: str = "doc1"
) -> DocumentPage:
    """Crée une page de test avec un texte donné."""
    # Source fixe : seuls le texte, la page et le document varient selon les tests
    return DocumentPage(
        document_id=document_id, source="cours.pdf", page_number=page_number, text=text
    )


# --- normalize_unicode ---


def test_typographic_apostrophe_is_replaced() -> None:
    # L'apostrophe typographique (’) devient l'apostrophe simple (')
    assert normalize_unicode("d’informations") == "d'informations"


def test_ligature_is_decomposed() -> None:
    # La ligature "ﬁ" (un seul caractère) devient les deux lettres "fi"
    assert normalize_unicode("ﬁchier") == "fichier"


def test_non_breaking_space_becomes_normal_space() -> None:
    # L'espace insécable (U+00A0) devient un espace normal
    assert normalize_unicode("RAG :") == "RAG :"


# --- join_wrapped_lines ---


def test_layout_line_break_is_joined() -> None:
    # Le saut de ligne au milieu d'une phrase est remplacé par un espace
    text = "un système de recherche\nd'informations."
    assert join_wrapped_lines(text) == "un système de recherche d'informations."


def test_line_break_after_sentence_is_kept() -> None:
    # Après un point, le saut de ligne est un vrai changement de paragraphe : il est gardé
    assert (
        join_wrapped_lines("comme contexte.\nCette approche")
        == "comme contexte.\nCette approche"
    )


def test_heading_stays_on_its_own_line() -> None:
    # Le titre n'est collé ni au texte précédent (sans point final) ni au texte suivant
    text = (
        "fin du paragraphe sans point\n2. Les deux pipelines\nLe pipeline d'ingestion"
    )
    expected = (
        "fin du paragraphe sans point\n2. Les deux pipelines\nLe pipeline d'ingestion"
    )
    assert join_wrapped_lines(text) == expected


def test_extra_spaces_and_blank_lines_are_removed() -> None:
    # Espaces multiples réduits, lignes vides supprimées, lignes coupées recollées
    assert join_wrapped_lines("  un   texte  \n\n\n  coupé.  ") == "un texte coupé."


def test_whitespace_only_text_gives_empty_string() -> None:
    # Un texte fait uniquement d'espaces et de sauts de ligne devient vide
    assert clean_text("   \n \t \n") == ""


# --- remove_repeated_lines ---


def test_repeated_header_with_page_number_is_removed() -> None:
    # Deux pages avec le même en-tête et un numéro de page différent
    pages = [
        make_page("Corpus RAG\nPage 1\nContenu A.", page_number=1),
        make_page("Corpus RAG\nPage 2\nContenu B.", page_number=2),
    ]

    # Retire les lignes répétées
    cleaned = remove_repeated_lines(pages)

    # "Corpus RAG" et "Page 1"/"Page 2" (même signature "Page #") ont disparu
    assert [page.text for page in cleaned] == ["Contenu A.", "Contenu B."]


def test_single_page_document_is_unchanged() -> None:
    # Avec une seule page, on ne peut rien détecter de répété
    pages = [make_page("Corpus RAG\nPage 1\nContenu.")]

    # Le texte reste identique
    assert remove_repeated_lines(pages)[0].text == "Corpus RAG\nPage 1\nContenu."


def test_repeated_line_in_body_is_kept() -> None:
    # Corps différent sur chaque page (sans chiffres, pour ne pas créer de signatures identiques)
    body_1 = [
        "Alpha.",
        "Bravo.",
        "Charlie.",
        "Phrase commune.",
        "Delta.",
        "Echo.",
        "Fox.",
    ]
    body_2 = [
        "Golf.",
        "Hotel.",
        "India.",
        "Phrase commune.",
        "Juliet.",
        "Kilo.",
        "Lima.",
    ]

    # Deux pages : même en-tête, et une phrase identique au milieu (hors des zones haut/bas)
    page_1 = make_page("\n".join(["En-tête", *body_1]), page_number=1)
    page_2 = make_page("\n".join(["En-tête", *body_2]), page_number=2)

    # Retire les lignes répétées
    cleaned = remove_repeated_lines([page_1, page_2])

    # L'en-tête est retiré, mais la phrase commune du milieu est conservée
    assert "En-tête" not in cleaned[0].text
    assert "Phrase commune." in cleaned[0].text


# --- clean_pages ---


def test_clean_pages_keeps_metadata_and_cleans_text() -> None:
    # Un document de 2 pages avec en-tête répété et ligne coupée
    pages = [
        make_page(
            "Corpus RAG\nPage 1\nLe RAG associe une\nrecherche d’informations.",
            page_number=1,
        ),
        make_page("Corpus RAG\nPage 2\nSuite du cours.", page_number=2),
    ]

    # Nettoyage complet
    cleaned = clean_pages(pages)

    # Le texte est propre : en-tête retiré, ligne recollée, apostrophe normalisée
    assert cleaned[0].text == "Le RAG associe une recherche d'informations."

    # Les métadonnées sont conservées
    assert (cleaned[0].document_id, cleaned[0].page_number) == ("doc1", 1)
    assert cleaned[1].page_number == 2


def test_page_empty_after_cleaning_is_dropped(caplog: pytest.LogCaptureFixture) -> None:
    # La page 2 ne contient que l'en-tête répété
    pages = [
        make_page("Corpus RAG\nPage 1\nContenu.", page_number=1),
        make_page("Corpus RAG\nPage 2", page_number=2),
    ]

    # Nettoyage en capturant les avertissements
    with caplog.at_level(logging.WARNING):
        # Nettoyage complet
        cleaned = clean_pages(pages)

    # Seule la page 1 reste
    assert [page.page_number for page in cleaned] == [1]

    # Un avertissement signale la page 2
    assert "page 2 vide après nettoyage" in caplog.text


def test_documents_are_cleaned_independently() -> None:
    # Deux documents différents : "Commun" est répété DANS le document 1 seulement
    pages = [
        make_page("Commun\nTexte 1A.", page_number=1, document_id="doc1"),
        make_page("Commun\nTexte 1B.", page_number=2, document_id="doc1"),
        make_page("Commun\nTexte 2.", page_number=1, document_id="doc2"),
    ]

    # Nettoyage complet
    cleaned = clean_pages(pages)

    # Dans doc1, "Commun" est retiré ; doc2 n'a qu'une page, donc "Commun" reste
    # (et il est recollé à la ligne suivante, car il ne finit pas par un point)
    assert [page.text for page in cleaned] == [
        "Texte 1A.",
        "Texte 1B.",
        "Commun Texte 2.",
    ]
