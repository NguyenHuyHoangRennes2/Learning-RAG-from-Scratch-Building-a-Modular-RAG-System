"""Découpage des pages nettoyées en chunks (passages).

Chaque page est découpée SÉPARÉMENT : un chunk n'appartient qu'à une seule page,
ce qui garde exacte la citation « p. N ».

Stratégies :
    - "fixed" (étape 3.3) : fenêtres de taille fixe, avancées de ``size - overlap``.
    - "sentence" (étape 3.4) : phrases entières regroupées jusqu'à ``size``.

Ce module n'appelle pas ``get_settings()`` et ne lit aucun fichier : il reçoit les
paramètres explicitement, ce qui le rend simple à tester avec n'importe quelles valeurs.
"""

# logging pour tracer le nombre de chunks produits
import logging

# re : expressions régulières, pour repérer les fins de phrase
import re

# Callable : le type « fonction », pour la table des stratégies
from collections.abc import Callable

# Le type des stratégies autorisées ("fixed" ou "sentence"), défini une seule fois dans la config
from app.core.config import ChunkStrategy

# Détection des titres numérotés (même règle que pour le nettoyage, étape 2.4)
from app.ingestion.text_cleaner import is_heading

# Les structures de données manipulées : des pages en entrée, des chunks en sortie
from app.models import Chunk, DocumentPage

# Logger nommé d'après le module : "app.ingestion.chunker"
logger = logging.getLogger(__name__)

# Fin de phrase = espaces précédés de . ! ? ou … ET suivis d'une majuscule (ou « " ( ).
# (?<!\d\.) exclut "1. Définition" : un chiffre suivi d'un point est un numéro de titre.
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?…])(?<!\d\.)\s+(?=[A-ZÀ-Ý«\"(])")

# Séparateur utilisé pour recoller les phrases d'un même chunk
SENTENCE_SEPARATOR = " "


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


# --- Stratégie "fixed" (étape 3.3) ---


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


# --- Stratégie "sentence" (étape 3.4) ---


def split_sentences(text: str) -> list[str]:
    """Découpe un texte en phrases (et en titres, qui sont sur leur propre ligne).

    Exemple : "1. Titre\\nPhrase un. Phrase deux." → ["1. Titre", "Phrase un.", "Phrase deux."]
    """
    # Liste des phrases trouvées
    sentences: list[str] = []

    # Après le nettoyage (2.4), un saut de ligne sépare deux paragraphes ou un titre de son texte
    for line in text.split("\n"):
        # Coupe la ligne à chaque fin de phrase repérée par l'expression régulière
        for sentence in SENTENCE_BOUNDARY.split(line):
            # Retire les espaces au début et à la fin de la phrase
            sentence = sentence.strip()

            # Ignore les morceaux vides (lignes blanches)
            if sentence:
                # Garde la phrase
                sentences.append(sentence)

    # Renvoie les phrases dans l'ordre du texte
    return sentences


def attach_headings(sentences: list[str]) -> list[str]:
    """Colle chaque titre numéroté à la phrase qui le suit (évite les titres orphelins).

    Exemple : ["1. Titre", "Phrase un.", "Phrase deux."] → ["1. Titre Phrase un.", "Phrase deux."]
    Sans cela, un titre pouvait terminer un chunk alors que son contenu était dans le suivant
    (mesuré à l'étape 3.5 : 1 chunk sur 15 avec 800/150).
    """
    # Phrases après regroupement
    units: list[str] = []

    # Titre(s) en attente de la phrase qui suit
    pending_headings: list[str] = []

    # Parcourt les phrases dans l'ordre
    for sentence in sentences:
        # Un titre est mis de côté : il sera collé à la prochaine phrase
        if is_heading(sentence):
            # Plusieurs titres consécutifs ("1. Partie" puis "1.1. Section") restent ensemble
            pending_headings.append(sentence)

            # Passe à la phrase suivante
            continue

        # Phrase normale : on lui colle les titres en attente (s'il y en a)
        units.append(SENTENCE_SEPARATOR.join([*pending_headings, sentence]))

        # Les titres sont consommés
        pending_headings = []

    # Titre(s) en toute fin de texte, sans phrase après : on les garde quand même
    if pending_headings:
        # Rien n'est perdu
        units.append(SENTENCE_SEPARATOR.join(pending_headings))

    # Renvoie les unités dans l'ordre du texte
    return units


def _joined_length(sentences: list[str]) -> int:
    """Longueur du texte obtenu en recollant les phrases avec SENTENCE_SEPARATOR."""
    # Aucune phrase : texte vide
    if not sentences:
        # Longueur nulle
        return 0

    # Somme des phrases + un séparateur entre chaque paire de phrases voisines
    return sum(len(sentence) for sentence in sentences) + len(SENTENCE_SEPARATOR) * (
        len(sentences) - 1
    )


def _overlap_tail(sentences: list[str], chunk_overlap: int) -> list[str]:
    """Dernières phrases entières d'un chunk dont la longueur totale tient dans ``chunk_overlap``.

    Le chevauchement se fait par phrases entières : si la dernière phrase est plus
    longue que ``chunk_overlap``, aucune phrase n'est reprise.
    """
    # Phrases reprises, dans l'ordre du texte
    tail: list[str] = []

    # On remonte depuis la dernière phrase du chunk
    for sentence in reversed(sentences):
        # Si ajouter cette phrase dépasse le chevauchement autorisé, on s'arrête
        if _joined_length([sentence, *tail]) > chunk_overlap:
            # Les phrases plus anciennes ne seront pas reprises non plus
            break

        # Ajoute la phrase au DÉBUT, pour garder l'ordre du texte
        tail.insert(0, sentence)

    # Renvoie les phrases à reprendre au début du chunk suivant
    return tail


def split_text_sentence(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Regroupe des phrases entières en morceaux d'au plus ``chunk_size`` caractères.

    - Les phrases sont ajoutées une à une tant que le morceau ne dépasse pas ``chunk_size``.
    - Le morceau suivant commence par les dernières phrases du précédent, dans la
      limite de ``chunk_overlap`` caractères (chevauchement par phrases entières).
    - Une phrase plus longue que ``chunk_size`` est découpée avec la stratégie "fixed".
    """
    # Mêmes règles de validation que la stratégie "fixed"
    _validate_chunk_params(chunk_size, chunk_overlap)

    # Morceaux terminés
    pieces: list[str] = []

    # Phrases du morceau en cours de construction
    current: list[str] = []

    # Parcourt les phrases dans l'ordre du texte (chaque titre est collé à la phrase suivante)
    for sentence in attach_headings(split_sentences(text)):
        # Cas rare : une phrase seule dépasse déjà la taille maximale
        if len(sentence) > chunk_size:
            # On termine d'abord le morceau en cours, s'il contient quelque chose
            if current:
                # Recolle ses phrases et l'enregistre
                pieces.append(SENTENCE_SEPARATOR.join(current))

            # La phrase géante est coupée en fenêtres fixes (seul cas où l'on coupe une phrase)
            pieces.extend(split_text_fixed(sentence, chunk_size, chunk_overlap))

            # Le morceau suivant repart de zéro
            current = []

            # Passe à la phrase suivante
            continue

        # Si ajouter cette phrase ferait dépasser la taille, le morceau en cours est terminé
        if current and _joined_length([*current, sentence]) > chunk_size:
            # Recolle ses phrases et l'enregistre
            pieces.append(SENTENCE_SEPARATOR.join(current))

            # Le nouveau morceau commence par les dernières phrases du précédent (chevauchement)
            current = _overlap_tail(current, chunk_overlap)

            # Si le chevauchement + la nouvelle phrase dépassent encore la taille...
            while current and _joined_length([*current, sentence]) > chunk_size:
                # ...on retire la phrase reprise la plus ancienne
                current.pop(0)

        # Ajoute la phrase au morceau en cours
        current.append(sentence)

    # Le dernier morceau n'a pas encore été enregistré
    if current:
        # Recolle ses phrases et l'enregistre
        pieces.append(SENTENCE_SEPARATOR.join(current))

    # Renvoie les morceaux dans l'ordre du texte
    return pieces


# --- Point d'entrée commun aux deux stratégies ---

# Table « nom de stratégie → fonction de découpage » : ajouter une stratégie = ajouter une ligne
SPLITTERS: dict[ChunkStrategy, Callable[[str, int, int], list[str]]] = {
    # Fenêtres de taille fixe (étape 3.3)
    "fixed": split_text_fixed,
    # Phrases entières regroupées (étape 3.4)
    "sentence": split_text_sentence,
}


def chunk_page(
    page: DocumentPage,
    chunk_size: int,
    chunk_overlap: int,
    strategy: ChunkStrategy,
) -> list[Chunk]:
    """Découpe une page avec la stratégie choisie et renvoie des Chunk avec leurs métadonnées."""
    # Une stratégie inconnue est refusée avec un message clair (plutôt qu'un KeyError obscur)
    if strategy not in SPLITTERS:
        # Le message liste les stratégies disponibles
        raise ValueError(
            f"stratégie inconnue : {strategy!r} (disponibles : {sorted(SPLITTERS)})"
        )

    # Découpe le texte de la page avec la fonction de la stratégie choisie
    pieces = SPLITTERS[strategy](page.text, chunk_size, chunk_overlap)

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
        "%s p.%d [%s] : %d caractère(s) → %d chunk(s)",
        page.source,
        page.page_number,
        strategy,
        len(page.text),
        len(chunks),
    )

    # Renvoie les chunks de la page, dans l'ordre
    return chunks


def chunk_pages(
    pages: list[DocumentPage],
    chunk_size: int,
    chunk_overlap: int,
    strategy: ChunkStrategy,
) -> list[Chunk]:
    """Découpe une liste de pages, page par page, et renvoie tous les chunks."""
    # Tous les chunks de toutes les pages
    chunks: list[Chunk] = []

    # Chaque page est découpée séparément : un chunk ne traverse jamais deux pages
    for page in pages:
        # Ajoute les chunks de cette page à la liste globale
        chunks.extend(chunk_page(page, chunk_size, chunk_overlap, strategy))

    # Résumé en INFO : visible par défaut
    logger.info(
        "%d page(s) → %d chunk(s) (stratégie %s, size=%d, overlap=%d)",
        len(pages),
        len(chunks),
        strategy,
        chunk_size,
        chunk_overlap,
    )

    # Renvoie les chunks dans l'ordre des pages
    return chunks
