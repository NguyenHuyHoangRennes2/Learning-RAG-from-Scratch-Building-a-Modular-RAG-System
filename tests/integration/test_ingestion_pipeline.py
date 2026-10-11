"""Test d'intégration de l'ingestion : PDF -> chargeur -> nettoyage -> export JSON.

Contrairement aux tests unitaires, on vérifie ici que les modules fonctionnent
ENSEMBLE, sur un PDF réaliste fabriqué pour l'occasion (en-tête répété, lignes coupées).
"""

# json pour relire le fichier exporté
import json

# Path représente un chemin de fichier
from pathlib import Path

# PyMuPDF sert à fabriquer le PDF de test
import pymupdf

# Les modules dont on teste l'enchaînement
from app.ingestion.pdf_loader import load_pdfs_from_directory
from app.ingestion.text_cleaner import clean_pages
from scripts.ingest_preview import export_pages

# Modèle de page, construit comme nos vrais PDF : en-tête, numéro de page, titre, ligne coupée
PAGE_TEMPLATE = (
    "Corpus de test • Démonstration\nPage {number}\n{number}. {title}\n{body}\n"
)

# Contenu DIFFÉRENT pour chaque page (comme dans un vrai document) : (titre, corps sur 2 lignes)
PAGE_CONTENTS = [
    (
        "Définition",
        "Le RAG associe une recherche\nd'informations à un modèle de langage.",
    ),
    (
        "Composants",
        "Un chargeur PDF extrait le texte\npage par page avant le découpage.",
    ),
]


def create_realistic_pdf(path: Path) -> None:
    """Crée un PDF de 2 pages qui reproduit les défauts de nos vrais documents."""
    # Document PDF vide, en mémoire
    doc = pymupdf.open()

    # Crée une page par contenu, numérotée à partir de 1
    for number, (title, body) in enumerate(PAGE_CONTENTS, start=1):
        # Remplit le modèle de page avec le numéro, le titre et le corps
        text = PAGE_TEMPLATE.format(number=number, title=title, body=body)

        # Écrit le texte de la page (les \n créent des lignes séparées dans le PDF)
        doc.new_page().insert_text((72, 72), text)

    # Enregistre le PDF sur le disque
    doc.save(path)

    # Libère le document en mémoire
    doc.close()


def test_pdf_is_loaded_and_cleaned(tmp_path: Path) -> None:
    # Crée un PDF réaliste de 2 pages dans un dossier temporaire
    create_realistic_pdf(tmp_path / "cours.pdf")

    # Enchaîne les deux étapes de l'ingestion : chargement puis nettoyage
    pages = clean_pages(load_pdfs_from_directory(tmp_path))

    # Les 2 pages sont présentes, numérotées 1 et 2
    assert [page.page_number for page in pages] == [1, 2]

    # Le texte attendu : en-tête et "Page N" retirés, titre seul sur sa ligne, phrase recollée
    expected = "1. Définition\nLe RAG associe une recherche d'informations à un modèle de langage."

    # Le texte de la page 1 est exactement celui attendu
    assert pages[0].text == expected

    # Les métadonnées sont conservées pour les citations
    assert pages[0].source == "cours.pdf"
    assert pages[0].document_id == pages[1].document_id


def test_cleaned_pages_are_exported_to_json(tmp_path: Path) -> None:
    # Dossier d'entrée avec un PDF réaliste
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    create_realistic_pdf(raw_dir / "cours.pdf")

    # Chaîne complète : chargement -> nettoyage -> export
    pages = clean_pages(load_pdfs_from_directory(raw_dir))
    written = export_pages(pages, tmp_path / "processed")

    # Un seul fichier, nommé d'après le PDF
    assert [path.name for path in written] == ["cours.json"]

    # Relit le fichier JSON écrit
    data = json.loads(written[0].read_text(encoding="utf-8"))

    # Le JSON contient les métadonnées du document et ses 2 pages
    assert data["source"] == "cours.pdf"
    assert [page["page_number"] for page in data["pages"]] == [1, 2]

    # Les accents sont écrits lisiblement (ensure_ascii=False), et pas sous la forme "à"
    assert "à un modèle" in written[0].read_text(encoding="utf-8")
