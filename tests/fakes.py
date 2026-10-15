"""Faux composants partagés par plusieurs fichiers de tests.

Ils remplacent les composants lents ou externes (modèle d'embeddings, LLM) par
des versions minuscules, rapides et PRÉVISIBLES.
"""

# Any : type des arguments nommés acceptés par encode()
from typing import Any

# Petit vocabulaire : chaque mot correspond à une dimension du faux vecteur
VOCABULARY = (
    "rag",
    "embeddings",
    "vecteurs",
    "chunk",
    "pdf",
    "llm",
    "évaluation",
    "cosinus",
)


class KeywordEncoder:
    """Faux modèle d'embeddings : une dimension par mot du vocabulaire.

    Le vecteur d'un texte compte les mots du vocabulaire qu'il contient (+ une
    petite constante pour ne jamais produire de vecteur nul). Deux textes qui
    partagent des mots-clés sont donc « proches » : les résultats d'une recherche
    se prévoient à la main.
    """

    def encode(self, sentences: list[str], **kwargs: Any) -> list[list[float]]:
        # Un vecteur par texte
        vectors: list[list[float]] = []

        # Calcule le vecteur de chaque texte
        for sentence in sentences:
            # Mots en minuscules, ponctuation simple retirée
            words = sentence.lower().replace(".", " ").replace("?", " ").split()

            # Nombre d'occurrences de chaque mot du vocabulaire (+ 0.01 : jamais de vecteur nul)
            vector = [words.count(term) + 0.01 for term in VOCABULARY]

            # Normalise (norme = 1), comme le vrai modèle avec normalize_embeddings=True
            norm = sum(v * v for v in vector) ** 0.5
            vectors.append([v / norm for v in vector])

        # Renvoie les vecteurs dans l'ordre des textes
        return vectors

    def get_embedding_dimension(self) -> int:
        # Une dimension par mot du vocabulaire
        return len(VOCABULARY)
