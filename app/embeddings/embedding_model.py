"""Transformation de textes en vecteurs (embeddings) avec Sentence Transformers.

Règle d'or du RAG : le MÊME modèle doit vectoriser les chunks (indexation) et les
questions (recherche). Sinon, les vecteurs ne vivent pas dans le même espace et la
similarité n'a plus de sens.

Modèle par défaut : ``intfloat/multilingual-e5-small``
    - 384 dimensions, 512 tokens maximum, multilingue (français compris) ;
    - entraîné avec des PRÉFIXES : "query: " pour les questions, "passage: " pour les
      documents. Les oublier dégrade la recherche ; ce module les ajoute lui-même.

Les vecteurs sont NORMALISÉS (norme = 1) : la similarité cosinus devient alors un
simple produit scalaire.
"""

# logging pour tracer le chargement du modèle (lent : plusieurs secondes)
import logging

# math.sqrt pour calculer la norme d'un vecteur
import math

# Sequence : tout ce qui se parcourt comme une liste (liste, tuple, tableau numpy...)
from collections.abc import Sequence

# Protocol : décrit une « forme » d'objet attendue, sans imposer d'héritage
from typing import Any, Protocol

# Logger nommé d'après le module : "app.embeddings.embedding_model"
logger = logging.getLogger(__name__)

# Préfixes attendus par les modèles de la famille E5 (questions / documents)
E5_QUERY_PREFIX = "query: "
E5_DOCUMENT_PREFIX = "passage: "


class TextEncoder(Protocol):
    """Ce dont EmbeddingModel a besoin : un objet qui sait encoder des textes.

    SentenceTransformer respecte cette forme. En test, on fournit un faux encodeur
    minuscule et rapide, sans télécharger de modèle.
    """

    def encode(self, sentences: list[str], **kwargs: Any) -> Any:
        """Renvoie un vecteur par texte (tableau numpy de forme [n, dimension])."""
        ...

    def get_embedding_dimension(self) -> int | None:
        """Renvoie la dimension des vecteurs produits."""
        ...


def prefixes_for_model(model_name: str) -> tuple[str, str]:
    """Renvoie les préfixes (question, document) adaptés au modèle.

    Les modèles E5 ont été entraînés avec "query: " / "passage: ". Les autres
    (ex. paraphrase-multilingual-MiniLM) n'en utilisent pas.
    """
    # Le nom du modèle contient "e5" (ex. "intfloat/multilingual-e5-small")
    if "e5" in model_name.lower():
        # Préfixes de la famille E5
        return E5_QUERY_PREFIX, E5_DOCUMENT_PREFIX

    # Aucun préfixe pour les autres modèles
    return "", ""


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Similarité cosinus entre deux vecteurs : cos(θ) = (a · b) / (‖a‖ × ‖b‖).

    Vaut 1 si les vecteurs pointent dans la même direction, 0 s'ils sont
    orthogonaux (sans rapport), -1 s'ils sont opposés.
    """
    # Deux vecteurs de tailles différentes ne sont pas comparables
    if len(a) != len(b):
        # Erreur explicite plutôt qu'un résultat faux
        raise ValueError(f"dimensions différentes : {len(a)} et {len(b)}")

    # Produit scalaire : somme des produits composante par composante
    dot = sum(x * y for x, y in zip(a, b, strict=True))

    # Norme (longueur) de chaque vecteur : racine de la somme des carrés
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    # Un vecteur nul n'a pas de direction : la similarité n'est pas définie
    if norm_a == 0 or norm_b == 0:
        # Erreur explicite plutôt qu'une division par zéro
        raise ValueError("la similarité cosinus n'est pas définie pour un vecteur nul")

    # Produit scalaire divisé par le produit des normes
    return dot / (norm_a * norm_b)


class EmbeddingModel:
    """Vectorise des documents (chunks) et des questions avec le même modèle."""

    def __init__(
        self,
        model_name: str,
        device: str = "cpu",
        batch_size: int = 32,
        encoder: TextEncoder | None = None,
    ) -> None:
        """Prépare le modèle SANS le charger (chargement paresseux, au premier usage).

        ``encoder`` permet d'injecter un encodeur déjà prêt (ex. un faux encodeur en test).
        """
        # Nom du modèle Hugging Face (sert aussi à choisir les préfixes)
        self.model_name = model_name

        # Matériel de calcul ("cpu" ou "cuda")
        self.device = device

        # Nombre de textes encodés en une passe
        self.batch_size = batch_size

        # Encodeur : None tant que le vrai modèle n'est pas chargé
        self._encoder = encoder

        # Préfixes à ajouter devant les questions et les documents
        self.query_prefix, self.document_prefix = prefixes_for_model(model_name)

    def _get_encoder(self) -> TextEncoder:
        """Renvoie l'encodeur, en chargeant le vrai modèle au premier appel."""
        # Déjà chargé (ou injecté) : on le réutilise
        if self._encoder is not None:
            # Pas de rechargement
            return self._encoder

        # Import ici : sentence_transformers (et PyTorch) mettent plusieurs secondes à s'importer
        from sentence_transformers import SentenceTransformer

        # Trace le chargement (téléchargé depuis Hugging Face au tout premier lancement)
        logger.info(
            "Chargement du modèle d'embeddings %s (%s)...", self.model_name, self.device
        )

        # Charge le modèle (depuis le cache local après le premier téléchargement)
        self._encoder = SentenceTransformer(self.model_name, device=self.device)

        # Renvoie le modèle chargé
        return self._encoder

    @property
    def dimension(self) -> int:
        """Nombre de composantes de chaque vecteur (384 pour multilingual-e5-small)."""
        # Demande la dimension au modèle
        dimension = self._get_encoder().get_embedding_dimension()

        # Certains modèles ne la déclarent pas : on refuse plutôt que de deviner
        if dimension is None:
            # Erreur explicite
            raise RuntimeError(f"dimension inconnue pour le modèle {self.model_name}")

        # Renvoie la dimension
        return int(dimension)

    def _encode(self, texts: list[str]) -> list[list[float]]:
        """Encode des textes (déjà préfixés) en vecteurs normalisés."""
        # Encode par lots ; normalize_embeddings=True ramène chaque vecteur à une norme de 1
        vectors = self._get_encoder().encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        # Convertit le tableau numpy en listes Python simples (format accepté partout)
        return [[float(value) for value in vector] for vector in vectors]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Vectorise des passages à indexer (ajoute le préfixe "passage: " pour E5)."""
        # Rien à encoder : on évite de charger le modèle pour rien
        if not texts:
            # Liste vide
            return []

        # Ajoute le préfixe document devant chaque texte
        prefixed = [f"{self.document_prefix}{text}" for text in texts]

        # Encode et renvoie un vecteur par texte, dans le même ordre
        return self._encode(prefixed)

    def embed_query(self, question: str) -> list[float]:
        """Vectorise une question (ajoute le préfixe "query: " pour E5)."""
        # Une question vide ne peut rien retrouver
        if not question.strip():
            # Erreur explicite
            raise ValueError("la question ne doit pas être vide")

        # Encode la question préfixée et renvoie son unique vecteur
        return self._encode([f"{self.query_prefix}{question}"])[0]
