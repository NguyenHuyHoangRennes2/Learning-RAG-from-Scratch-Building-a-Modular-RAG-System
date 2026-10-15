"""Tests du client Ollama SANS serveur Ollama : httpx.MockTransport simule ses réponses."""

# json pour relire le corps de la requête envoyée
import json

# httpx fournit MockTransport (faux réseau) et les objets Request / Response
import httpx

# pytest fournit pytest.raises
import pytest

# Ce que l'on teste
from app.generation.llm import LLMError, LLMUnavailableError, OllamaClient


def make_client(handler) -> OllamaClient:  # type: ignore[no-untyped-def]
    """Client Ollama dont les requêtes HTTP sont traitées par ``handler`` (aucun réseau)."""
    # Le faux transport appelle handler(request) au lieu d'envoyer la requête
    http = httpx.Client(
        base_url="http://ollama.test", transport=httpx.MockTransport(handler)
    )

    # Client configuré avec un modèle fictif
    return OllamaClient(
        "http://ollama.test", "qwen2.5:3b", temperature=0.1, http_client=http
    )


def test_generate_sends_messages_and_returns_content() -> None:
    # Mémorise la requête reçue par le « serveur »
    received: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        # Enregistre le chemin et le corps JSON de la requête
        received["path"] = request.url.path
        received["body"] = json.loads(request.content)

        # Répond comme Ollama
        return httpx.Response(
            200, json={"message": {"role": "assistant", "content": " Réponse [1]. "}}
        )

    # Appelle le client
    answer = make_client(handler).generate("consignes", "question")

    # Le texte est renvoyé sans espaces superflus
    assert answer == "Réponse [1]."

    # La requête vise /api/chat, sans streaming, avec les deux messages et les options
    body = received["body"]
    assert received["path"] == "/api/chat"
    assert body["stream"] is False  # type: ignore[index]
    assert body["messages"] == [  # type: ignore[index]
        {"role": "system", "content": "consignes"},
        {"role": "user", "content": "question"},
    ]
    assert body["options"]["temperature"] == 0.1  # type: ignore[index]


def test_unreachable_server_raises_a_helpful_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        # Simule un serveur éteint
        raise httpx.ConnectError("connexion refusée", request=request)

    # L'erreur métier explique quoi faire
    with pytest.raises(LLMUnavailableError, match="injoignable"):
        # Appel qui échoue
        make_client(handler).generate("s", "u")


def test_connection_timeout_means_server_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        # Simule une connexion qui ne s'établit pas dans le délai (serveur absent)
        raise httpx.ConnectTimeout("connexion trop lente", request=request)

    # Ce n'est PAS une génération trop lente : c'est un serveur indisponible
    with pytest.raises(LLMUnavailableError, match="injoignable"):
        # Appel qui échoue
        make_client(handler).generate("s", "u")


def test_missing_model_suggests_ollama_pull() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        # Ollama répond 404 quand le modèle n'est pas téléchargé
        return httpx.Response(404, json={"error": "model not found"})

    # Le message donne la commande à lancer
    with pytest.raises(LLMError, match="ollama pull qwen2.5:3b"):
        # Appel qui échoue
        make_client(handler).generate("s", "u")


def test_timeout_and_invalid_responses_raise_llm_error() -> None:
    def slow(request: httpx.Request) -> httpx.Response:
        # Simule un délai dépassé
        raise httpx.ReadTimeout("trop long", request=request)

    def garbage(request: httpx.Request) -> httpx.Response:
        # Réponse 200 mais sans le champ "message"
        return httpx.Response(200, json={"inattendu": True})

    # Délai dépassé
    with pytest.raises(LLMError, match="à temps"):
        # Appel qui échoue
        make_client(slow).generate("s", "u")

    # Réponse illisible
    with pytest.raises(LLMError, match="illisible"):
        # Appel qui échoue
        make_client(garbage).generate("s", "u")


def test_is_available_checks_that_the_model_is_installed() -> None:
    def with_model(request: httpx.Request) -> httpx.Response:
        # /api/tags liste les modèles installés
        return httpx.Response(200, json={"models": [{"name": "qwen2.5:3b"}]})

    def without_model(request: httpx.Request) -> httpx.Response:
        # Un autre modèle seulement
        return httpx.Response(200, json={"models": [{"name": "llama3.2:3b"}]})

    def offline(request: httpx.Request) -> httpx.Response:
        # Serveur éteint
        raise httpx.ConnectError("refus", request=request)

    # Disponible seulement si le modèle configuré est installé et le serveur joignable
    assert make_client(with_model).is_available()
    assert not make_client(without_model).is_available()
    assert not make_client(offline).is_available()
