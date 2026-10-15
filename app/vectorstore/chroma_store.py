"""Stockage persistant des chunks et de leurs vecteurs dans ChromaDB.

Ce module ne calcule AUCUN embedding : il reçoit des vecteurs déjà calculés
(par app/embeddings) et les range. Il ne connaît donc ni le modèle, ni le LLM.

Choix importants :
    - espace « cosine » : ChromaDB renvoie une DISTANCE cosinus d = 1 - cos(θ),
      convertie ici en SCORE de similarité s = 1 - d (plus grand = plus proche) ;
    - identifiant ChromaDB = chunk_id déterministe : réindexer le même document
      REMPLACE ses chunks (upsert) au lieu de les dupliquer ;
    - le nom du modèle d'embeddings est enregistré dans la collection : on refuse
      d'y mélanger des vecteurs d'un autre modèle.
"""

# logging pour tracer les ajouts et suppressions
import logging

# Path représente le dossier de persistance
from pathlib import Path

# Any : type des valeurs de métadonnées renvoyées par ChromaDB
from typing import Any

# chromadb : la base vectorielle (persistance sur disque, index HNSW)
import chromadb

# Les structures de données manipulées
from app.models import Chunk, SearchResult

# Logger nommé d'après le module : "app.vectorstore.chroma_store"
logger = logging.getLogger(__name__)

# Nombre maximal de chunks envoyés à ChromaDB en un seul appel (limite interne de ChromaDB)
UPSERT_BATCH_SIZE = 1000

# Clé de métadonnée de collection qui mémorise le modèle d'embeddings utilisé
EMBEDDING_MODEL_KEY = "embedding_model"


class EmbeddingModelMismatchError(RuntimeError):
    """La collection a été créée avec un autre modèle d'embeddings : il faut réindexer."""


def _chunk_metadata(chunk: Chunk) -> dict[str, str | int]:
    """Métadonnées « à plat » stockées avec chaque vecteur (pour filtrer et citer)."""
    # Uniquement des types simples : ChromaDB n'accepte pas d'objets imbriqués
    return {
        # Pour retrouver / supprimer tous les chunks d'un document
        "document_id": chunk.document_id,
        # Pour la citation
        "source": chunk.source,
        # Pour la citation
        "page_number": chunk.page_number,
        # Pour reconstruire le Chunk à l'identique
        "chunk_index": chunk.chunk_index,
    }


def _chunk_from_record(text: str, metadata: dict[str, Any]) -> Chunk:
    """Reconstruit un Chunk à partir du texte et des métadonnées stockés."""
    # Mêmes champs que ceux écrits par _chunk_metadata
    return Chunk(
        document_id=str(metadata["document_id"]),
        source=str(metadata["source"]),
        page_number=int(metadata["page_number"]),
        chunk_index=int(metadata["chunk_index"]),
        text=text,
    )


class ChromaStore:
    """Collection ChromaDB persistante dédiée aux chunks du RAG."""

    def __init__(
        self,
        persist_dir: Path,
        collection_name: str,
        embedding_model_name: str,
    ) -> None:
        """Ouvre (ou crée) la collection stockée dans ``persist_dir``."""
        # Crée le dossier de stockage s'il n'existe pas encore
        persist_dir.mkdir(parents=True, exist_ok=True)

        # Client persistant : les données survivent à l'arrêt du programme
        self._client = chromadb.PersistentClient(path=str(persist_dir))

        # Nom du modèle d'embeddings attendu dans cette collection
        self.embedding_model_name = embedding_model_name

        # Ouvre la collection, ou la crée avec l'espace cosinus et le nom du modèle
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            # Espace de distance de l'index HNSW : cosinus (vecteurs normalisés)
            configuration={"hnsw": {"space": "cosine"}},
            # Mémorise le modèle utilisé pour remplir la collection
            metadata={EMBEDDING_MODEL_KEY: embedding_model_name},
            # None : c'est NOUS qui fournissons les vecteurs (pas de modèle par défaut de Chroma)
            embedding_function=None,
        )

        # Modèle enregistré lors de la création de la collection (peut être ancien)
        stored_model = (self._collection.metadata or {}).get(EMBEDDING_MODEL_KEY)

        # Règle d'or : un seul modèle par collection
        if stored_model != embedding_model_name:
            # Mélanger deux modèles rendrait les similarités absurdes
            raise EmbeddingModelMismatchError(
                f"la collection {collection_name!r} contient des vecteurs de {stored_model!r}, "
                f"pas de {embedding_model_name!r} : supprimez-la et réindexez"
            )

    def count(self) -> int:
        """Nombre de chunks stockés."""
        # Compte les éléments de la collection
        return self._collection.count()

    def add_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """Ajoute (ou remplace) des chunks et leurs vecteurs.

        ``upsert`` = update + insert : un chunk_id déjà présent est remplacé.
        """
        # Un vecteur par chunk, dans le même ordre : sinon les associations seraient fausses
        if len(chunks) != len(embeddings):
            # Erreur explicite plutôt qu'un index incohérent
            raise ValueError(
                f"{len(chunks)} chunk(s) mais {len(embeddings)} vecteur(s)"
            )

        # Envoie les chunks par lots pour respecter la limite de ChromaDB
        for start in range(0, len(chunks), UPSERT_BATCH_SIZE):
            # Tranche de chunks et de vecteurs correspondants
            batch = chunks[start : start + UPSERT_BATCH_SIZE]
            batch_embeddings = embeddings[start : start + UPSERT_BATCH_SIZE]

            # Ajoute ou remplace le lot
            self._collection.upsert(
                # Identifiants déterministes : pas de doublon en cas de réindexation
                ids=[chunk.chunk_id for chunk in batch],
                # Les vecteurs calculés par EmbeddingModel
                embeddings=batch_embeddings,
                # Le texte, renvoyé tel quel lors d'une recherche
                documents=[chunk.text for chunk in batch],
                # L'origine de chaque chunk
                metadatas=[_chunk_metadata(chunk) for chunk in batch],
            )

        # Trace l'opération
        logger.info("%d chunk(s) indexé(s) ; total : %d", len(chunks), self.count())

    def search(self, query_embedding: list[float], top_k: int) -> list[SearchResult]:
        """Renvoie les ``top_k`` chunks les plus proches du vecteur de la question."""
        # Un top_k nul ou négatif n'a pas de sens
        if top_k <= 0:
            # Erreur explicite
            raise ValueError(f"top_k doit être > 0 (reçu : {top_k})")

        # Collection vide : rien à chercher (ChromaDB lèverait une erreur)
        if self.count() == 0:
            # Aucun résultat
            return []

        # Recherche des plus proches voisins dans l'index HNSW
        response = self._collection.query(
            # Une seule question à la fois
            query_embeddings=[query_embedding],
            # On ne peut pas demander plus de résultats qu'il n'y a de chunks
            n_results=min(top_k, self.count()),
            # Ce qu'on veut récupérer (les vecteurs eux-mêmes sont inutiles ici)
            include=["documents", "metadatas", "distances"],
        )

        # Les réponses sont des listes de listes (une par question) : on prend la première
        texts = (response["documents"] or [[]])[0]
        metadatas = (response["metadatas"] or [[]])[0]
        distances = (response["distances"] or [[]])[0]

        # Reconstruit les résultats, déjà triés du plus proche au plus lointain
        return [
            # score = 1 - distance cosinus = similarité cosinus
            SearchResult(
                chunk=_chunk_from_record(text, dict(meta)), score=1.0 - distance
            )
            for text, meta, distance in zip(texts, metadatas, distances, strict=True)
        ]

    def has_document(self, document_id: str) -> bool:
        """Indique si au moins un chunk de ce document est déjà indexé."""
        # Cherche un seul chunk portant ce document_id (filtre sur les métadonnées)
        found = self._collection.get(where={"document_id": document_id}, limit=1)

        # Présent si la liste d'identifiants n'est pas vide
        return bool(found["ids"])

    def delete_document(self, document_id: str) -> int:
        """Supprime tous les chunks d'un document ; renvoie le nombre supprimé."""
        # Identifiants des chunks de ce document
        ids = self._collection.get(where={"document_id": document_id})["ids"]

        # Supprime seulement s'il y a quelque chose à supprimer
        if ids:
            # Suppression par identifiants
            self._collection.delete(ids=ids)

        # Trace l'opération
        logger.info("Document %s : %d chunk(s) supprimé(s)", document_id, len(ids))

        # Renvoie le nombre de chunks supprimés
        return len(ids)

    def list_documents(self) -> list[dict[str, str | int]]:
        """Liste les documents indexés : id, nom de fichier et nombre de chunks."""
        # Lit toutes les métadonnées (suffisant pour quelques milliers de chunks)
        metadatas = self._collection.get(include=["metadatas"])["metadatas"] or []

        # Regroupe par document : document_id -> {source, nombre de chunks}
        documents: dict[str, dict[str, str | int]] = {}

        # Compte les chunks de chaque document
        for meta in metadatas:
            # Identifiant du document de ce chunk
            document_id = str(meta["document_id"])

            # Première rencontre : crée l'entrée du document
            entry = documents.setdefault(
                document_id,
                {
                    "document_id": document_id,
                    "source": str(meta["source"]),
                    "chunk_count": 0,
                },
            )

            # Un chunk de plus pour ce document
            entry["chunk_count"] = int(entry["chunk_count"]) + 1

        # Trie par nom de fichier pour un affichage stable
        return sorted(documents.values(), key=lambda doc: str(doc["source"]))
