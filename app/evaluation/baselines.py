"""Référence (baseline) de génération SANS LLM, pour situer les résultats du vrai LLM.

``ExtractiveBaseline`` respecte le protocole LLMClient : au lieu de rédiger, il
recopie le début de la source [1] (le chunk le mieux classé) et le cite. Il ne
s'abstient jamais et n'invente jamais rien.

Utilité :
    - faire tourner toute la chaîne d'évaluation des réponses sans Ollama ;
    - fixer un « plancher » : un LLM qui ferait moins bien que de recopier le
      meilleur passage n'apporterait rien.
"""

# re : extraction du texte de la source [1] dans le prompt
import re

# Texte entre <source id="1" ...> et </source> (DOTALL : le point traverse les sauts de ligne)
FIRST_SOURCE = re.compile(r'<source id="1"[^>]*>\n(.*?)\n</source>', re.DOTALL)

# Longueur maximale de l'extrait recopié, en caractères
MAX_EXTRACT_LENGTH = 300


class ExtractiveBaseline:
    """Faux « LLM » extractif : renvoie le début de la meilleure source, cité [1]."""

    # Nom affiché dans les rapports (comme OllamaClient.model)
    model = "baseline-extractive"

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Recopie le début de la source [1] et ajoute la citation."""
        # Cherche la source [1] dans le prompt construit par build_user_prompt
        match = FIRST_SOURCE.search(user_prompt)

        # Aucune source dans le prompt : ne devrait pas arriver (le pipeline s'abstient avant)
        if match is None:
            # Réponse vide plutôt qu'une invention
            return ""

        # Texte complet de la source [1]
        extract = match.group(1)

        # Trop long : on coupe à la limite, puis au dernier espace (pas de mot coupé)
        if len(extract) > MAX_EXTRACT_LENGTH:
            # Coupe propre à la fin d'un mot
            extract = extract[:MAX_EXTRACT_LENGTH].rsplit(" ", 1)[0]

        # Extrait + citation de la source
        return f"{extract} [1]"
