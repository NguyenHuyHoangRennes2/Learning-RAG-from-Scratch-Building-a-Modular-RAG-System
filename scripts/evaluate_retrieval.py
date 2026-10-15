"""Compare plusieurs réglages de chunking avec les métriques de recherche.

Protocole (repris du document 03_evaluation_rag.pdf) : même corpus, mêmes
questions, UN paramètre à la fois. Chaque réglage est indexé dans une base
temporaire (la vraie base storage/chroma n'est pas touchée), avec le vrai modèle
d'embeddings.

Utilisation (depuis la racine du projet, venv activé) :
    python -m scripts.evaluate_retrieval
Résultats : affichés et enregistrés dans evaluation/results/retrieval.json
"""

# json : écriture du fichier de résultats
import json

# tempfile : dossier temporaire pour chaque base d'évaluation
import tempfile

# time.perf_counter : mesure de la latence de recherche
import time

# Path représente un chemin de fichier
from pathlib import Path

# Configuration centralisée
from app.core.config import PROJECT_ROOT, ChunkStrategy, get_settings

# Configuration du logging : ce script est un POINT D'ENTRÉE
from app.core.logging_config import setup_logging

# Composants
from app.embeddings.embedding_model import EmbeddingModel
from app.evaluation.dataset import find_missing_evidence, load_questions
from app.evaluation.retrieval_eval import RetrievalEvaluation, evaluate_retrieval
from app.ingestion.chunker import chunk_pages
from app.ingestion.pdf_loader import load_pdfs_from_directory
from app.ingestion.text_cleaner import clean_pages
from app.retrieval.retriever import Retriever
from app.vectorstore.chroma_store import ChromaStore

# Réglages comparés : (stratégie, taille, chevauchement)
CONFIGURATIONS: list[tuple[ChunkStrategy, int, int]] = [
    ("sentence", 800, 150),
    ("fixed", 800, 150),
    ("sentence", 400, 50),
    ("fixed", 400, 50),
]

# Valeurs de K comparées (Top-K = 3 ou 5, comme dans le protocole du corpus)
KS = (3, 5)

# Fichier de résultats (versionné : c'est la trace des mesures)
RESULTS_PATH = PROJECT_ROOT / "evaluation" / "results" / "retrieval.json"


def summarize(evaluation: RetrievalEvaluation) -> dict[str, float]:
    """Résume une évaluation en quelques nombres."""
    # Meilleurs scores des questions avec et sans réponse
    answerable = evaluation.top_scores(answerable=True)
    unanswerable = evaluation.top_scores(answerable=False)

    # Métriques agrégées
    return {
        "precision@3": evaluation.mean_precision(3),
        "recall@3": evaluation.mean_recall(3),
        "precision@5": evaluation.mean_precision(5),
        "recall@5": evaluation.mean_recall(5),
        "mrr": evaluation.mrr(),
        "recall@5_paraphrase": evaluation.mean_recall(5, "paraphrase"),
        "recall@5_multi-documents": evaluation.mean_recall(5, "multi-documents"),
        "min_top_score_answerable": min(answerable),
        "max_top_score_unanswerable": max(unanswerable),
    }


def main() -> None:
    """Point d'entrée : un index temporaire par réglage, puis un tableau comparatif."""
    # Configure le logging (une seule fois, au point d'entrée)
    setup_logging("WARNING")

    # Lit la configuration et les questions
    settings = get_settings()
    questions = load_questions()

    # Pages nettoyées (identiques pour tous les réglages)
    pages = clean_pages(load_pdfs_from_directory(settings.raw_data_dir))

    # Garde-fou : toutes les preuves doivent exister dans le corpus
    missing = find_missing_evidence(questions, [page.text for page in pages])
    if missing:
        # Une évaluation avec une preuve introuvable serait fausse
        raise SystemExit(f"Preuves introuvables dans le corpus : {missing}")

    # Un seul modèle d'embeddings, chargé une fois, partagé par tous les réglages
    embedder = EmbeddingModel(settings.embedding_model_name, settings.embedding_device)

    # Résultats par réglage
    rows: dict[str, dict[str, float]] = {}

    # Évalue chaque réglage
    for strategy, size, overlap in CONFIGURATIONS:
        # Nom lisible du réglage
        name = f"{strategy} {size}/{overlap}"

        # Base temporaire (ignore_cleanup_errors : Windows peut garder un verrou sur les fichiers)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            # Indexe le corpus avec ce réglage
            chunks = chunk_pages(pages, size, overlap, strategy)
            store = ChromaStore(Path(tmp), "eval_chunks", settings.embedding_model_name)
            store.add_chunks(chunks, embedder.embed_documents([c.text for c in chunks]))

            # Évalue la recherche et mesure la durée moyenne par question
            start = time.perf_counter()
            evaluation = evaluate_retrieval(
                Retriever(embedder, store, top_k=max(KS)), questions, KS
            )
            latency_ms = 1000 * (time.perf_counter() - start) / len(questions)

        # Résumé chiffré du réglage
        rows[name] = {
            "chunks": len(chunks),
            **summarize(evaluation),
            "latency_ms": latency_ms,
        }

    # Affiche le tableau comparatif (une colonne par réglage)
    print(
        f"\n{len(questions)} questions ({sum(q.answerable for q in questions)} avec réponse)\n"
    )
    print(f"{'Mesure':<28}" + "".join(f"{name:>18}" for name in rows))
    for metric in next(iter(rows.values())):
        # Une ligne par métrique
        print(
            f"{metric:<28}" + "".join(f"{row[metric]:>18.3f}" for row in rows.values())
        )

    # Enregistre les résultats pour garder une trace des mesures
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "embedding_model": settings.embedding_model_name,
                "questions": len(questions),
                "results": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nRésultats enregistrés dans {RESULTS_PATH.relative_to(PROJECT_ROOT)}")


# Ce bloc ne s'exécute que si on lance le fichier directement (pas si on l'importe)
if __name__ == "__main__":
    # Lance le programme
    main()
