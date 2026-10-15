"""Découpage des pages nettoyées en chunks (passages).

Chaque page est découpée SÉPARÉMENT : un chunk n'appartient qu'à une seule page,
ce qui garde exacte la citation « p. N ».

Stratégies :
    - "fixed" (étape 3.3) : fenêtres de taille fixe, avancées de ``size - overlap``.
    - "sentence" (étape 3.4) : à venir.

Ce module ne lit ni la configuration ni aucun fichier : il reçoit les paramètres
explicitement, ce qui le rend simple à tester avec n'importe quelles valeurs.
"""

# logging pour tracer le nombre de chunks produits par page
import logging

# Les structures de données manipulées : une page en entrée, des chunks en sortie
from app.models import Chunk, DocumentPage

# Logger nommé d'après le module : "app.ingestion.chunker"
logger = logging.getLogger(__name__)


def _validate_chunk_params(chunk_size: int, chunk_overlap: int) -> None:
    """Refuse les paramètres qui rendraient le découpage impossible ou infini."""
    # Une taille nulle ou négative ne produirait aucun texte
    if chunk_size <= 0:
        # Le message indique la valeur reçue pour faciliter le débogage
        raise ValueError(f"chunk_size doit être > 0 (reçu : {chunk_size})")

    # Un chevauchement négatif n'a pas de sens
    if chunk_overlap < 0:
        # Le message indique la valeur reçue
        raise ValueError(f"chunk_overlap doit être >= 0 (reçu : {chunk_overlap})")

    # Si overlap >= size, le pas (size - overlap) vaut 0 ou moins : la boucle ne finirait jamais
    if chunk_overlap >= chunk_size:
        # On refuse plutôt que de tourner indéfiniment
        raise ValueError(
            f"chunk_overlap ({chunk_overlap}) doit être < chunk_size ({chunk_size})"
        )


def split_text_fixed(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Découpe un texte en fenêtres de ``chunk_size`` caractères qui se chevauchent.

    Chaque fenêtre commence ``chunk_size - chunk_overlap`` caractères après la
    précédente. La dernière fenêtre peut être plus courte. Les coupures tombent
    n'importe où, y compris au milieu d'un mot : c'est la stratégie de référence,
    volontairement naïve.

    Exemple : 1 000 caractères, size=400, overlap=100
    → fenêtres [0, 400), [300, 700), [600, 1000).
    """
    # On vérifie les paramètres AVANT la boucle, pour éviter une boucle infinie
    _validate_chunk_params(chunk_size, chunk_overlap)

    # Un texte vide ne produit aucun morceau
    if not text:
        # Liste vide plutôt qu'un morceau vide
        return []

    # Le pas : de combien de caractères on avance entre deux débuts de fenêtre
    step = chunk_size - chunk_overlap

    # Liste des morceaux produits
    pieces: list[str] = []

    # Position du début de la fenêtre courante
    start = 0

    # On produit des fenêtres jusqu'à atteindre la fin du texte
    while True:
        # Fin de la fenêtre (exclue), comme dans text[start:end]
        end = start + chunk_size

        # Le slicing Python s'arrête de lui-même à la fin du texte : pas d'IndexError
        pieces.append(text[start:end])

        # Si cette fenêtre atteint la fin du texte, le découpage est terminé
        if end >= len(text):
            # Sans ce test, on créerait une fenêtre de plus, entièrement contenue dans la précédente
            break

        # On avance d'un pas : les chunk_overlap derniers caractères seront repris
        start += step

    # Renvoie les morceaux dans l'ordre du texte
    return pieces


def chunk_page_fixed(
    page: DocumentPage, chunk_size: int, chunk_overlap: int
) -> list[Chunk]:
    """Découpe une page avec la stratégie "fixed" et renvoie des Chunk avec leurs métadonnées."""
    # Découpe le texte brut de la page en morceaux
    pieces = split_text_fixed(page.text, chunk_size, chunk_overlap)

    # Liste des chunks produits pour cette page
    chunks: list[Chunk] = []

    # Parcourt les morceaux non vides ; on ne numérote que ceux qu'on garde
    for piece in pieces:
        # Un morceau fait uniquement d'espaces serait refusé par Chunk : on l'ignore
        if not piece.strip():
            # Passe au morceau suivant
            continue

        # Crée le chunk en recopiant l'origine de la page (pour la citation)
        chunk = Chunk(
            # Même document que la page
            document_id=page.document_id,
            # Même fichier source
            source=page.source,
            # Même numéro de page
            page_number=page.page_number,
            # Position dans la page : 0, 1, 2... (= nombre de chunks déjà créés)
            chunk_index=len(chunks),
            # Texte du passage
            text=piece,
        )

        # Ajoute le chunk à la liste
        chunks.append(chunk)

    # Trace en DEBUG (détail, masqué au niveau INFO par défaut)
    logger.debug(
        "%s p.%d : %d caractère(s) → %d chunk(s)",
        page.source,
        page.page_number,
        len(page.text),
        len(chunks),
    )

    # Renvoie les chunks de la page, dans l'ordre
    return chunks
