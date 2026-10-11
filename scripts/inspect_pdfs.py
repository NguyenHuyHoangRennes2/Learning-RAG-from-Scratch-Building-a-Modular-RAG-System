"""Script d'exploration : affiche ce que PyMuPDF extrait de nos PDF.

Utilisation (depuis la racine du projet, venv activé) :
    python -m scripts.inspect_pdfs
"""

# Path représente un chemin de fichier de façon portable (Windows / Linux)
from pathlib import Path

# PyMuPDF : bibliothèque de lecture des PDF (l'ancien nom "fitz" est déprécié)
import pymupdf

# Configuration centralisée : on y lit le chemin du dossier des PDF (pas de chemin en dur)
from app.core.config import get_settings

# Nombre de caractères affichés pour l'aperçu de chaque page
PREVIEW_LENGTH = 400


def inspect_pdf(pdf_path: Path) -> None:
    """Affiche un rapport sur un PDF : métadonnées, pages et aperçu du texte."""
    # Ligne de séparation entre deux fichiers dans le rapport
    print("=" * 70)

    # Affiche le nom du fichier et sa taille en octets
    print(f"Fichier : {pdf_path.name}  ({pdf_path.stat().st_size:,} octets)")

    # Ouvre le PDF ; le "with" referme automatiquement le fichier à la fin, même en cas d'erreur
    with pymupdf.open(pdf_path) as doc:
        # Affiche le nombre total de pages du document
        print(f"Nombre de pages : {doc.page_count}")

        # Garde seulement les métadonnées remplies (titre, auteur...), beaucoup sont souvent vides
        filled_metadata = {key: value for key, value in doc.metadata.items() if value}

        # Affiche ces métadonnées
        print(f"Métadonnées : {filled_metadata}")

        # Parcourt les pages une par une, numérotées à partir de 1 (PyMuPDF compte à partir de 0)
        for page_number, page in enumerate(doc, start=1):
            # Extrait le texte brut de la page (chaîne vide si la page est une image scannée)
            text = page.get_text()

            # Affiche le numéro de page et la longueur du texte extrait
            print(f"\n--- Page {page_number} : {len(text)} caractères ---")

            # repr() montre les caractères invisibles (\n, \t...) : utile pour repérer quoi nettoyer
            print(repr(text[:PREVIEW_LENGTH]))


def main() -> None:
    """Point d'entrée : inspecte tous les PDF du dossier de données brutes."""
    # Récupère le dossier des PDF depuis la configuration (data/raw par défaut)
    raw_dir = get_settings().raw_data_dir

    # Liste les fichiers .pdf du dossier, triés pour avoir toujours le même ordre
    pdf_paths = sorted(raw_dir.glob("*.pdf"))

    # S'il n'y a aucun PDF, on prévient et on s'arrête
    if not pdf_paths:
        # Message pour l'utilisateur
        print(f"Aucun PDF trouvé dans {raw_dir}")

        # Fin de la fonction
        return

    # Inspecte chaque PDF trouvé
    for pdf_path in pdf_paths:
        # Affiche le rapport de ce PDF
        inspect_pdf(pdf_path)


# Ce bloc ne s'exécute que si on lance le fichier directement (pas si on l'importe)
if __name__ == "__main__":
    # Lance le programme
    main()
