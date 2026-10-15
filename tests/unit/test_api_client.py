"""Tests du client HTTP de l'interface, avec un faux serveur (httpx.MockTransport)."""

# json pour relire le corps des requêtes envoyées
import json

# httpx fournit MockTransport et les objets Request / Response
import httpx

# pytest fournit pytest.raises
import pytest

# Ce que l'on teste
from frontend.api_client import ApiError, RAGApiClient


def make_client(handler) -> RAGApiClient:  # type: ignore[no-untyped-def]
    """Client dont les requêtes sont traitées par ``handler`` (aucun réseau)."""
    # Faux transport : handler(request) répond à la place de l'API
    http = httpx.Client(
        base_url="http://api.test", transport=httpx.MockTransport(handler)
    )
    return RAGApiClient("http://api.test", http_client=http)


def test_ask_posts_the_question_as_json() -> None:
    # Mémorise la requête reçue
    received: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        # Enregistre la méthode, le chemin et le corps
        received.update(
            method=request.method,
            path=request.url.path,
            body=json.loads(request.content),
        )
        return httpx.Response(200, json={"answer": "Réponse [1].", "sources": []})

    # Pose une question
    result = make_client(handler).ask("Qu'est-ce que le RAG ?")

    # Bonne route, bon corps, réponse décodée
    assert received == {
        "method": "POST",
        "path": "/ask",
        "body": {"question": "Qu'est-ce que le RAG ?"},
    }
    assert result["answer"] == "Réponse [1]."


def test_upload_sends_a_multipart_file() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        # Le corps multipart contient le nom du fichier et son contenu
        assert b'filename="cours.pdf"' in request.content
        assert b"%PDF-contenu" in request.content
        return httpx.Response(201, json={"status": "indexed"})

    # Envoie un fichier
    assert (
        make_client(handler).upload("cours.pdf", b"%PDF-contenu")["status"] == "indexed"
    )


def test_http_errors_carry_the_api_detail() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        # L'API répond 503 avec une explication (format FastAPI)
        return httpx.Response(503, json={"detail": "Ollama est injoignable"})

    # L'erreur garde le code et le message de l'API
    with pytest.raises(ApiError, match="503 : Ollama est injoignable") as info:
        # Appel qui échoue
        make_client(handler).ask("question")
    assert info.value.status_code == 503


def test_unreachable_api_gives_a_helpful_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        # API éteinte
        raise httpx.ConnectError("refus", request=request)

    # Le message explique comment démarrer l'API
    with pytest.raises(ApiError, match="uvicorn app.main:app"):
        # Appel qui échoue
        make_client(handler).health()


def test_delete_and_list_use_the_right_routes() -> None:
    # Routes appelées, dans l'ordre
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        # Mémorise "MÉTHODE chemin"
        calls.append(f"{request.method} {request.url.path}")
        return httpx.Response(
            200, json=[] if request.method == "GET" else {"deleted_chunks": 3}
        )

    # Liste puis suppression
    client = make_client(handler)
    client.list_documents()
    client.delete("abc123")

    # Les deux routes attendues
    assert calls == ["GET /documents", "DELETE /documents/abc123"]
