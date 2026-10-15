"""Tests de l'API FastAPI avec TestClient (requêtes HTTP simulées, sans serveur réel).

Le pipeline est réel (ChromaDB temporaire), sauf le modèle d'embeddings et le LLM (faux).
"""

# Path représente un chemin de fichier
from pathlib import Path

# pytest fournit les fixtures
import pytest

# TestClient : envoie des requêtes HTTP à l'application, en mémoire
from fastapi.testclient import TestClient

# Ce que l'on teste
from app.core.config import Settings
from app.generation.llm import LLMError, LLMUnavailableError
from app.main import create_app
from tests.fakes import FakeLLM, make_fake_pipeline, pdf_bytes

# Un PDF de 2 pages : une sur le RAG, une sur le cosinus
DEMO_PDF = pdf_bytes(
    "Le rag associe recherche et llm.", "Le cosinus compare deux vecteurs."
)


class FailingLLM:
    """Faux LLM qui lève l'erreur donnée (pour tester la traduction en codes HTTP)."""

    def __init__(self, error: Exception) -> None:
        # Erreur à lever à chaque appel
        self.error = error

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        # Simule une panne du LLM
        raise self.error


def make_client(tmp_path: Path, llm: object | None = None) -> TestClient:
    """Client HTTP de test branché sur une application avec un pipeline factice."""
    # Configuration de test : sans .env, limite d'envoi réduite à 1 Mo
    settings = Settings(_env_file=None, max_upload_mb=1)

    # Application avec le pipeline injecté (aucun vrai modèle, aucun Ollama)
    app = create_app(
        settings,
        make_fake_pipeline(
            tmp_path, llm or FakeLLM("Le cosinus compare des vecteurs [1].")
        ),
    )

    # TestClient exécute aussi le cycle de vie (lifespan) de l'application
    return TestClient(app)


def upload(client: TestClient, name: str, content: bytes) -> object:
    """Envoie un fichier sur POST /documents (formulaire multipart)."""
    # Le champ du formulaire s'appelle "file", comme le paramètre de la route
    return client.post("/documents", files={"file": (name, content, "application/pdf")})


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    """Client démarré (lifespan exécuté) puis arrêté proprement après le test."""
    # Le bloc with déclenche le démarrage et l'arrêt de l'application
    with make_client(tmp_path) as test_client:
        yield test_client


def test_health_reports_empty_index(client: TestClient) -> None:
    # État initial
    response = client.get("/health")

    # L'API répond ; index vide ; le faux LLM ne sait pas dire s'il est disponible → False
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "documents": 0,
        "chunks": 0,
        "llm_available": False,
        "llm_model": "inconnu",
    }


def test_upload_indexes_then_skips_duplicate(
    client: TestClient, tmp_path: Path
) -> None:
    # Premier envoi : indexé
    first = upload(client, "cours.pdf", DEMO_PDF)
    assert first.status_code == 201
    assert first.json()["status"] == "indexed"

    # Le fichier est enregistré dans data/raw/ (ici le dossier temporaire)
    assert (tmp_path / "raw" / "cours.pdf").read_bytes() == DEMO_PDF

    # Second envoi identique : reconnu, non réindexé
    assert upload(client, "cours.pdf", DEMO_PDF).json()["status"] == "skipped"

    # Le document est listé une seule fois
    assert [doc["source"] for doc in client.get("/documents").json()] == ["cours.pdf"]


@pytest.mark.parametrize(
    ("name", "content", "expected_status"),
    [
        # Mauvaise extension
        ("notes.txt", b"du texte", 415),
        # Bonne extension mais contenu qui n'est pas un PDF
        ("faux.pdf", b"ceci n'est pas un PDF", 415),
        # Signature PDF correcte mais fichier corrompu : illisible par PyMuPDF
        ("casse.pdf", b"%PDF-1.4 contenu corrompu", 422),
        # Plus de 1 Mo (limite de test)
        ("gros.pdf", b"%PDF-" + b"0" * (1024 * 1024), 413),
    ],
    # Identifiants courts : sinon pytest afficherait le contenu de 1 Mo dans le nom du test
    ids=["extension", "signature", "corrompu", "trop-gros"],
)
def test_invalid_uploads_are_rejected(
    client: TestClient, tmp_path: Path, name: str, content: bytes, expected_status: int
) -> None:
    # Envoi du fichier invalide
    response = upload(client, name, content)

    # Code HTTP attendu, et aucun fichier conservé dans data/raw/
    assert response.status_code == expected_status
    assert not (tmp_path / "raw" / name).exists()


def test_same_name_with_other_content_is_a_conflict(client: TestClient) -> None:
    # Un premier document "cours.pdf"
    upload(client, "cours.pdf", DEMO_PDF)

    # Un AUTRE contenu sous le même nom : refusé plutôt qu'écrasé
    response = upload(client, "cours.pdf", pdf_bytes("Un tout autre cours."))
    assert response.status_code == 409


def test_path_traversal_in_filename_is_neutralized(
    client: TestClient, tmp_path: Path
) -> None:
    # Un nom de fichier qui tente de sortir du dossier
    response = upload(client, "../../evil.pdf", DEMO_PDF)

    # Le fichier est enregistré DANS data/raw/, sous son seul nom
    assert response.status_code == 201
    assert (tmp_path / "raw" / "evil.pdf").exists()
    assert not (tmp_path / "evil.pdf").exists()


def test_ask_returns_answer_with_numbered_sources(client: TestClient) -> None:
    # Indexe le document puis pose une question
    upload(client, "cours.pdf", DEMO_PDF)
    response = client.post("/ask", json={"question": "Que compare le cosinus ?"})

    # Réponse du faux LLM, sources numérotées, la source [1] est marquée comme citée
    body = response.json()
    assert response.status_code == 200
    assert body["answer"] == "Le cosinus compare des vecteurs [1]."
    assert body["sources"][0]["number"] == 1
    assert body["sources"][0]["cited"] is True
    assert body["sources"][0]["page_number"] == 2
    assert body["abstained"] is False


@pytest.mark.parametrize("question", ["", "   ", "x" * 1001])
def test_invalid_questions_are_rejected(client: TestClient, question: str) -> None:
    # Vide, blanche ou trop longue : 422
    assert client.post("/ask", json={"question": question}).status_code == 422


@pytest.mark.parametrize(
    ("error", "expected_status"),
    [
        # Ollama éteint
        (LLMUnavailableError("Ollama est injoignable"), 503),
        # Ollama a mal répondu (modèle absent...)
        (LLMError("modèle absent"), 502),
    ],
)
def test_llm_failures_become_http_errors(
    tmp_path: Path, error: Exception, expected_status: int
) -> None:
    # Application dont le LLM tombe en panne
    with make_client(tmp_path, FailingLLM(error)) as client:
        # Il faut au moins une source pour que le LLM soit appelé
        upload(client, "cours.pdf", DEMO_PDF)
        response = client.post("/ask", json={"question": "rag et llm"})

    # Code HTTP attendu, avec le message d'origine
    assert response.status_code == expected_status
    assert str(error) in response.json()["detail"]


def test_delete_removes_chunks_and_file(client: TestClient, tmp_path: Path) -> None:
    # Indexe un document
    document_id = upload(client, "cours.pdf", DEMO_PDF).json()["document_id"]

    # Le supprime
    response = client.delete(f"/documents/{document_id}")

    # Chunks supprimés, fichier effacé, index vide
    assert response.status_code == 200
    assert response.json()["deleted_chunks"] > 0
    assert not (tmp_path / "raw" / "cours.pdf").exists()
    assert client.get("/documents").json() == []

    # Un document inconnu : 404
    assert client.delete("/documents/inconnu").status_code == 404


def test_openapi_documentation_is_generated(client: TestClient) -> None:
    # FastAPI génère la documentation à partir des schémas
    paths = client.get("/openapi.json").json()["paths"]

    # Les routes sont toutes documentées
    assert {"/health", "/ask", "/documents", "/documents/{document_id}"} <= set(paths)
