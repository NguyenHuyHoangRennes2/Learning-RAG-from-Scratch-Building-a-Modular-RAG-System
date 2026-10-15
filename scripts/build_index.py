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

# Les composants assemblés
from app.embeddings.embedding_model import EmbeddingModel
from app.rag.pipeline import IngestionPipeline
from app.vectorstore.chroma_store import ChromaStore


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

    # Lit la configuration
    settings = get_settings()

    # Assemble les composants à partir de la configuration
    pipeline = IngestionPipeline(
        embedder=EmbeddingModel(
            settings.embedding_model_name,
            settings.embedding_device,
            settings.embedding_batch_size,
        ),
        store=ChromaStore(
            settings.chroma_dir,
            settings.chroma_collection_name,
            settings.embedding_model_name,
        ),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        chunk_strategy=settings.chunk_strategy,
    )

    # Lance l'ingestion et mesure sa durée
    start = time.perf_counter()
    reports = pipeline.ingest_directory(settings.raw_data_dir, replace=args.replace)
    seconds = time.perf_counter() - start

    # Rapport par document
    print()
    for report in reports:
        # Statut, nom du fichier, pages, chunks et éventuel message
        print(
            f"{report.status:<8} {report.source:<42} {report.page_count} p. {report.chunk_count:>3} chunks  {report.message}"
        )

    # Rapport global
    print(f"\nDurée : {seconds:.1f} s — chunks dans l'index : {pipeline.store.count()}")


# Ce bloc ne s'exécute que si on lance le fichier directement (pas si on l'importe)
if __name__ == "__main__":
    # Lance le programme
    main()
