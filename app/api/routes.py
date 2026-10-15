"""Routes HTTP de l'API : elles traduisent HTTP ⇄ appels au pipeline RAG.

Aucune logique RAG ici : chaque route valide l'entrée, appelle la façade
RAGPipeline, puis convertit le résultat (ou l'erreur) en réponse HTTP.

    GET    /health                  état de l'index et du LLM
    POST   /ask                     question → réponse citée
    GET    /documents               documents indexés
    POST   /documents               envoi d'un PDF → indexation
    DELETE /documents/{document_id} retrait d'un document
"""

# logging pour tracer les fichiers reçus
import logging

# Path représente un chemin de fichier
from pathlib import Path

# Annotated : associe un type et sa dépendance FastAPI (forme recommandée)
from typing import Annotated

# Outils FastAPI : routeur, dépendances, fichiers envoyés, erreurs HTTP, objet requête
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

# Les contrats d'entrée / sortie
from app.api.schemas import (
    AskRequest,
    AskResponse,
    DeleteResponse,
    DocumentOut,
    HealthResponse,
    IngestResponse,
)

# Configuration (taille maximale des envois)
from app.core.config import Settings

# Erreurs du LLM, à traduire en codes HTTP
from app.generation.llm import LLMError, LLMUnavailableError

# La façade du RAG
from app.rag.pipeline import RAGPipeline

# Logger nommé d'après le module : "app.api.routes"
logger = logging.getLogger(__name__)

# Routeur regroupant toutes les routes (branché sur l'application dans app/main.py)
router = APIRouter()

# Signature de début d'un fichier PDF (« nombre magique ») : un vrai PDF commence par %PDF-
PDF_MAGIC = b"%PDF-"


def get_pipeline(request: Request) -> RAGPipeline:
    """Dépendance FastAPI : le pipeline créé au démarrage (remplaçable en test)."""
    # Le pipeline est rangé dans l'état de l'application par app/main.py
    return request.app.state.pipeline


def get_settings_dependency(request: Request) -> Settings:
    """Dépendance FastAPI : la configuration de l'application."""
    # La configuration est rangée dans l'état de l'application par app/main.py
    return request.app.state.settings


# Types annotés : « un RAGPipeline fourni par get_pipeline », réutilisables dans chaque route
PipelineDep = Annotated[RAGPipeline, Depends(get_pipeline)]
SettingsDep = Annotated[Settings, Depends(get_settings_dependency)]


@router.get("/health", response_model=HealthResponse, tags=["système"])
def health(pipeline: PipelineDep) -> HealthResponse:
    """Indique si l'API répond, ce que contient l'index et si le LLM est disponible."""
    # Le client LLM sait-il vérifier sa disponibilité ? (un faux LLM de test peut ne pas le savoir)
    is_available = getattr(pipeline.qa.llm, "is_available", None)

    # État de chaque brique
    return HealthResponse(
        status="ok",
        documents=len(pipeline.list_documents()),
        chunks=pipeline.ingestion.store.count(),
        llm_available=bool(is_available()) if callable(is_available) else False,
        llm_model=str(getattr(pipeline.qa.llm, "model", "inconnu")),
    )


@router.post("/ask", response_model=AskResponse, tags=["questions"])
def ask(body: AskRequest, pipeline: PipelineDep) -> AskResponse:
    """Pose une question : renvoie la réponse, les sources numérotées et les citations."""
    # Les erreurs internes sont traduites en codes HTTP explicites
    try:
        # Recherche + génération
        result = pipeline.ask(body.question)
    except ValueError as error:
        # Question invalide (ex. uniquement des espaces) : 422 Unprocessable Entity
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)
        ) from error
    except LLMUnavailableError as error:
        # Ollama éteint : 503 Service Unavailable (le client peut réessayer plus tard)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(error)) from error
    except LLMError as error:
        # Ollama a répondu, mais mal (modèle absent, délai) : 502 Bad Gateway
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(error)) from error

    # Conversion vers le schéma de réponse
    return AskResponse.from_answer(result)


@router.get("/documents", response_model=list[DocumentOut], tags=["documents"])
def list_documents(pipeline: PipelineDep) -> list[DocumentOut]:
    """Liste les documents présents dans l'index."""
    # Un DocumentOut par document indexé
    return [DocumentOut(**document) for document in pipeline.list_documents()]


@router.post(
    "/documents",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["documents"],
)
def upload_document(
    file: Annotated[UploadFile, File(description="Fichier PDF à indexer")],
    pipeline: PipelineDep,
    settings: SettingsDep,
) -> IngestResponse:
    """Reçoit un PDF, l'enregistre dans data/raw/ puis l'indexe."""
    # Path(...).name ne garde que le nom : "../../etc/x.pdf" devient "x.pdf" (pas de sortie du dossier)
    filename = Path(file.filename or "").name

    # Seuls les fichiers .pdf sont acceptés
    if not filename.lower().endswith(".pdf"):
        # 415 Unsupported Media Type
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "seuls les fichiers .pdf sont acceptés",
        )

    # Taille maximale autorisée, en octets
    max_bytes = settings.max_upload_mb * 1024 * 1024

    # Lit au plus max_bytes + 1 octets : suffisant pour savoir si la limite est dépassée
    content = file.file.read(max_bytes + 1)

    # Fichier trop gros
    if len(content) > max_bytes:
        # 413 Content Too Large
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"fichier trop volumineux (maximum {settings.max_upload_mb} Mo)",
        )

    # L'extension ne suffit pas : on vérifie la signature d'un vrai PDF
    if not content.startswith(PDF_MAGIC):
        # 415 : le contenu n'est pas un PDF
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "le contenu n'est pas un PDF valide"
        )

    # Chemin de destination dans data/raw/
    destination = pipeline.raw_data_dir / filename

    # Un AUTRE fichier porte déjà ce nom : on refuse plutôt que de l'écraser
    if destination.exists() and destination.read_bytes() != content:
        # 409 Conflict
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"un autre document s'appelle déjà {filename!r} : renommez le fichier",
        )

    # Enregistre le fichier (crée data/raw/ si besoin)
    pipeline.raw_data_dir.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    logger.info("PDF reçu : %s (%d octets)", filename, len(content))

    # Indexation (sautée si ce contenu est déjà indexé)
    report = pipeline.ingest_pdf(destination)

    # PDF illisible ou sans texte : 422, et on ne garde pas un fichier inutilisable
    if report.status == "error":
        # Supprime le fichier enregistré
        destination.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, report.message)

    # Compte rendu (201 si indexé ; "skipped" signale un document déjà présent)
    return IngestResponse.from_report(report)


@router.delete(
    "/documents/{document_id}", response_model=DeleteResponse, tags=["documents"]
)
def delete_document(document_id: str, pipeline: PipelineDep) -> DeleteResponse:
    """Retire un document de l'index et supprime son fichier de data/raw/."""
    # Retrouve le nom du fichier avant la suppression (pour effacer aussi le PDF)
    sources = {
        str(doc["document_id"]): str(doc["source"]) for doc in pipeline.list_documents()
    }

    # Document inconnu : 404 Not Found
    if document_id not in sources:
        # Erreur explicite
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"document inconnu : {document_id}"
        )

    # Supprime les chunks de l'index
    deleted = pipeline.delete_document(document_id)

    # Supprime le PDF, sinon il serait réindexé au prochain build_index
    (pipeline.raw_data_dir / sources[document_id]).unlink(missing_ok=True)

    # Compte rendu
    return DeleteResponse(document_id=document_id, deleted_chunks=deleted)
