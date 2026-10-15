"""Recherche sémantique : question → chunks les plus pertinents.

Le retriever est INDÉPENDANT du LLM (règle 6.5 de CLAUDE.md) : il ne fait que
vectoriser la question avec le même modèle que l'indexation, interroger la base
vectorielle et filtrer les résultats trop peu similaires.
"""

# logging pour tracer chaque recherche (en DEBUG)
import logging

# Vectorisation de la question (préfixe "query: " ajouté par le modèle)
from app.embeddings.embedding_model import EmbeddingModel

# Structure renvoyée
from app.models import SearchResult

# Base vectorielle interrogée
from app.vectorstore.chroma_store import ChromaStore

# Logger nommé d'après le module : "app.retrieval.retriever"
logger = logging.getLogger(__name__)


class Retriever:
    """Recherche sémantique Top-K avec seuil de score optionnel."""

    def __init__(
        self,
        embedder: EmbeddingModel,
        store: ChromaStore,
        top_k: int,
        min_score: float = 0.0,
    ) -> None:
        """Reçoit le modèle d'embeddings et la base vectorielle déjà construits."""
        # Top-K doit être strictement positif
        if top_k <= 0:
            # Erreur explicite
            raise ValueError(f"top_k doit être > 0 (reçu : {top_k})")

        # Le MÊME modèle que celui qui a indexé les chunks
        self.embedder = embedder

        # La base vectorielle à interroger
        self.store = store

        # Nombre de chunks renvoyés par défaut
        self.top_k = top_k

        # Score minimal : un chunk moins similaire est écarté (0.0 = aucun filtre)
        self.min_score = min_score

    def retrieve(self, question: str, top_k: int | None = None) -> list[SearchResult]:
        """Renvoie au plus ``top_k`` chunks, du plus au moins similaire, au-dessus de ``min_score``."""
        # top_k explicite, sinon la valeur par défaut du retriever
        k = top_k if top_k is not None else self.top_k

        # Vectorise la question (lève ValueError si elle est vide)
        query_vector = self.embedder.embed_query(question)

        # Les k plus proches voisins dans la base
        results = self.store.search(query_vector, k)

        # Écarte les résultats sous le seuil de similarité
        kept = [result for result in results if result.score >= self.min_score]

        # Trace en DEBUG : utile pour comprendre une mauvaise réponse
        logger.debug(
            "Question %r : %d résultat(s), %d gardé(s) (seuil %.3f), scores %s",
            question,
            len(results),
            len(kept),
            self.min_score,
            [round(result.score, 3) for result in results],
        )

        # Résultats triés du plus au moins similaire (ordre de ChromaDB)
        return kept
