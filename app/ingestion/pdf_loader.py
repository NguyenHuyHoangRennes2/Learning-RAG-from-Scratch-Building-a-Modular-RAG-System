"""Chargement des PDF : fichier PDF -> liste de DocumentPage (texte brut, page par page).

Ce module ne fait QUE lire les PDF. Le nettoyage du texte est fait ailleurs
(app/ingestion/text_cleaner.py), pour garder une responsabilité par fichier.
"""

# hashlib fournit les fonctions de hachage (SHA-256) pour calculer l'identifiant d'un document
import hashlib

# logging pour tracer ce qui se passe (pages chargées, pages vides, fichiers en erreur)
import logging

# Path représente un chemin de fichier de façon portable
from pathlib import Path

# PyMuPDF : lecture des PDF
import pymupdf

# La structure de données produite par ce module (étape 2.2)
from app.models import DocumentPage

# Logger nommé d'après le module : "app.ingestion.pdf_loader" apparaîtra dans les logs
logger = logging.getLogger(__name__)

# Nombre de caractères hexadécimaux gardés du hash SHA-256 (64 au total) pour l'identifiant
DOCUMENT_ID_LENGTH = 16

# Taille des morceaux lus pour calculer le hash : 1 Mo (évite de charger un gros fichier d'un coup)
HASH_READ_SIZE = 1024 * 1024


class PDFLoadError(Exception):
    """Erreur levée quand un PDF ne peut pas être chargé (absent, corrompu, protégé)."""


def compute_document_id(pdf_path: Path) -> str:
    """Calcule un identifiant stable à partir du CONTENU du fichier (et non de son nom).

    Deux fichiers identiques ont le même identifiant, même s'ils portent des noms
    différents : cela permettra d'éviter d'indexer deux fois le même document.
    """
    # Crée un objet de hachage SHA-256 vide
    hasher = hashlib.sha256()

    # Ouvre le fichier en lecture binaire ("rb") : on hache les octets bruts
    with pdf_path.open("rb") as file:
        # Lit le fichier morceau par morceau jusqu'à ce que read() renvoie b"" (fin du fichier)
        while block := file.read(HASH_READ_SIZE):
            # Ajoute ce morceau au calcul du hash
            hasher.update(block)

    # hexdigest() donne le hash en 64 caractères hexadécimaux ; on garde les 16 premiers
    return hasher.hexdigest()[:DOCUMENT_ID_LENGTH]


def load_pdf(pdf_path: Path) -> list[DocumentPage]:
    """Charge un PDF et renvoie une DocumentPage par page contenant du texte.

    Les pages sans texte (vides ou scannées) sont ignorées avec un avertissement.

    Raises:
        PDFLoadError: si le fichier est absent, n'est pas un PDF lisible, ou est protégé.
    """
    # Vérifie que le chemin désigne bien un fichier existant
    if not pdf_path.is_file():
        # Erreur explicite plutôt qu'une erreur obscure de PyMuPDF
        raise PDFLoadError(f"Fichier introuvable : {pdf_path}")

    # Calcule l'identifiant du document à partir de son contenu
    document_id = compute_document_id(pdf_path)

    # Essaie d'ouvrir le PDF ; un fichier corrompu ou qui n'est pas un PDF lève FileDataError
    try:
        # Ouvre le PDF depuis la MÉMOIRE (stream) et non depuis le disque : sous Windows,
        # un échec d'ouverture laissait le fichier verrouillé (WinError 32, trouvé en Phase 9)
        doc = pymupdf.open(stream=pdf_path.read_bytes(), filetype="pdf")

    # Le fichier existe mais son contenu n'est pas un PDF valide
    except pymupdf.FileDataError as error:
        # On transforme l'erreur de PyMuPDF en erreur de notre projet ("from" garde la cause d'origine)
        raise PDFLoadError(f"PDF illisible ou corrompu : {pdf_path.name}") from error

    # Le "with" garantit la fermeture du document à la fin, même en cas d'erreur
    with doc:
        # Un PDF protégé par mot de passe ne peut pas être lu sans ce mot de passe
        if doc.needs_pass:
            # On refuse explicitement le fichier
            raise PDFLoadError(f"PDF protégé par mot de passe : {pdf_path.name}")

        # Liste des pages produites
        pages: list[DocumentPage] = []

        # Parcourt les pages ; start=1 pour numéroter comme un humain (conversion faite UNE seule fois ici)
        for page_number, page in enumerate(doc, start=1):
            # Extrait le texte brut de la page
            text = page.get_text()

            # strip() retire les espaces/sauts de ligne : s'il ne reste rien, la page n'a pas de texte
            if not text.strip():
                # Prévient sans bloquer : la page est peut-être une image scannée (nécessiterait de l'OCR)
                logger.warning(
                    "%s : page %d sans texte (vide ou scannée), ignorée",
                    pdf_path.name,
                    page_number,
                )

                # Passe directement à la page suivante
                continue

            # Crée la page avec ses métadonnées et l'ajoute à la liste
            pages.append(
                DocumentPage(
                    document_id=document_id,
                    source=pdf_path.name,
                    page_number=page_number,
                    text=text,
                )
            )

        # Résumé du chargement de ce fichier
        logger.info(
            "%s : %d page(s) chargée(s) sur %d (id=%s)",
            pdf_path.name,
            len(pages),
            doc.page_count,
            document_id,
        )

    # Renvoie toutes les pages contenant du texte
    return pages


def load_pdfs_from_directory(directory: Path) -> list[DocumentPage]:
    """Charge tous les PDF d'un dossier.

    - Un fichier en erreur est signalé puis ignoré : il ne bloque pas les autres.
    - Un fichier en double (même contenu, donc même document_id) n'est chargé qu'une fois.
    """
    # Vérifie que le dossier existe
    if not directory.is_dir():
        # Sans dossier, il n'y a rien à charger : c'est une erreur de configuration
        raise PDFLoadError(f"Dossier introuvable : {directory}")

    # Liste les PDF du dossier, triés pour toujours traiter les fichiers dans le même ordre
    pdf_paths = sorted(directory.glob("*.pdf"))

    # Prévient si le dossier ne contient aucun PDF
    if not pdf_paths:
        # Avertissement : ce n'est pas une erreur, mais c'est probablement inattendu
        logger.warning("Aucun PDF trouvé dans %s", directory)

    # Toutes les pages de tous les documents
    all_pages: list[DocumentPage] = []

    # Identifiants des documents déjà chargés (un set permet une recherche très rapide)
    seen_document_ids: set[str] = set()

    # Traite chaque fichier PDF
    for pdf_path in pdf_paths:
        # Essaie de charger ce PDF
        try:
            # Charge les pages du fichier
            pages = load_pdf(pdf_path)

        # Un fichier illisible ne doit pas empêcher de charger les autres
        except PDFLoadError as error:
            # On journalise l'erreur et on passe au fichier suivant
            logger.error("Fichier ignoré : %s", error)

            # Fichier suivant
            continue

        # Si le fichier n'a aucune page avec du texte, il n'y a rien à ajouter
        if not pages:
            # Fichier suivant
            continue

        # Toutes les pages d'un fichier partagent le même document_id : on lit celui de la première
        document_id = pages[0].document_id

        # Si ce contenu a déjà été chargé sous un autre nom, c'est un doublon
        if document_id in seen_document_ids:
            # On le signale et on ne l'ajoute pas une seconde fois
            logger.warning(
                "Doublon ignoré : %s (id=%s déjà chargé)", pdf_path.name, document_id
            )

            # Fichier suivant
            continue

        # Mémorise cet identifiant comme déjà chargé
        seen_document_ids.add(document_id)

        # Ajoute les pages de ce fichier à la liste globale
        all_pages.extend(pages)

    # Résumé global
    logger.info(
        "%d document(s) chargé(s), %d page(s) au total",
        len(seen_document_ids),
        len(all_pages),
    )

    # Renvoie toutes les pages
    return all_pages
