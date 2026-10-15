"""Structures de données partagées par les modules du RAG.

Ces classes circulent d'un module à l'autre (ingestion -> chunking -> vectorstore...).
Elles sont placées ici, dans un module commun, pour qu'aucun package n'ait besoin
d'importer un autre package uniquement pour connaître un type.
"""

# dataclass génère automatiquement __init__, __repr__ et __eq__ à partir des champs
from dataclasses import dataclass


def _validate_origin(document_id: str, source: str, page_number: int) -> None:
    """Vérifie les informations d'origine communes à DocumentPage et Chunk."""
    # Un document sans identifiant ne pourrait pas être retrouvé ni dédoublonné
    if not document_id:
        # On refuse de créer l'objet
        raise ValueError("document_id ne doit pas être vide")

    # Sans source, impossible de citer le document dans une réponse
    if not source:
        # On refuse de créer l'objet
        raise ValueError("source ne doit pas être vide")

    # Une page 0 ou négative signale un bug de numérotation (oubli du +1)
    if page_number < 1:
        # Le message indique la valeur reçue pour faciliter le débogage
        raise ValueError(f"page_number doit être >= 1 (reçu : {page_number})")


# frozen=True rend l'objet immuable : impossible de modifier un champ après sa création
@dataclass(frozen=True)
class DocumentPage:
    """Le texte d'une page d'un document, avec de quoi retrouver son origine."""

    # Identifiant stable du document (calculé à partir du contenu du fichier en 2.3)
    document_id: str

    # Nom du fichier d'origine, ex. "01_introduction_rag.pdf" (affiché dans les citations)
    source: str

    # Numéro de page tel qu'un humain le lit : la première page vaut 1 (et pas 0)
    page_number: int

    # Texte de la page (brut après extraction, puis nettoyé en 2.4)
    text: str

    # Méthode appelée automatiquement juste après __init__ : on y vérifie les valeurs
    def __post_init__(self) -> None:
        # Vérifie document_id, source et page_number (règles communes avec Chunk)
        _validate_origin(self.document_id, self.source, self.page_number)


# frozen=True : un chunk ne doit pas être modifié une fois créé (il sera vectorisé puis stocké)
@dataclass(frozen=True)
class Chunk:
    """Un passage de texte issu d'une page : l'unité vectorisée, stockée, retrouvée et citée."""

    # Identifiant du document d'origine (le même que celui de la DocumentPage)
    document_id: str

    # Nom du fichier d'origine (pour la citation)
    source: str

    # Page d'origine, numérotée à partir de 1 (un chunk ne traverse jamais deux pages)
    page_number: int

    # Position du chunk dans sa page : 0 pour le premier, 1 pour le suivant...
    chunk_index: int

    # Texte du passage
    text: str

    # Méthode appelée automatiquement juste après __init__ : on y vérifie les valeurs
    def __post_init__(self) -> None:
        # Vérifie document_id, source et page_number (règles communes avec DocumentPage)
        _validate_origin(self.document_id, self.source, self.page_number)

        # Un index négatif signale un bug de numérotation
        if self.chunk_index < 0:
            # Le message indique la valeur reçue pour faciliter le débogage
            raise ValueError(f"chunk_index doit être >= 0 (reçu : {self.chunk_index})")

        # Un chunk vide ou fait uniquement d'espaces n'apporterait rien à la recherche
        if not self.text.strip():
            # On refuse de créer l'objet
            raise ValueError("text ne doit pas être vide")

    # @property : chunk_id s'utilise comme un attribut (chunk.chunk_id), mais il est CALCULÉ
    @property
    def chunk_id(self) -> str:
        """Identifiant unique et stable du chunk, ex. "49289fd3ade5e236-p1-c0"."""
        # Calculé à partir des autres champs : impossible qu'il soit incohérent avec eux
        return f"{self.document_id}-p{self.page_number}-c{self.chunk_index}"

    @property
    def citation(self) -> str:
        """Référence lisible par un humain, ex. "01_introduction_rag.pdf, p. 1"."""
        # Nom du fichier et numéro de page : ce que l'utilisateur peut vérifier lui-même
        return f"{self.source}, p. {self.page_number}"


# frozen=True : un résultat de recherche ne doit pas être modifié après coup
@dataclass(frozen=True)
class SearchResult:
    """Un chunk retrouvé pour une question, avec son score de similarité."""

    # Le chunk retrouvé (texte + origine, pour la citation)
    chunk: Chunk

    # Similarité cosinus avec la question : plus c'est grand, plus c'est proche (max 1)
    score: float
