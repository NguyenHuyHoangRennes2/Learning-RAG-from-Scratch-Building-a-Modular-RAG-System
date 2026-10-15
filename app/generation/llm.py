"""Client du LLM local Ollama, via son API REST (http://127.0.0.1:11434).

On appelle l'API HTTP « à la main » avec httpx (et non avec le paquet ``ollama``) :
chaque requête est visible et explicite, ce qui est plus pédagogique.

Le reste de l'application ne dépend que du protocole ``LLMClient`` : changer de
fournisseur (autre serveur local, API externe) ne demanderait qu'une nouvelle classe.
"""

# logging pour tracer les appels (modèle, durée)
import logging

# time.perf_counter : mesure de la durée de génération
import time

# Protocol : décrit la forme attendue d'un client LLM
from typing import Protocol

# httpx : client HTTP (déjà utilisé pour tester FastAPI en Phase 9)
import httpx

# Logger nommé d'après le module : "app.generation.llm"
logger = logging.getLogger(__name__)

# Délai maximal pour ÉTABLIR la connexion avec Ollama (serveur local : quelques ms suffisent)
CONNECT_TIMEOUT_SECONDS = 1.0


class LLMError(RuntimeError):
    """Le LLM n'a pas pu produire de réponse (modèle absent, délai dépassé, réponse invalide)."""


class LLMUnavailableError(LLMError):
    """Le serveur du LLM est injoignable (Ollama n'est pas lancé ou pas installé)."""


class LLMClient(Protocol):
    """Ce dont le pipeline RAG a besoin : générer un texte à partir de deux messages."""

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Renvoie la réponse du LLM."""
        ...


class OllamaClient:
    """Appelle ``POST /api/chat`` d'Ollama, sans streaming."""

    def __init__(
        self,
        base_url: str,
        model: str,
        temperature: float = 0.1,
        num_ctx: int = 4096,
        timeout_seconds: float = 120.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        """Prépare le client ; ``http_client`` permet d'injecter un faux transport en test."""
        # Nom du modèle Ollama, ex. "qwen2.5:3b"
        self.model = model

        # Adresse du serveur (sans "/" final, pour concaténer proprement les chemins)
        self.base_url = base_url.rstrip("/")

        # Options de génération transmises à Ollama
        self.options = {"temperature": temperature, "num_ctx": num_ctx}

        # Délais : la GÉNÉRATION peut être longue, mais la CONNEXION à un serveur local
        # doit être quasi instantanée. Sans connect=1.0, un Ollama absent coûtait ~4 s
        # par requête sous Windows (mesuré en Phase 9).
        timeout = httpx.Timeout(timeout_seconds, connect=CONNECT_TIMEOUT_SECONDS)

        # Client HTTP réutilisé pour tous les appels (connexions gardées ouvertes)
        self._http = http_client or httpx.Client(
            base_url=self.base_url, timeout=timeout
        )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Envoie les deux messages et renvoie le texte généré."""
        # Corps de la requête : modèle, conversation, réponse en un seul bloc, options
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "options": self.options,
        }

        # Chronomètre la génération
        start = time.perf_counter()

        # Les erreurs réseau sont traduites en erreurs métier explicites
        try:
            # Appel HTTP à l'API de chat d'Ollama
            response = self._http.post("/api/chat", json=payload)
        except (httpx.ConnectError, httpx.ConnectTimeout) as error:
            # ConnectTimeout est testé AVANT TimeoutException (dont il hérite) : c'est une absence de serveur
            # Serveur absent : message qui dit QUOI faire
            raise LLMUnavailableError(
                f"Ollama est injoignable à {self.base_url}. "
                "Installez-le (https://ollama.com) puis lancez-le, ou vérifiez RAG_OLLAMA_BASE_URL."
            ) from error
        except httpx.TimeoutException as error:
            # Génération trop longue
            raise LLMError(f"Ollama n'a pas répondu à temps ({self.model})") from error

        # Modèle non téléchargé : Ollama répond 404
        if response.status_code == 404:
            # Message qui donne la commande à lancer
            raise LLMError(
                f"Le modèle {self.model!r} n'est pas disponible dans Ollama : "
                f"lancez « ollama pull {self.model} »"
            )

        # Toute autre erreur HTTP (500...)
        if response.is_error:
            # Le corps de la réponse contient souvent l'explication
            raise LLMError(
                f"Erreur Ollama {response.status_code} : {response.text[:200]}"
            )

        # Extrait le texte de la réponse : {"message": {"role": "assistant", "content": "..."}}
        try:
            # Décodage JSON puis accès au contenu
            content = response.json()["message"]["content"]
        except (ValueError, KeyError, TypeError) as error:
            # Réponse inattendue
            raise LLMError("Réponse d'Ollama illisible") from error

        # Trace la durée (utile pour mesurer la latence)
        logger.info("Réponse de %s en %.1f s", self.model, time.perf_counter() - start)

        # Renvoie le texte sans espaces superflus
        return str(content).strip()

    def is_available(self) -> bool:
        """Vrai si Ollama répond ET si le modèle configuré est téléchargé."""
        # GET /api/tags liste les modèles installés
        try:
            # Appel léger, sans génération
            response = self._http.get("/api/tags")
        except httpx.HTTPError:
            # Serveur injoignable
            return False

        # Réponse invalide : considéré comme indisponible
        if response.is_error:
            # Pas disponible
            return False

        # Noms des modèles installés, ex. ["qwen2.5:3b", "llama3.2:3b"]
        names = [model.get("name", "") for model in response.json().get("models", [])]

        # Disponible si le modèle configuré est dans la liste
        return self.model in names
