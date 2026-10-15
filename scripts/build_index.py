"""Construit (ou complète) l'index vectoriel à partir des PDF de data/raw/.

Utilisation (depuis la racine du projet, venv activé) :
    python -m scripts.build_index            # indexe les nouveaux PDF seulement
    python -m scripts.build_index --replace  # réindexe tout (après un changement de chunking)
"""

# argparse : lecture de l'option --replace
import argparse

# time.perf_counter : mesure de la durée totale
import time

# Configuration centralisée
from app.core.config import get_settings

# Configuration du logging : ce script est un POINT D'ENTRÉE
from app.core.logging_config import setup_logging

# Assemblage de tous les composants à partir de la configuration
from app.rag.pipeline import build_pipeline


def main() -> None:
    """Point d'entrée : PDF de data/raw → chunks vectorisés dans storage/chroma."""
    # Configure le logging (une seule fois, au point d'entrée)
    setup_logging()

    # Option --replace : réindexer même les documents déjà présents
    parser = argparse.ArgumentParser(description="Indexe les PDF de data/raw.")
    parser.add_argument(
        "--replace", action="store_true", help="réindexer les documents déjà présents"
    )
    args = parser.parse_args()

    # Pipeline complet construit depuis la configuration (le LLM n'est pas appelé ici)
    pipeline = build_pipeline(get_settings())

    # Lance l'ingestion et mesure sa durée
    start = time.perf_counter()
    reports = pipeline.ingest_directory(replace=args.replace)
    seconds = time.perf_counter() - start

    # Rapport par document
    print()
    for report in reports:
        # Statut, nom du fichier, pages, chunks et éventuel message
        print(
            f"{report.status:<8} {report.source:<42} {report.page_count} p. "
            f"{report.chunk_count:>3} chunks  {report.message}"
        )

    # Rapport global
    print(
        f"\nDurée : {seconds:.1f} s — chunks dans l'index : {pipeline.ingestion.store.count()}"
    )


# Ce bloc ne s'exécute que si on lance le fichier directement (pas si on l'importe)
if __name__ == "__main__":
    # Lance le programme
    main()
