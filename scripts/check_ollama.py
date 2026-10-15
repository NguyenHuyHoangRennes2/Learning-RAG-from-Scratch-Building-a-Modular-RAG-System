"""Vérifie qu'Ollama est joignable et que le modèle configuré est installé, puis le teste.

Utilisation (depuis la racine du projet, venv activé) :
    python -m scripts.check_ollama
"""

# sys.exit : code de sortie 1 en cas de problème (utile dans un script d'installation)
import sys

# Configuration centralisée (adresse et modèle Ollama)
from app.core.config import get_settings

# Configuration du logging : ce script est un POINT D'ENTRÉE
from app.core.logging_config import setup_logging

# Le client testé
from app.generation.llm import LLMError, OllamaClient


def main() -> None:
    """Point d'entrée : diagnostic d'Ollama en deux temps (disponibilité, puis génération)."""
    # Configure le logging (une seule fois, au point d'entrée)
    setup_logging()

    # Lit la configuration
    settings = get_settings()

    # Client construit à partir de la configuration
    client = OllamaClient(
        settings.ollama_base_url,
        settings.ollama_model,
        settings.llm_temperature,
        settings.llm_num_ctx,
        settings.llm_timeout_seconds,
    )

    # 1. Le serveur répond-il, et le modèle est-il téléchargé ?
    if not client.is_available():
        # Diagnostic et marche à suivre
        print(
            f"❌ Ollama injoignable à {settings.ollama_base_url} ou modèle {settings.ollama_model!r} absent."
        )
        print(
            "   1. Installer Ollama : https://ollama.com/download (ou : winget install Ollama.Ollama)"
        )
        print(f"   2. Télécharger le modèle : ollama pull {settings.ollama_model}")
        print("   3. Relancer : python -m scripts.check_ollama")
        sys.exit(1)

    # 2. Une vraie génération courte
    try:
        # Question triviale : on vérifie seulement que la chaîne fonctionne
        answer = client.generate(
            "Réponds en un mot.", "Quelle est la couleur du ciel par beau temps ?"
        )
    except LLMError as error:
        # Échec de génération (délai, mémoire...)
        print(f"❌ Ollama joignable mais la génération a échoué : {error}")
        sys.exit(1)

    # Tout fonctionne
    print(f"✅ Ollama fonctionne avec {settings.ollama_model} : {answer!r}")


# Ce bloc ne s'exécute que si on lance le fichier directement (pas si on l'importe)
if __name__ == "__main__":
    # Lance le programme
    main()
