"""Client HTTP de l'API RAG, utilisé par l'interface Streamlit.

L'interface ne touche JAMAIS directement au pipeline, à ChromaDB ou au LLM : elle
passe par l'API, comme le ferait n'importe quel autre client. Ce module isole les
appels HTTP pour qu'ils soient testables sans lancer Streamlit.
"""

# Any : les réponses JSON sont des dictionnaires aux valeurs variées
from typing import Any

# httpx : client HTTP
import httpx

# Délais : connexion rapide (API locale), réponse longue possible (génération par le LLM)
DEFAULT_TIMEOUT = httpx.Timeout(180.0, connect=2.0)


class ApiError(RuntimeError):
    """L'API a répondu par une erreur, ou n'a pas pu être jointe."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        # Message lisible, affiché tel quel dans l'interface
        super().__init__(message)

        # Code HTTP (None si l'API est injoignable)
        self.status_code = status_code


class RAGApiClient:
    """Une méthode par route de l'API."""

    def __init__(self, base_url: str, http_client: httpx.Client | None = None) -> None:
        """``http_client`` permet d'injecter un faux transport en test."""
        # Client HTTP partagé par tous les appels
        self._http = http_client or httpx.Client(
            base_url=base_url, timeout=DEFAULT_TIMEOUT
        )

        # Adresse affichée dans les messages d'erreur
        self.base_url = base_url

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Envoie une requête et renvoie le JSON ; toute erreur devient une ApiError."""
        # Les erreurs réseau sont traduites en message compréhensible
        try:
            # Requête HTTP
            response = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as error:
            # API éteinte ou injoignable
            raise ApiError(
                f"API injoignable à {self.base_url} : lancez « uvicorn app.main:app »"
            ) from error

        # Réponse d'erreur : FastAPI met l'explication dans le champ "detail"
        if response.is_error:
            # Le détail peut être un texte ou une liste (erreurs de validation Pydantic)
            try:
                # Lecture du champ detail
                detail = response.json().get("detail", response.text)
            except ValueError:
                # Corps non JSON
                detail = response.text

            # Erreur avec son code HTTP
            raise ApiError(
                f"Erreur {response.status_code} : {detail}", response.status_code
            )

        # Corps JSON décodé
        return response.json()

    def health(self) -> dict[str, Any]:
        """État de l'API, de l'index et du LLM."""
        # GET /health
        return self._request("GET", "/health")

    def list_documents(self) -> list[dict[str, Any]]:
        """Documents indexés."""
        # GET /documents
        return self._request("GET", "/documents")

    def upload(self, filename: str, content: bytes) -> dict[str, Any]:
        """Envoie un PDF à indexer."""
        # POST /documents en multipart (champ "file")
        return self._request(
            "POST", "/documents", files={"file": (filename, content, "application/pdf")}
        )

    def delete(self, document_id: str) -> dict[str, Any]:
        """Retire un document de l'index."""
        # DELETE /documents/{id}
        return self._request("DELETE", f"/documents/{document_id}")

    def ask(self, question: str) -> dict[str, Any]:
        """Pose une question ; renvoie la réponse et ses sources."""
        # POST /ask avec un corps JSON
        return self._request("POST", "/ask", json={"question": question})
