"""Comparaison des stratégies de chunking ("fixed" et "sentence") sur les vrais PDF.

Pour chaque stratégie, le script affiche des statistiques MESURÉES :
nombre de chunks, tailles, redondance due au chevauchement, et proportion de
chunks dont les bords sont « propres » (début et fin de phrase).

Utilisation (depuis la racine du projet, venv activé) :
    python -m scripts.compare_chunking
    python -m scripts.compare_chunking --size 400 --overlap 50
"""

# argparse : lecture des options de la ligne de commande (--size, --overlap)
import argparse

# logging pour les messages de diagnostic (le rapport, lui, est affiché avec print)
import logging

# dataclass pour regrouper les statistiques d'une stratégie
from dataclasses import dataclass

# Configuration centralisée : dossier des PDF et paramètres de chunking par défaut
from app.core.config import ChunkStrategy, get_settings

# Configuration du logging : ce script est un POINT D'ENTRÉE, c'est donc ici qu'on l'appelle
from app.core.logging_config import setup_logging

# Étape 3 de l'ingestion : découpage en chunks
from app.ingestion.chunker import chunk_pages

# Étape 1 de l'ingestion : lecture des PDF
from app.ingestion.pdf_loader import load_pdfs_from_directory

# Étape 2 de l'ingestion : nettoyage du texte
from app.ingestion.text_cleaner import clean_pages

# Les structures de données manipulées
from app.models import Chunk, DocumentPage

# Logger nommé d'après le module : "scripts.compare_chunking"
logger = logging.getLogger(__name__)

# Les stratégies comparées, dans l'ordre d'affichage
STRATEGIES: tuple[ChunkStrategy, ...] = ("fixed", "sentence")

# Ponctuation qui termine proprement un chunk
CLEAN_ENDINGS = (".", "!", "?", "…")


@dataclass(frozen=True)
class ChunkingStats:
    """Statistiques mesurées pour une stratégie de chunking."""

    # Nombre total de chunks produits
    chunk_count: int

    # Taille du plus petit chunk (caractères)
    min_length: int

    # Taille moyenne des chunks (caractères)
    mean_length: float

    # Taille du plus grand chunk (caractères)
    max_length: int

    # Caractères stockés / caractères du texte d'origine (1.0 = aucune répétition)
    redundancy: float

    # Proportion de chunks qui commencent par une majuscule ou un chiffre (début de phrase)
    clean_start_ratio: float

    # Proportion de chunks qui se terminent par une ponctuation finale (fin de phrase)
    clean_end_ratio: float


def _starts_cleanly(text: str) -> bool:
    """Indique si un chunk commence comme une phrase : majuscule ou chiffre (titre numéroté)."""
    # Le premier caractère est examiné ; un chunk n'est jamais vide (validé par Chunk)
    first = text[0]

    # isupper() couvre aussi les majuscules accentuées ; isdigit() couvre "2. Titre"
    return first.isupper() or first.isdigit()


def compute_stats(chunks: list[Chunk], pages: list[DocumentPage]) -> ChunkingStats:
    """Calcule les statistiques d'un découpage par rapport aux pages d'origine."""
    # Aucun chunk : on refuse plutôt que de diviser par zéro
    if not chunks:
        # Message explicite pour l'appelant
        raise ValueError("aucun chunk à analyser")

    # Longueur de chaque chunk
    lengths = [len(chunk.text) for chunk in chunks]

    # Longueur totale du texte d'origine (toutes les pages)
    total_page_length = sum(len(page.text) for page in pages)

    # Nombre de chunks dont le début est propre
    clean_starts = sum(_starts_cleanly(chunk.text) for chunk in chunks)

    # Nombre de chunks dont la fin est propre (endswith accepte un tuple de suffixes)
    clean_ends = sum(chunk.text.endswith(CLEAN_ENDINGS) for chunk in chunks)

    # Regroupe toutes les mesures
    return ChunkingStats(
        # Nombre de chunks
        chunk_count=len(chunks),
        # Plus petit chunk
        min_length=min(lengths),
        # Taille moyenne
        mean_length=sum(lengths) / len(lengths),
        # Plus grand chunk
        max_length=max(lengths),
        # Redondance : ce qu'on stocke rapporté à ce qu'on avait
        redundancy=sum(lengths) / total_page_length,
        # Proportion de débuts propres
        clean_start_ratio=clean_starts / len(chunks),
        # Proportion de fins propres
        clean_end_ratio=clean_ends / len(chunks),
    )


def print_report(results: dict[ChunkStrategy, ChunkingStats]) -> None:
    """Affiche un tableau comparatif des stratégies."""
    # En-tête du tableau
    print(f"{'Mesure':<28}" + "".join(f"{name:>12}" for name in results))

    # Lignes du tableau : (libellé, fonction qui formate la valeur d'une stratégie)
    rows = [
        ("Nombre de chunks", lambda s: f"{s.chunk_count}"),
        ("Taille min (car.)", lambda s: f"{s.min_length}"),
        ("Taille moyenne (car.)", lambda s: f"{s.mean_length:.0f}"),
        ("Taille max (car.)", lambda s: f"{s.max_length}"),
        ("Redondance (stocké/texte)", lambda s: f"{s.redundancy:.2f}"),
        ("Débuts propres", lambda s: f"{s.clean_start_ratio:.0%}"),
        ("Fins propres", lambda s: f"{s.clean_end_ratio:.0%}"),
    ]

    # Affiche chaque ligne, une colonne par stratégie
    for label, fmt in rows:
        # Libellé aligné à gauche, valeurs alignées à droite
        print(
            f"{label:<28}" + "".join(f"{fmt(stats):>12}" for stats in results.values())
        )


def print_first_boundary(chunks: list[Chunk], strategy: ChunkStrategy) -> None:
    """Affiche la première frontière entre deux chunks, pour la voir à l'œil."""
    # Il faut au moins deux chunks pour avoir une frontière
    if len(chunks) < 2:
        # Rien à montrer
        return

    # Titre de l'exemple
    print(
        f"\n[{strategy}] frontière entre {chunks[0].chunk_id} et {chunks[1].chunk_id}"
    )

    # Les 60 derniers caractères du premier chunk
    print(f"  fin    : ...{chunks[0].text[-60:]!r}")

    # Les 60 premiers caractères du chunk suivant
    print(f"  début  : {chunks[1].text[:60]!r}...")


def parse_args() -> argparse.Namespace:
    """Lit les options --size et --overlap (par défaut : valeurs de la configuration)."""
    # Valeurs par défaut lues dans la configuration centralisée
    settings = get_settings()

    # Description affichée par --help
    parser = argparse.ArgumentParser(description="Compare les stratégies de chunking.")

    # Taille maximale d'un chunk
    parser.add_argument("--size", type=int, default=settings.chunk_size)

    # Chevauchement entre chunks
    parser.add_argument("--overlap", type=int, default=settings.chunk_overlap)

    # Analyse la ligne de commande
    return parser.parse_args()


def main() -> None:
    """Point d'entrée : PDF → pages nettoyées → chunks (2 stratégies) → rapport."""
    # Configure le logging (une seule fois, au point d'entrée)
    setup_logging()

    # Lit les options de la ligne de commande
    args = parse_args()

    # Charge et nettoie les pages une seule fois : les deux stratégies partent du même texte
    pages = clean_pages(load_pdfs_from_directory(get_settings().raw_data_dir))

    # Résultats par stratégie
    results: dict[ChunkStrategy, ChunkingStats] = {}

    # Chunks par stratégie (pour l'exemple de frontière)
    chunks_by_strategy: dict[ChunkStrategy, list[Chunk]] = {}

    # Découpe avec chaque stratégie et mesure
    for strategy in STRATEGIES:
        # Découpe toutes les pages
        chunks = chunk_pages(pages, args.size, args.overlap, strategy)

        # Mémorise les chunks
        chunks_by_strategy[strategy] = chunks

        # Calcule et mémorise les statistiques
        results[strategy] = compute_stats(chunks, pages)

    # Rappel des paramètres utilisés
    print(f"\nsize={args.size}, overlap={args.overlap}, {len(pages)} page(s)\n")

    # Tableau comparatif
    print_report(results)

    # Exemples de frontières
    for strategy, chunks in chunks_by_strategy.items():
        # Affiche la première frontière de cette stratégie
        print_first_boundary(chunks, strategy)


# Ce bloc ne s'exécute que si on lance le fichier directement (pas si on l'importe)
if __name__ == "__main__":
    # Lance le programme
    main()
