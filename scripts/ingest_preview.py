"""Aperçu de l'ingestion : charge, nettoie et exporte le texte des PDF en JSON.

Le résultat (un fichier JSON par document dans data/processed/) permet de VÉRIFIER
à l'œil ce que le RAG va indexer, avant de passer au chunking.

Utilisation (depuis la racine du projet, venv activé) :
    python -m scripts.ingest_preview
"""

# json : écriture des fichiers JSON
import json

# logging pour tracer les fichiers exportés
import logging

# Path représente un chemin de fichier
from pathlib import Path

# Configuration centralisée : dossiers d'entrée (raw) et de sortie (processed)
from app.core.config import get_settings

# Configuration du logging : ce script est un POINT D'ENTRÉE, c'est donc ici qu'on l'appelle
from app.core.logging_config import setup_logging

# Étape 1 de l'ingestion : lecture des PDF
from app.ingestion.pdf_loader import load_pdfs_from_directory

# Étape 2 de l'ingestion : nettoyage du texte
from app.ingestion.text_cleaner import clean_pages

# La structure de données manipulée
from app.models import DocumentPage

# Logger nommé d'après le module : "scripts.ingest_preview"
logger = logging.getLogger(__name__)


def export_pages(pages: list[DocumentPage], output_dir: Path) -> list[Path]:
    """Écrit un fichier JSON par document et renvoie la liste des fichiers créés."""
    # Crée le dossier de sortie s'il n'existe pas (parents=True crée aussi les dossiers parents)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Regroupe les pages par document (un dict garde l'ordre d'insertion)
    pages_by_document: dict[str, list[DocumentPage]] = {}

    # Range chaque page dans la liste de son document
    for page in pages:
        # setdefault crée la liste vide au premier passage, puis renvoie la liste existante
        pages_by_document.setdefault(page.document_id, []).append(page)

    # Liste des fichiers écrits
    written_files: list[Path] = []

    # Écrit un fichier par document
    for document_id, document_pages in pages_by_document.items():
        # Toutes les pages d'un document ont la même source : on lit celle de la première
        source = document_pages[0].source

        # Contenu du fichier JSON : métadonnées du document, puis la liste de ses pages
        data = {
            "document_id": document_id,
            "source": source,
            "pages": [
                {"page_number": page.page_number, "text": page.text}
                for page in document_pages
            ],
        }

        # Nom du fichier de sortie : nom du PDF sans extension (.stem) + ".json"
        output_path = output_dir / f"{Path(source).stem}.json"

        # ensure_ascii=False garde les accents lisibles ("é" et non "é") ; indent=2 indente le JSON
        output_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # Trace le fichier écrit
        logger.info("Exporté : %s (%d page(s))", output_path.name, len(document_pages))

        # Mémorise le chemin du fichier écrit
        written_files.append(output_path)

    # Renvoie la liste des fichiers créés
    return written_files


def main() -> None:
    """Point d'entrée : PDF bruts -> pages nettoyées -> fichiers JSON."""
    # Configure le logging (une seule fois, au point d'entrée)
    setup_logging()

    # Lit la configuration (dossiers d'entrée et de sortie)
    settings = get_settings()

    # Étape 1 : charge les pages brutes de tous les PDF
    raw_pages = load_pdfs_from_directory(settings.raw_data_dir)

    # Étape 2 : nettoie le texte des pages
    cleaned_pages = clean_pages(raw_pages)

    # Étape 3 : exporte le résultat pour inspection
    export_pages(cleaned_pages, settings.processed_data_dir)


# Ce bloc ne s'exécute que si on lance le fichier directement (pas si on l'importe)
if __name__ == "__main__":
    # Lance le programme
    main()
