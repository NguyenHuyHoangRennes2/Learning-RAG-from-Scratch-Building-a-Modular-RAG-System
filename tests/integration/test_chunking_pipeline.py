"""Test d'intégration du chunking : PDF -> chargeur -> nettoyage -> chunks -> statistiques.

On vérifie que les modules fonctionnent ENSEMBLE, sur un PDF réaliste de 2 pages
(en-tête répété, numéro de page, titre numéroté, lignes coupées par la mise en page).
"""

# Path représente un chemin de fichier
from pathlib import Path

# PyMuPDF sert à fabriquer le PDF de test
import pymupdf

# pytest fournit pytest.mark.parametrize
import pytest

# Le type des stratégies ("fixed" ou "sentence")
from app.core.config import ChunkStrategy

# Les modules dont on teste l'enchaînement
from app.ingestion.chunker import chunk_pages, split_sentences
from app.ingestion.pdf_loader import load_pdfs_from_directory
from app.ingestion.text_cleaner import clean_pages
from app.models import DocumentPage
from scripts.compare_chunking import compute_stats

# Petits paramètres pour obtenir plusieurs chunks par page avec un texte court
CHUNK_SIZE = 200
CHUNK_OVERLAP = 50

# Contenu de chaque page : (titre, lignes du corps telles que la mise en page les coupe)
PAGE_CONTENTS = [
    (
        "Définition",
        [
            "Le RAG associe une recherche d'informations à un modèle",
            "de langage. Le modèle reçoit des passages pertinents et",
            "les utilise comme contexte pour répondre. Cette approche",
            "réduit les hallucinations, sans les supprimer totalement.",
            "Il faut donc mesurer la qualité des passages retrouvés",
            "et vérifier que la réponse cite correctement ses sources.",
        ],
    ),
    (
        "Composants",
        [
            "Un chargeur PDF extrait le texte page par page. Le texte",
            "est ensuite nettoyé puis découpé en chunks de taille",
            "limitée. Chaque chunk garde son document et sa page",
            "d'origine, ce qui permet de citer la source exacte dans",
            "la réponse finale.",
        ],
    ),
]


def create_realistic_pdf(path: Path) -> None:
    """Crée un PDF de 2 pages qui reproduit les défauts de nos vrais documents."""
    # Document PDF vide, en mémoire
    doc = pymupdf.open()

    # Crée une page par contenu, numérotée à partir de 1
    for number, (title, body_lines) in enumerate(PAGE_CONTENTS, start=1):
        # En-tête répété, numéro de page, titre numéroté, puis le corps ligne par ligne
        lines = [
            "Corpus de test • Démonstration",
            f"Page {number}",
            f"{number}. {title}",
            *body_lines,
        ]

        # Écrit le texte de la page (les \n créent des lignes séparées dans le PDF)
        doc.new_page().insert_text((72, 72), "\n".join(lines))

    # Enregistre le PDF sur le disque
    doc.save(path)

    # Libère le document en mémoire
    doc.close()


@pytest.fixture
def pages(tmp_path: Path) -> list[DocumentPage]:
    """Pages nettoyées d'un PDF réaliste (chargeur + nettoyage, comme en production)."""
    # Crée le PDF dans un dossier temporaire
    create_realistic_pdf(tmp_path / "cours.pdf")

    # Enchaîne les deux premières étapes de l'ingestion
    return clean_pages(load_pdfs_from_directory(tmp_path))


# Les règles communes doivent être vraies pour les deux stratégies
@pytest.mark.parametrize("strategy", ["fixed", "sentence"])
def test_chunks_are_valid_and_traceable(
    pages: list[DocumentPage], strategy: ChunkStrategy
) -> None:
    # Découpe les 2 pages
    chunks = chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP, strategy)

    # Le texte est assez long pour produire plusieurs chunks
    assert len(chunks) > len(pages)

    # Aucun chunk ne dépasse la taille maximale
    assert all(len(chunk.text) <= CHUNK_SIZE for chunk in chunks)

    # Les identifiants sont uniques : pas de collision possible dans ChromaDB (Phase 5)
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)

    # Chaque chunk est rattaché au bon document et à une page qui existe
    assert {(chunk.document_id, chunk.page_number) for chunk in chunks} == {
        (page.document_id, page.page_number) for page in pages
    }

    # L'en-tête répété a bien été retiré AVANT le découpage : aucun chunk ne le contient
    assert not any("Corpus de test" in chunk.text for chunk in chunks)


def test_sentence_strategy_keeps_every_sentence_whole(
    pages: list[DocumentPage],
) -> None:
    # Découpe avec la stratégie par phrases
    chunks = chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP, "sentence")

    # Pour chaque page et chacune de ses phrases...
    for page in pages:
        # Textes des chunks de CETTE page
        page_chunks = [c.text for c in chunks if c.page_number == page.page_number]

        # ...la phrase apparaît ENTIÈRE dans au moins un chunk de sa page
        for sentence in split_sentences(page.text):
            # Aucune phrase n'est perdue ni coupée
            assert any(sentence in text for text in page_chunks), sentence


def test_sentence_strategy_has_cleaner_boundaries_than_fixed(
    pages: list[DocumentPage],
) -> None:
    # Statistiques mesurées pour chaque stratégie, sur les mêmes pages
    fixed = compute_stats(chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP, "fixed"), pages)
    sentence = compute_stats(
        chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP, "sentence"), pages
    )

    # "sentence" : tous les chunks commencent et finissent comme des phrases
    # (y compris aucun titre orphelin en fin de chunk, grâce à attach_headings)
    assert sentence.clean_start_ratio == 1.0
    assert sentence.clean_end_ratio == 1.0

    # "fixed" coupe au milieu des phrases : certaines fins ne sont pas propres
    assert fixed.clean_end_ratio < 1.0
