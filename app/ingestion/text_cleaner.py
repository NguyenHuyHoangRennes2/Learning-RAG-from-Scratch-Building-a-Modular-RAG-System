"""Nettoyage du texte extrait des PDF.

Deux niveaux de nettoyage :
    1. Par DOCUMENT : retirer les en-têtes / pieds de page répétés sur toutes les pages.
    2. Par PAGE : normaliser les caractères, recoller les lignes coupées par la mise en page.

Ce module ne lit aucun fichier : il reçoit des DocumentPage et en renvoie de nouvelles.
"""

# logging pour tracer le nettoyage (lignes retirées, pages devenues vides)
import logging

# re : expressions régulières, pour reconnaître des motifs dans le texte (titres, chiffres, espaces)
import re

# unicodedata : normalisation Unicode (ligatures, espaces insécables...)
import unicodedata

# replace crée une copie modifiée d'une DocumentPage (qui est immuable)
from dataclasses import replace

# La structure de données manipulée (étape 2.2)
from app.models import DocumentPage

# Logger nommé d'après le module : "app.ingestion.text_cleaner"
logger = logging.getLogger(__name__)

# Nombre de lignes examinées en haut ET en bas de chaque page pour trouver les en-têtes/pieds de page
HEADER_FOOTER_ZONE = 3

# Caractères qui terminent une phrase : après eux, un saut de ligne est un vrai changement de paragraphe
SENTENCE_ENDINGS = (".", "!", "?", ":", "»")

# Un titre numéroté ressemble à "1. Définition" ou "2.3. Titre" : chiffres, point, espace, majuscule
HEADING_PATTERN = re.compile(r"^\d+(?:\.\d+)*\.\s+[A-ZÀ-Ý]")

# Au-delà de cette longueur, une ligne qui commence par "1. " est plutôt un paragraphe qu'un titre
MAX_HEADING_LENGTH = 80

# Table de remplacement des apostrophes typographiques par l'apostrophe simple du clavier
APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'"})

# Suite d'espaces ou de tabulations (pour les réduire à un seul espace)
MULTIPLE_SPACES = re.compile(r"[ \t]+")

# Suite de chiffres (pour comparer "Page 1" et "Page 2" comme la même ligne "Page #")
DIGITS = re.compile(r"\d+")


def normalize_unicode(text: str) -> str:
    """Uniformise les caractères : ligatures, espaces spéciaux, apostrophes."""
    # NFKC décompose les caractères « décoratifs » : la ligature "ﬁ" devient "fi", l'espace insécable devient " "
    text = unicodedata.normalize("NFKC", text)

    # Remplace les apostrophes typographiques (’ ‘) par l'apostrophe simple (')
    return text.translate(APOSTROPHES)


def _is_heading(line: str) -> bool:
    """Indique si une ligne ressemble à un titre de section numéroté."""
    # Un titre est court ET commence par une numérotation suivie d'une majuscule
    return len(line) <= MAX_HEADING_LENGTH and bool(HEADING_PATTERN.match(line))


def _is_paragraph_break(previous: str, current: str) -> bool:
    """Décide si le saut de ligne entre deux lignes est un VRAI changement de paragraphe."""
    # La ligne précédente finit une phrase : le saut de ligne est un vrai changement de paragraphe
    if previous.endswith(SENTENCE_ENDINGS):
        # On garde le saut de ligne
        return True

    # Un titre reste seul sur sa ligne : saut gardé si l'une des deux lignes est un titre.
    # Sinon (False), c'est un simple retour à la ligne de mise en page : les lignes seront recollées
    return _is_heading(previous) or _is_heading(current)


def join_wrapped_lines(text: str) -> str:
    """Recolle les lignes coupées par la mise en page ; garde un paragraphe par ligne."""
    # Découpe en lignes, retire les espaces aux extrémités et réduit les espaces multiples
    lines = [MULTIPLE_SPACES.sub(" ", line).strip() for line in text.splitlines()]

    # Supprime les lignes vides
    lines = [line for line in lines if line]

    # Rien à recoller si la page ne contient aucune ligne
    if not lines:
        # Texte vide
        return ""

    # Liste des paragraphes reconstruits ; le premier commence avec la première ligne
    paragraphs = [lines[0]]

    # Examine chaque ligne suivante
    for line in lines[1:]:
        # Vrai changement de paragraphe : la ligne commence un nouveau paragraphe
        if _is_paragraph_break(paragraphs[-1], line):
            # Nouveau paragraphe
            paragraphs.append(line)

        # Simple retour à la ligne de mise en page : on recolle au paragraphe en cours
        else:
            # Ajout avec un espace (le saut de ligne remplaçait un espace)
            paragraphs[-1] += " " + line

    # Un paragraphe par ligne dans le texte final
    return "\n".join(paragraphs)


def clean_text(text: str) -> str:
    """Nettoie le texte d'UNE page : normalisation des caractères puis recollage des lignes."""
    # Étape 1 : caractères uniformes
    text = normalize_unicode(text)

    # Étape 2 : lignes recollées en paragraphes
    return join_wrapped_lines(text)


def _line_signature(line: str) -> str:
    """Forme comparable d'une ligne : les chiffres sont masqués ("Page 2" -> "Page #")."""
    # Remplace chaque nombre par "#" et retire les espaces aux extrémités
    return DIGITS.sub("#", line.strip())


def remove_repeated_lines(pages: list[DocumentPage]) -> list[DocumentPage]:
    """Retire les en-têtes / pieds de page présents sur TOUTES les pages d'UN document.

    Seules les HEADER_FOOTER_ZONE premières et dernières lignes de chaque page sont
    examinées, pour ne jamais supprimer une phrase du corps du texte.
    """
    # Avec une seule page, impossible de savoir ce qui se répète : on ne touche à rien
    if len(pages) < 2:
        # Pages inchangées
        return pages

    # Pour chaque page, la liste de ses lignes non vides
    lines_per_page = [
        [line for line in page.text.splitlines() if line.strip()] for page in pages
    ]

    # Pour chaque page, l'ensemble des signatures des lignes du haut et du bas
    zone_signatures = [
        {
            _line_signature(line)
            for line in lines[:HEADER_FOOTER_ZONE] + lines[-HEADER_FOOTER_ZONE:]
        }
        for lines in lines_per_page
    ]

    # Intersection : les signatures présentes sur TOUTES les pages sont des en-têtes/pieds de page
    repeated = set.intersection(*zone_signatures)

    # Rien de répété : pages inchangées
    if not repeated:
        # Pages inchangées
        return pages

    # Trace en mode DEBUG les lignes retirées (utile pour vérifier qu'on n'enlève rien d'important)
    logger.debug(
        "%s : lignes répétées retirées : %s", pages[0].source, sorted(repeated)
    )

    # Nouvelles pages, sans les lignes répétées
    cleaned_pages: list[DocumentPage] = []

    # Traite chaque page avec ses lignes
    for page, lines in zip(pages, lines_per_page, strict=True):
        # Index à partir duquel commence la zone du bas de page
        footer_start = len(lines) - HEADER_FOOTER_ZONE

        # Garde une ligne si elle est hors des zones haut/bas, ou si elle n'est pas répétée
        kept_lines = [
            line
            for index, line in enumerate(lines)
            if HEADER_FOOTER_ZONE <= index < footer_start
            or _line_signature(line) not in repeated
        ]

        # Crée une nouvelle page avec le texte filtré (l'originale reste intacte)
        cleaned_pages.append(replace(page, text="\n".join(kept_lines)))

    # Renvoie les pages nettoyées
    return cleaned_pages


def clean_pages(pages: list[DocumentPage]) -> list[DocumentPage]:
    """Nettoie toutes les pages : en-têtes répétés par document, puis texte de chaque page.

    Les pages devenues vides après nettoyage sont ignorées avec un avertissement.
    """
    # Regroupe les pages par document (un dict garde l'ordre d'insertion)
    pages_by_document: dict[str, list[DocumentPage]] = {}

    # Range chaque page dans la liste de son document
    for page in pages:
        # setdefault crée la liste vide au premier passage, puis renvoie la liste existante
        pages_by_document.setdefault(page.document_id, []).append(page)

    # Pages nettoyées, tous documents confondus
    cleaned: list[DocumentPage] = []

    # Traite chaque document séparément
    for document_pages in pages_by_document.values():
        # Niveau document : retire les en-têtes / pieds de page répétés
        for page in remove_repeated_lines(document_pages):
            # Niveau page : normalise et recolle les lignes
            text = clean_text(page.text)

            # Une page qui ne contenait que l'en-tête est maintenant vide
            if not text:
                # On prévient et on l'ignore
                logger.warning(
                    "%s : page %d vide après nettoyage, ignorée",
                    page.source,
                    page.page_number,
                )

                # Page suivante
                continue

            # Nouvelle page avec le texte propre (document_id, source et page_number sont conservés)
            cleaned.append(replace(page, text=text))

    # Résumé du nettoyage
    logger.info(
        "Nettoyage : %d page(s) en entrée, %d page(s) en sortie",
        len(pages),
        len(cleaned),
    )

    # Renvoie les pages propres
    return cleaned
