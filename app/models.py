"""Structures de données partagées par les modules du RAG.

Ces classes circulent d'un module à l'autre (ingestion -> chunking -> vectorstore...).
Elles sont placées ici, dans un module commun, pour qu'aucun package n'ait besoin
d'importer un autre package uniquement pour connaître un type.
"""

# dataclass génère automatiquement __init__, __repr__ et __eq__ à partir des champs
from dataclasses import dataclass


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
        # Un document sans identifiant ne pourrait pas être retrouvé ni dédoublonné
        if not self.document_id:
            # On refuse de créer l'objet
            raise ValueError("document_id ne doit pas être vide")

        # Sans source, impossible de citer le document dans une réponse
        if not self.source:
            # On refuse de créer l'objet
            raise ValueError("source ne doit pas être vide")

        # Une page 0 ou négative signale un bug de numérotation (oubli du +1)
        if self.page_number < 1:
            # Le message indique la valeur reçue pour faciliter le débogage
            raise ValueError(f"page_number doit être >= 1 (reçu : {self.page_number})")
