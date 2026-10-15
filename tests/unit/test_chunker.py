"""Tests du découpage en chunks (app/ingestion/chunker.py)."""

# itertools.pairwise parcourt les éléments voisins deux à deux
import itertools

# pytest fournit pytest.raises et pytest.mark.parametrize
import pytest

# Le type des stratégies ("fixed" ou "sentence")
from app.core.config import ChunkStrategy

# Les fonctions que l'on teste
from app.ingestion.chunker import (
    chunk_page,
    chunk_pages,
    split_sentences,
    split_text_fixed,
    split_text_sentence,
)

# La page donnée en entrée au chunker
from app.models import DocumentPage


def make_page(text: str) -> DocumentPage:
    """Crée une page valide avec le texte donné."""
    # Seul le texte varie d'un test à l'autre
    return DocumentPage(
        document_id="abc123", source="cours.pdf", page_number=2, text=text
    )


# --- split_text_fixed ---


def test_short_text_gives_a_single_piece() -> None:
    # Un texte plus court que chunk_size tient dans un seul morceau
    assert split_text_fixed("Bonjour", chunk_size=400, chunk_overlap=100) == ["Bonjour"]


def test_empty_text_gives_no_piece() -> None:
    # Un texte vide ne produit aucun morceau
    assert split_text_fixed("", chunk_size=400, chunk_overlap=100) == []


def test_worked_example_from_the_notes() -> None:
    # Texte de 1 000 caractères : 10 blocs de 100 caractères identiques ("0000...", "1111...")
    text = "".join(str(digit) * 100 for digit in range(10))

    # Exemple numérique 1 de l'étape 3.1 : L=1000, s=400, o=100
    pieces = split_text_fixed(text, chunk_size=400, chunk_overlap=100)

    # Fenêtres attendues : [0, 400), [300, 700), [600, 1000)
    assert pieces == [text[0:400], text[300:700], text[600:1000]]


def test_number_of_pieces_matches_the_formula_on_a_real_page_size() -> None:
    # Longueur de ma vraie page 01_introduction_rag p.1 (mesurée à l'étape 3.1)
    pieces = split_text_fixed("a" * 2386, chunk_size=800, chunk_overlap=150)

    # Formule : ceil((2386 - 150) / 650) = ceil(3.44) = 4
    assert len(pieces) == 4

    # Le dernier morceau commence à 1950 : il ne fait que 2386 - 1950 = 436 caractères
    assert len(pieces[-1]) == 436


def test_consecutive_pieces_share_exactly_the_overlap() -> None:
    # Texte de 26 caractères, tous différents : facile de voir ce qui est partagé
    pieces = split_text_fixed(
        "abcdefghijklmnopqrstuvwxyz", chunk_size=10, chunk_overlap=3
    )

    # Pour chaque paire de morceaux voisins : pairwise donne (p0, p1), (p1, p2), (p2, p3)...
    for previous, following in itertools.pairwise(pieces):
        # ...les 3 derniers caractères de l'un sont les 3 premiers de l'autre
        assert previous[-3:] == following[:3]


def test_without_overlap_pieces_rebuild_the_text() -> None:
    # Phrase quelconque, plus longue que chunk_size
    text = "Le RAG associe une recherche de passages et une génération de réponse par un LLM local."

    # Sans chevauchement, on avance exactement de chunk_size
    pieces = split_text_fixed(text, chunk_size=20, chunk_overlap=0)

    # Recoller les morceaux redonne le texte original : rien n'est perdu
    assert "".join(pieces) == text


def test_no_piece_exceeds_chunk_size() -> None:
    # Texte de 1 234 caractères
    pieces = split_text_fixed("x" * 1234, chunk_size=300, chunk_overlap=50)

    # Aucun morceau ne dépasse la taille maximale
    assert all(len(piece) <= 300 for piece in pieces)


# parametrize : le même test est exécuté une fois pour chaque ligne de valeurs
@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap", "message"),
    [
        # Taille nulle
        (0, 0, "chunk_size"),
        # Chevauchement négatif
        (100, -1, "chunk_overlap"),
        # Chevauchement égal à la taille : le pas serait 0 (boucle infinie)
        (100, 100, "chunk_overlap"),
        # Chevauchement plus grand que la taille : le pas serait négatif
        (100, 150, "chunk_overlap"),
    ],
)
def test_invalid_parameters_are_rejected(
    chunk_size: int, chunk_overlap: int, message: str
) -> None:
    # Des paramètres invalides doivent lever une ValueError qui nomme le paramètre fautif
    with pytest.raises(ValueError, match=message):
        # Tentative de découpage invalide
        split_text_fixed("du texte", chunk_size=chunk_size, chunk_overlap=chunk_overlap)


# --- split_sentences ---


def test_sentences_are_split_on_endings_and_line_breaks() -> None:
    # Un titre sur sa ligne, puis un paragraphe de 3 phrases (dont « ! » précédé d'une espace)
    text = "1. Définition\nLe RAG cherche des passages. Il cite ses sources ! Pourquoi ? Pour vérifier."

    # Le titre est gardé entier ; chaque phrase devient un élément
    assert split_sentences(text) == [
        "1. Définition",
        "Le RAG cherche des passages.",
        "Il cite ses sources !",
        "Pourquoi ?",
        "Pour vérifier.",
    ]


def test_numbers_and_lowercase_do_not_end_a_sentence() -> None:
    # "3.5" (pas d'espace après le point), "2.3. Les" (numéro de titre), "etc. puis" (minuscule)
    text = "2.3. Les versions 3.5 et 4.0 changent tout, etc. puis on mesure."

    # Aucune de ces coupures n'est une vraie fin de phrase : un seul élément
    assert split_sentences(text) == [text]


# --- split_text_sentence ---


def sentence(first_letter: str, length: int) -> str:
    """Crée une phrase de ``length`` caractères : majuscule, des "x", puis un point."""
    # Exemple : sentence("A", 5) == "Axxx."
    return first_letter + "x" * (length - 2) + "."


def test_sentences_are_packed_until_chunk_size() -> None:
    # 3 phrases de 30 caractères
    a, b, c = sentence("A", 30), sentence("B", 30), sentence("C", 30)

    # A + " " + B = 61 <= 70 ; ajouter C donnerait 92 > 70 : C commence un nouveau morceau
    pieces = split_text_sentence(f"{a} {b} {c}", chunk_size=70, chunk_overlap=0)

    # Deux morceaux, faits de phrases entières
    assert pieces == [f"{a} {b}", c]


def test_overlap_repeats_whole_sentences() -> None:
    # 3 phrases de 30 caractères
    a, b, c = sentence("A", 30), sentence("B", 30), sentence("C", 30)

    # overlap=35 : la dernière phrase (B, 30 car.) tient dans le chevauchement, pas A + B (61)
    pieces = split_text_sentence(f"{a} {b} {c}", chunk_size=70, chunk_overlap=35)

    # B est répétée au début du second morceau
    assert pieces == [f"{a} {b}", f"{b} {c}"]


def test_sentence_longer_than_overlap_is_not_repeated() -> None:
    # 3 phrases de 30 caractères
    a, b, c = sentence("A", 30), sentence("B", 30), sentence("C", 30)

    # overlap=20 < 30 : aucune phrase entière ne tient dans le chevauchement
    pieces = split_text_sentence(f"{a} {b} {c}", chunk_size=70, chunk_overlap=20)

    # Pas de répétition : on ne coupe jamais une phrase pour remplir le chevauchement
    assert pieces == [f"{a} {b}", c]


def test_overlap_shrinks_to_make_room_for_the_next_sentence() -> None:
    # Deux phrases de 30 puis une de 45
    a, b, e = sentence("A", 30), sentence("B", 30), sentence("E", 45)

    # overlap=65 permettrait de reprendre A + B (61), mais A + B + E (107) dépasse 70 :
    # on retire A (B + E = 76, encore trop), puis B : le second morceau ne contient que E
    pieces = split_text_sentence(f"{a} {b} {e}", chunk_size=70, chunk_overlap=65)

    # Aucun morceau ne dépasse la taille, même avec un grand chevauchement
    assert pieces == [f"{a} {b}", e]


def test_giant_sentence_falls_back_to_fixed_windows() -> None:
    # Une phrase normale (30 car.) puis une phrase géante (150 car.) plus grande que chunk_size
    a, giant = sentence("A", 30), sentence("D", 150)

    # size=60, overlap=10 : la phrase géante est coupée en fenêtres fixes (pas de 50)
    pieces = split_text_sentence(f"{a} {giant}", chunk_size=60, chunk_overlap=10)

    # A seule, puis les fenêtres [0, 60), [50, 110), [100, 150) de la phrase géante
    assert pieces == [a, giant[0:60], giant[50:110], giant[100:150]]


def test_sentence_strategy_validates_its_parameters() -> None:
    # Mêmes règles que "fixed" : overlap >= size est refusé
    with pytest.raises(ValueError, match="chunk_overlap"):
        # Tentative de découpage invalide
        split_text_sentence("Une phrase.", chunk_size=100, chunk_overlap=100)


def test_sentence_strategy_on_empty_text_gives_no_piece() -> None:
    # Un texte vide ne produit aucun morceau
    assert split_text_sentence("", chunk_size=100, chunk_overlap=10) == []


# --- chunk_page et chunk_pages ---


# Les deux stratégies doivent produire des chunks avec les mêmes métadonnées
@pytest.mark.parametrize("strategy", ["fixed", "sentence"])
def test_chunks_keep_the_page_origin_and_are_numbered(strategy: ChunkStrategy) -> None:
    # Page de 250 caractères sans fin de phrase, fenêtres de 100 avec 20 de chevauchement
    # (avec "sentence", c'est une phrase géante : elle est coupée comme avec "fixed")
    chunks = chunk_page(
        make_page("z" * 250), chunk_size=100, chunk_overlap=20, strategy=strategy
    )

    # Débuts 0, 80, 160 : la fenêtre [160, 260) atteint la fin, donc 3 chunks
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]

    # Chaque chunk garde le document, la source et la page d'origine
    assert all(
        (chunk.document_id, chunk.source, chunk.page_number)
        == ("abc123", "cours.pdf", 2)
        for chunk in chunks
    )

    # Les identifiants suivent le format "<document_id>-p<page>-c<index>"
    assert [chunk.chunk_id for chunk in chunks] == [
        "abc123-p2-c0",
        "abc123-p2-c1",
        "abc123-p2-c2",
    ]


def test_blank_pieces_are_skipped_without_gap_in_numbering() -> None:
    # 10 lettres, 10 espaces, puis 10 lettres : la fenêtre du milieu ne contient que des espaces
    text = "a" * 10 + " " * 10 + "b" * 10

    # Fenêtres de 10 sans chevauchement : "aaaaaaaaaa", "          ", "bbbbbbbbbb"
    chunks = chunk_page(
        make_page(text), chunk_size=10, chunk_overlap=0, strategy="fixed"
    )

    # Le morceau vide est ignoré : seuls les deux morceaux utiles deviennent des chunks
    assert [chunk.text for chunk in chunks] == ["a" * 10, "b" * 10]

    # La numérotation reste continue (0, 1), sans trou à la place du morceau ignoré
    assert [chunk.chunk_index for chunk in chunks] == [0, 1]


def test_unknown_strategy_is_rejected() -> None:
    # Une stratégie non implémentée doit lever une ValueError claire
    with pytest.raises(ValueError, match="stratégie inconnue"):
        # "semantic" n'existe pas (le type est contourné volontairement pour le test)
        chunk_page(
            make_page("Du texte."),
            chunk_size=100,
            chunk_overlap=10,
            strategy="semantic",  # type: ignore[arg-type]
        )


def test_chunk_pages_never_crosses_pages_and_restarts_numbering() -> None:
    # Deux pages d'un même document
    page_1 = DocumentPage("abc123", "cours.pdf", 1, "Première page. Elle parle du RAG.")
    page_2 = DocumentPage(
        "abc123", "cours.pdf", 2, "Deuxième page. Elle parle des embeddings."
    )

    # Taille large : chaque page tient dans un seul chunk
    chunks = chunk_pages(
        [page_1, page_2], chunk_size=800, chunk_overlap=150, strategy="sentence"
    )

    # Un chunk par page, chacun rattaché à SA page, et l'index repart de 0 sur chaque page
    assert [chunk.chunk_id for chunk in chunks] == ["abc123-p1-c0", "abc123-p2-c0"]

    # Le texte de la page 2 ne déborde pas dans le chunk de la page 1
    assert chunks[0].text == "Première page. Elle parle du RAG."
