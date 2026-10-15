"""Mesures du modèle d'embeddings sur nos vrais chunks.

Répond à des questions laissées ouvertes en Phase 3 :
    - Combien de tokens font réellement nos chunks de 800 caractères ?
    - Tiennent-ils dans la limite du modèle (512 tokens), sans troncature ?
    - Combien de temps prend la vectorisation sur CPU ?
    - Les similarités ont-elles du sens sur une vraie question ?

Utilisation (depuis la racine du projet, venv activé) :
    python -m scripts.inspect_embeddings
"""

# time.perf_counter : chronomètre précis pour mesurer les durées
import time

# Configuration centralisée : modèle et paramètres de chunking
from app.core.config import get_settings

# Configuration du logging : ce script est un POINT D'ENTRÉE
from app.core.logging_config import setup_logging

# Le module mesuré
from app.embeddings.embedding_model import EmbeddingModel, cosine_similarity

# Les étapes d'ingestion qui produisent les chunks
from app.ingestion.chunker import chunk_pages
from app.ingestion.pdf_loader import load_pdfs_from_directory
from app.ingestion.text_cleaner import clean_pages

# Question de démonstration pour la similarité
DEMO_QUESTION = "Pourquoi faut-il normaliser les vecteurs ?"

# Nombre de chunks les plus proches affichés
DEMO_TOP_K = 3


def main() -> None:
    """Point d'entrée : chunks réels → tokens, vitesse et similarités mesurés."""
    # Configure le logging (une seule fois, au point d'entrée)
    setup_logging()

    # Lit la configuration
    settings = get_settings()

    # Produit les chunks exactement comme le fera le pipeline
    pages = clean_pages(load_pdfs_from_directory(settings.raw_data_dir))
    chunks = chunk_pages(
        pages, settings.chunk_size, settings.chunk_overlap, settings.chunk_strategy
    )

    # Crée le modèle configuré
    model = EmbeddingModel(
        settings.embedding_model_name,
        settings.embedding_device,
        settings.embedding_batch_size,
    )

    # Mesure le temps de chargement (le modèle est chargé au premier usage)
    start = time.perf_counter()
    dimension = model.dimension
    load_seconds = time.perf_counter() - start

    # Accès au vrai modèle Sentence Transformers (tokenizer et limite de longueur)
    encoder = model._get_encoder()

    # Nombre de tokens de chaque chunk, préfixe "passage: " compris (comme à l'indexation)
    token_counts = [
        len(encoder.tokenizer(f"{model.document_prefix}{chunk.text}")["input_ids"])
        for chunk in chunks
    ]

    # Rapport caractères / tokens moyen
    chars_per_token = sum(len(c.text) for c in chunks) / sum(token_counts)

    # Mesure le temps de vectorisation de tous les chunks
    start = time.perf_counter()
    vectors = model.embed_documents([chunk.text for chunk in chunks])
    encode_seconds = time.perf_counter() - start

    # Rapport sur le modèle
    print(f"\nModèle : {model.model_name}")
    print(f"Dimension : {dimension}  |  limite : {encoder.max_seq_length} tokens")
    print(f"Chargement : {load_seconds:.1f} s")

    # Rapport sur les tokens
    print(
        f"\nChunks : {len(chunks)} (stratégie {settings.chunk_strategy}, {settings.chunk_size}/{settings.chunk_overlap})"
    )
    print(
        f"Tokens par chunk : min {min(token_counts)}, moyenne {sum(token_counts) / len(token_counts):.0f}, max {max(token_counts)}"
    )
    print(f"Caractères par token (moyenne) : {chars_per_token:.2f}")
    print(
        f"Chunks tronqués (> {encoder.max_seq_length} tokens) : {sum(n > encoder.max_seq_length for n in token_counts)}"
    )

    # Rapport sur la vitesse
    print(
        f"\nVectorisation de {len(chunks)} chunks : {encode_seconds:.2f} s ({1000 * encode_seconds / len(chunks):.0f} ms/chunk)"
    )

    # Démonstration : similarité entre une question et chaque chunk
    question_vector = model.embed_query(DEMO_QUESTION)
    scored = sorted(
        (
            (cosine_similarity(question_vector, vector), chunk)
            for vector, chunk in zip(vectors, chunks, strict=True)
        ),
        key=lambda pair: pair[0],
        reverse=True,
    )

    # Affiche les chunks les plus proches et le plus éloigné
    print(f"\nQuestion : {DEMO_QUESTION!r}")
    for score, chunk in scored[:DEMO_TOP_K]:
        # Score cosinus, identifiant du chunk et début de son texte
        print(f"  {score:.3f}  {chunk.chunk_id}  {chunk.text[:70]!r}")
    print(f"  ...\n  {scored[-1][0]:.3f}  {scored[-1][1].chunk_id}  (le moins proche)")


# Ce bloc ne s'exécute que si on lance le fichier directement (pas si on l'importe)
if __name__ == "__main__":
    # Lance le programme
    main()
