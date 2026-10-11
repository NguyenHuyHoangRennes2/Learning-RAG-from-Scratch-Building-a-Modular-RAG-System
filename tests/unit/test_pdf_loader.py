"""Tests unitaires du chargeur PDF (app/ingestion/pdf_loader.py).

Les PDF de test sont créés à la volée dans un dossier temporaire (tmp_path) :
les tests ne dépendent donc pas des vrais PDF de data/raw/.
"""

# logging pour vérifier les niveaux des messages capturés
import logging

# shutil.copy copie un fichier octet par octet (pour créer un doublon exact)
import shutil

# Path représente un chemin de fichier
from pathlib import Path

# PyMuPDF sert ici à FABRIQUER des petits PDF de test
import pymupdf

# pytest fournit tmp_path, caplog et pytest.raises
import pytest

# Les fonctions et l'erreur que l'on teste
from app.ingestion.pdf_loader import (
    DOCUMENT_ID_LENGTH,
    PDFLoadError,
    compute_document_id,
    load_pdf,
    load_pdfs_from_directory,
)


def create_pdf(path: Path, page_texts: list[str]) -> Path:
    """Crée un PDF avec une page par texte ; un texte vide donne une page blanche."""
    # Crée un document PDF vide, en mémoire
    doc = pymupdf.open()

    # Ajoute une page pour chaque texte demandé
    for text in page_texts:
        # Nouvelle page blanche (format A4 par défaut)
        page = doc.new_page()

        # Écrit le texte seulement s'il n'est pas vide
        if text:
            # Écrit le texte à 72 points (1 pouce) du bord gauche et du haut
            page.insert_text((72, 72), text)

    # Enregistre le PDF sur le disque
    doc.save(path)

    # Libère le document en mémoire
    doc.close()

    # Renvoie le chemin pour pouvoir l'utiliser directement
    return path


def test_one_document_page_per_pdf_page(tmp_path: Path) -> None:
    # Crée un PDF de 2 pages
    pdf_path = create_pdf(tmp_path / "cours.pdf", ["Premiere page", "Deuxieme page"])

    # Charge le PDF
    pages = load_pdf(pdf_path)

    # On obtient 2 pages, numérotées 1 et 2 (et non 0 et 1)
    assert [page.page_number for page in pages] == [1, 2]

    # Le texte de chaque page est bien extrait
    assert "Premiere page" in pages[0].text
    assert "Deuxieme page" in pages[1].text


def test_source_is_the_file_name(tmp_path: Path) -> None:
    # Crée un PDF d'une page
    pdf_path = create_pdf(tmp_path / "mon_document.pdf", ["Texte"])

    # La source est le nom du fichier seul, sans le chemin complet
    assert load_pdf(pdf_path)[0].source == "mon_document.pdf"


def test_document_id_depends_on_content_not_name(tmp_path: Path) -> None:
    # Crée un PDF original
    original = create_pdf(tmp_path / "original.pdf", ["Contenu A"])

    # Copie exacte sous un autre nom
    copy = tmp_path / "copie.pdf"
    shutil.copy(original, copy)

    # Crée un PDF au contenu différent
    other = create_pdf(tmp_path / "autre.pdf", ["Contenu B"])

    # Même contenu -> même identifiant, quel que soit le nom
    assert compute_document_id(original) == compute_document_id(copy)

    # Contenu différent -> identifiant différent
    assert compute_document_id(original) != compute_document_id(other)

    # L'identifiant a la longueur prévue
    assert len(compute_document_id(original)) == DOCUMENT_ID_LENGTH


def test_empty_page_is_skipped_with_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # Crée un PDF : page 1 avec du texte, page 2 blanche
    pdf_path = create_pdf(tmp_path / "scan.pdf", ["Texte", ""])

    # Charge le PDF en capturant les logs à partir du niveau WARNING
    with caplog.at_level(logging.WARNING):
        # Chargement
        pages = load_pdf(pdf_path)

    # Seule la page 1 est gardée
    assert [page.page_number for page in pages] == [1]

    # Un avertissement mentionne la page 2
    assert "page 2 sans texte" in caplog.text


def test_missing_file_raises_pdf_load_error(tmp_path: Path) -> None:
    # Charger un fichier qui n'existe pas doit lever PDFLoadError
    with pytest.raises(PDFLoadError, match="introuvable"):
        # Tentative de chargement
        load_pdf(tmp_path / "absent.pdf")


def test_corrupted_file_raises_pdf_load_error(tmp_path: Path) -> None:
    # Crée un faux PDF : l'extension est .pdf mais le contenu est du texte quelconque
    fake_pdf = tmp_path / "faux.pdf"
    fake_pdf.write_bytes(b"ceci n'est pas un PDF")

    # Le chargement doit lever PDFLoadError
    with pytest.raises(PDFLoadError, match="corrompu"):
        # Tentative de chargement
        load_pdf(fake_pdf)


def test_password_protected_pdf_raises_pdf_load_error(tmp_path: Path) -> None:
    # Crée un PDF en mémoire avec une page de texte
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Secret")

    # L'enregistre chiffré avec un mot de passe utilisateur
    protected = tmp_path / "protege.pdf"
    doc.save(
        protected,
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        user_pw="motdepasse",
        owner_pw="admin",
    )
    doc.close()

    # Le chargement doit lever PDFLoadError
    with pytest.raises(PDFLoadError, match="mot de passe"):
        # Tentative de chargement
        load_pdf(protected)


def test_directory_skips_bad_files_and_duplicates(tmp_path: Path) -> None:
    # Deux PDF valides au contenu différent
    create_pdf(tmp_path / "a.pdf", ["Document A"])
    create_pdf(tmp_path / "b.pdf", ["Document B"])

    # Un doublon exact de a.pdf sous un autre nom
    shutil.copy(tmp_path / "a.pdf", tmp_path / "a_copie.pdf")

    # Un faux PDF illisible
    (tmp_path / "casse.pdf").write_bytes(b"pas un pdf")

    # Charge tout le dossier
    pages = load_pdfs_from_directory(tmp_path)

    # Seuls a.pdf et b.pdf sont gardés : la copie (doublon) et le fichier cassé sont ignorés
    assert [page.source for page in pages] == ["a.pdf", "b.pdf"]


def test_missing_directory_raises_pdf_load_error(tmp_path: Path) -> None:
    # Charger un dossier inexistant doit lever PDFLoadError
    with pytest.raises(PDFLoadError, match="Dossier introuvable"):
        # Tentative de chargement
        load_pdfs_from_directory(tmp_path / "inexistant")
