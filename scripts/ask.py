"""Pose une question au RAG depuis le terminal.

Utilisation (depuis la racine du projet, venv activé, index construit) :
    python -m scripts.ask "Qu'est-ce que le RAG ?"

Si Ollama est injoignable, le script affiche quand même les passages retrouvés
(la recherche ne dépend pas du LLM).
"""

# argparse : lecture de la question sur la ligne de commande
import argparse

# Configuration centralisée
from app.core.config import get_settings

# Configuration du logging : ce script est un POINT D'ENTRÉE
from app.core.logging_config import setup_logging

# Erreur levée quand le LLM ne peut pas répondre
from app.generation.llm import LLMError

# Types affichés
from app.models import SearchResult

# Assemblage de tous les composants
from app.rag.pipeline import build_pipeline


def print_sources(sources: tuple[SearchResult, ...] | list[SearchResult]) -> None:
    """Affiche les passages numérotés, avec leur origine et leur score."""
    # Une ligne d'en-tête et un extrait par source
    for number, result in enumerate(sources, start=1):
        # [n] fichier, page, score, puis le début du texte
        print(f"  [{number}] {result.chunk.citation} (score {result.score:.3f})")
        print(f"      {result.chunk.text[:150]}...")


def main() -> None:
    """Point d'entrée : question → réponse citée (ou passages seuls si le LLM est absent)."""
    # Configure le logging : WARNING pour ne pas noyer la réponse dans les messages INFO
    setup_logging("WARNING")

    # Lit la question
    parser = argparse.ArgumentParser(description="Pose une question au RAG.")
    parser.add_argument("question", help="la question, entre guillemets")
    args = parser.parse_args()

    # Pipeline complet construit depuis la configuration
    pipeline = build_pipeline(get_settings())

    # Interroge le RAG
    try:
        # Recherche + génération
        result = pipeline.ask(args.question)
    except LLMError as error:
        # LLM indisponible : on montre au moins ce que la recherche a trouvé
        print(f"\n⚠️  {error}\n\nPassages retrouvés (sans génération) :")
        print_sources(pipeline.qa.retriever.retrieve(args.question))
        return

    # Réponse
    print(f"\n{result.answer}\n")

    # Sources fournies au LLM, en signalant celles qui sont citées
    print(f"Sources (citées : {list(result.cited) or 'aucune'}) :")
    print_sources(result.sources)

    # Latence de chaque étape
    print(
        f"\nRecherche : {result.retrieval_ms:.0f} ms — génération : {result.generation_ms:.0f} ms"
    )


# Ce bloc ne s'exécute que si on lance le fichier directement (pas si on l'importe)
if __name__ == "__main__":
    # Lance le programme
    main()
