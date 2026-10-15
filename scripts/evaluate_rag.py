"""Évalue les RÉPONSES du RAG sur les 20 questions de référence.

Utilisation (depuis la racine du projet, venv activé, index construit) :
    python -m scripts.evaluate_rag                      # avec Ollama (vrai LLM)
    python -m scripts.evaluate_rag --llm baseline       # référence extractive, sans LLM

Résultats : affichés et enregistrés dans evaluation/results/answers_<llm>.json
"""

# argparse : choix du générateur (ollama ou baseline)
import argparse

# json : écriture du fichier de résultats
import json

# asdict : conversion d'une dataclass en dictionnaire (pour le JSON)
from dataclasses import asdict

# Configuration centralisée
from app.core.config import PROJECT_ROOT, get_settings

# Configuration du logging : ce script est un POINT D'ENTRÉE
from app.core.logging_config import setup_logging

# Évaluation des réponses et référence sans LLM
from app.evaluation.answer_eval import evaluate_answer, summarize_answers
from app.evaluation.baselines import ExtractiveBaseline
from app.evaluation.dataset import load_questions

# Client Ollama et pipeline complet
from app.generation.llm import LLMClient, OllamaClient
from app.rag.pipeline import build_pipeline

# Dossier des résultats (versionné : trace des mesures)
RESULTS_DIR = PROJECT_ROOT / "evaluation" / "results"


def main() -> None:
    """Point d'entrée : pose les 20 questions au pipeline et mesure les réponses."""
    # Configure le logging (WARNING : le rapport reste lisible)
    setup_logging("WARNING")

    # Choix du générateur
    parser = argparse.ArgumentParser(description="Évalue les réponses du RAG.")
    parser.add_argument("--llm", choices=["ollama", "baseline"], default="ollama")
    args = parser.parse_args()

    # Lit la configuration
    settings = get_settings()

    # Générateur : vrai LLM, ou référence extractive
    llm: LLMClient
    if args.llm == "ollama":
        # Client Ollama configuré
        ollama = OllamaClient(
            settings.ollama_base_url,
            settings.ollama_model,
            settings.llm_temperature,
            settings.llm_num_ctx,
            settings.llm_timeout_seconds,
        )

        # Sans Ollama, l'évaluation n'aurait aucun sens : on s'arrête avec la marche à suivre
        if not ollama.is_available():
            raise SystemExit(
                f"Ollama ou le modèle {settings.ollama_model!r} est indisponible : "
                "lancez « python -m scripts.check_ollama » pour le diagnostic, "
                "ou utilisez --llm baseline."
            )
        llm = ollama
    else:
        # Référence sans LLM
        llm = ExtractiveBaseline()

    # Pipeline complet sur le VRAI index (storage/chroma)
    pipeline = build_pipeline(settings, llm=llm)

    # Pose chaque question et mesure la réponse
    questions = load_questions()
    results = []
    for question in questions:
        # Réponse du pipeline
        answer = pipeline.ask(question.question)

        # Mesures de cette réponse
        result = evaluate_answer(question, answer)
        results.append(result)

        # Une ligne par question
        print(
            f"{question.id} {question.category:<16} abst={'oui' if result.abstained else 'non'} "
            f"({'OK' if result.abstention_correct else 'FAUX'})  "
            f"mots-clés={result.keyword_coverage}  citations={result.citation_precision}  "
            f"fidélité={result.faithfulness}  {result.generation_ms:.0f} ms"
        )

    # Synthèse
    summary = summarize_answers(results)
    print(f"\nSynthèse ({args.llm}, {len(questions)} questions) :")
    for name, value in summary.items():
        # None = métrique non applicable
        print(f"  {name:<30} {'n/a' if value is None else f'{value:.3f}'}")

    # Enregistre les résultats détaillés et la synthèse
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / f"answers_{args.llm}.json"
    path.write_text(
        json.dumps(
            {
                "llm": getattr(llm, "model", args.llm),
                "embedding_model": settings.embedding_model_name,
                "chunking": f"{settings.chunk_strategy} {settings.chunk_size}/{settings.chunk_overlap}",
                "top_k": settings.retrieval_top_k,
                "summary": summary,
                "per_question": [asdict(r) for r in results],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nRésultats enregistrés dans {path.relative_to(PROJECT_ROOT)}")


# Ce bloc ne s'exécute que si on lance le fichier directement (pas si on l'importe)
if __name__ == "__main__":
    # Lance le programme
    main()
