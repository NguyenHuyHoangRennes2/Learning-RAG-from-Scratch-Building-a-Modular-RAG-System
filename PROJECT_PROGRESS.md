# PROJECT_PROGRESS.md — Suivi du projet RAG

Dépôt GitHub : https://github.com/NguyenHuyHoangRennes2/Learning-RAG-from-Scratch-Building-a-Modular-RAG-System

## Phase en cours

> **Mode autonome (2026-10-15)** : l'étudiant a demandé de terminer le projet jusqu'à la Phase 12 **sans validation intermédiaire**. Il évaluera l'ensemble à la fin. Les étapes suivantes sont donc marquées « Terminée (mode autonome) » et non « Validée ». Chaque étape reste documentée ici (résultats réels) et dans `NOTES_APPRENTISSAGE.md`.

## Phase 10 — Interface Streamlit

| Étape | Titre | Statut |
|---|---|---|
| 10.1 | Client HTTP de l'API (`frontend/api_client.py`) | ✅ Terminée (2026-10-15, mode autonome) |
| 10.2 | Interface (`frontend/streamlit_app.py`) : état, envoi/suppression de PDF, questions, sources citées | ✅ Terminée (2026-10-15, mode autonome) |
| 10.3 | Tests (`MockTransport`, `AppTest`) + essai avec la vraie API ; statistiques Streamlit désactivées | ✅ Terminée (2026-10-15, mode autonome) |

**Phase 10 terminée le 2026-10-15.**

## Phase 9 — API REST (FastAPI)

| Étape | Titre | Statut |
|---|---|---|
| 9.1 | Dépendances (`fastapi`, `uvicorn`, `python-multipart`) et schémas Pydantic (`app/api/schemas.py`) | ✅ Terminée (2026-10-15, mode autonome) |
| 9.2 | Routes (`app/api/routes.py`) et application (`app/main.py`) | ✅ Terminée (2026-10-15, mode autonome) |
| 9.3 | Tests `TestClient` + essais avec le vrai serveur uvicorn ; 3 corrections issues des mesures | ✅ Terminée (2026-10-15, mode autonome) |

**Phase 9 terminée le 2026-10-15.**

## Phase 8 — Pipeline RAG complet

| Étape | Titre | Statut |
|---|---|---|
| 8.1 | Structure `RAGAnswer` (`app/models.py`) | ✅ Terminée (2026-10-15, mode autonome) |
| 8.2 | `QuestionAnsweringPipeline`, façade `RAGPipeline`, `build_pipeline(settings)` (`app/rag/pipeline.py`) | ✅ Terminée (2026-10-15, mode autonome) |
| 8.3 | `scripts/ask.py` (CLI) ; `build_index.py` simplifié | ✅ Terminée (2026-10-15, mode autonome), génération réelle non testée (Ollama absent) |

**Phase 8 terminée le 2026-10-15.**

## Phase 7 — Intégration du LLM (Ollama)

| Étape | Titre | Statut |
|---|---|---|
| 7.1 | Paramètres Ollama dans la configuration | ✅ Terminée (2026-10-15, mode autonome) |
| 7.2 | Prompts (`app/generation/prompts.py`) : consignes, sources numérotées, anti-injection, citations, abstention | ✅ Terminée (2026-10-15, mode autonome) |
| 7.3 | Client Ollama (`app/generation/llm.py`) + `scripts/check_ollama.py` | ⚠️ Terminée, testée **avec un faux serveur uniquement** : Ollama n'est pas installé |

**Phase 7 terminée le 2026-10-15**, avec un blocage documenté (voir « Problèmes connus »).

## Phase 6 — Recherche sémantique et évaluation de la recherche

| Étape | Titre | Statut |
|---|---|---|
| 6.1 | `Retriever` (`app/retrieval/retriever.py`) : Top-K + seuil optionnel | ✅ Terminée (2026-10-15, mode autonome) |
| 6.2 | Métriques (`app/evaluation/metrics.py`) et jeu de 20 questions de référence (`evaluation/questions.json`) | ✅ Terminée (2026-10-15, mode autonome) |
| 6.3 | Comparaison de 4 réglages (`scripts/evaluate_retrieval.py`) → nouveaux réglages par défaut | ✅ Terminée (2026-10-15, mode autonome) |

**Phase 6 terminée le 2026-10-15.**

## Phase 5 — Base vectorielle (ChromaDB)

| Étape | Titre | Statut |
|---|---|---|
| 5.1 | `SearchResult` et `Chunk.citation` (`app/models.py`), nom de collection dans la configuration | ✅ Terminée (2026-10-15, mode autonome) |
| 5.2 | `ChromaStore` (`app/vectorstore/chroma_store.py`) : upsert, recherche, suppression, garde-fou « même modèle » | ✅ Terminée (2026-10-15, mode autonome) |
| 5.3 | Flux d'indexation `IngestionPipeline` (`app/rag/pipeline.py`) + `scripts/build_index.py` | ✅ Terminée (2026-10-15, mode autonome) |

**Phase 5 terminée le 2026-10-15.**

## Phase 4 — Embeddings

| Étape | Titre | Statut |
|---|---|---|
| 4.1 | Choix du modèle et paramètres dans la configuration | ✅ Terminée (2026-10-15, mode autonome) |
| 4.2 | Module `app/embeddings/embedding_model.py` (préfixes E5, normalisation, cosinus) | ✅ Terminée (2026-10-15, mode autonome) |
| 4.3 | Mesures réelles (tokens, vitesse, similarités) et tests avec le vrai modèle | ✅ Terminée (2026-10-15, mode autonome) |

**Phase 4 terminée le 2026-10-15.**

## Phase 3 — Chunking

| Étape | Titre | Statut |
|---|---|---|
| 3.1 | Principes du chunking + paramètres dans la configuration | ✅ Validée (2026-10-12) |
| 3.2 | Structure de données `Chunk` (`app/models.py`) | ✅ Validée (2026-10-15) |
| 3.3 | Chunker, stratégie « fixed » (`app/ingestion/chunker.py`) | ✅ Validée (2026-10-15) |
| 3.4 | Chunker, stratégie « sentence » (`app/ingestion/chunker.py`) | ✅ Validée (2026-10-15) |
| 3.5 | Comparaison des stratégies sur les vrais PDF (script + test d'intégration) + correction des titres orphelins | ✅ Terminée (2026-10-15, mode autonome) |

**Phase 3 terminée le 2026-10-15.**

## Phase 2 — Ingestion

| Étape | Titre | Statut |
|---|---|---|
| 2.1 | Le format PDF et exploration de nos documents | ✅ Validée (2026-10-11) |
| 2.2 | Structure de données d'une page (`app/models.py`) | ✅ Validée (2026-10-11) |
| 2.3 | Chargeur PDF (`app/ingestion/pdf_loader.py`) | ✅ Validée (2026-10-11) |
| 2.4 | Nettoyage du texte (`app/ingestion/text_cleaner.py`) | ✅ Validée (2026-10-11) |
| 2.5 | Validation sur les vrais PDF (test d'intégration + export `data/processed/`) | ✅ Validée (2026-10-11) |

**Phase 2 terminée le 2026-10-11.**

## Phase 1 — Initialisation

## Sous-étapes

| Étape | Titre | Statut |
|---|---|---|
| 1.1 | Préparation de l'environnement de développement | ✅ Validée (2026-10-11) |
| 1.2 | Arborescence du projet et packages Python | ✅ Validée (2026-10-11) |
| 1.3 | Environnement virtuel Python | ✅ Validée (2026-10-11) |
| 1.4 | Gestion des dépendances | ✅ Validée (2026-10-11) |
| 1.5-A | Configuration centralisée (`config.py`, `.env.example`) | ✅ Validée (2026-10-11) |
| 1.5-B | Logging (`logging_config.py`) | ✅ Validée (2026-10-11) |
| 1.6 | Git : `.gitignore`, premier commit, GitHub | ✅ Validée (2026-10-11) |

**Phase 1 terminée le 2026-10-11.**

## Fichiers créés ou modifiés

| Fichier | Étape | Rôle |
|---|---|---|
| `PROJECT_PROGRESS.md` | 1.1 | Suivi de l'avancement |
| `NOTES_APPRENTISSAGE.md` | 1.3 | Carnet de révision : actions et définitions de chaque étape |
| `.venv/` | 1.3 | Environnement virtuel Python 3.13.14 (non versionné) |
| `requirements.txt` | 1.4 | Dépendances d'exécution, versions figées |
| `requirements-dev.txt` | 1.4 | Dépendances de dev (pytest, ruff) + `-r requirements.txt` |
| `app/core/config.py` | 1.5-A | Classe `Settings` (pydantic-settings), `PROJECT_ROOT`, `get_settings()` |
| `.env.example` | 1.5-A | Modèle documenté du fichier `.env` (commité, sans secrets) |
| `tests/unit/test_config.py` | 1.5-A | 4 tests : valeurs par défaut, surcharge par l'environnement, chemins relatifs, validation |
| `app/core/logging_config.py` | 1.5-B | `setup_logging()` : niveau, format, handler console, bibliothèques bavardes réduites au silence |
| `tests/unit/test_logging_config.py` | 1.5-B | 4 tests : niveau, pas de doublon de handler, bibliothèques bavardes, filtrage par niveau |
| `.gitignore` | 1.6 | Exclut `.venv/`, `.env`, caches, `__pycache__`, contenu de `data/` et `storage/` (sauf `.gitkeep`) |
| `README.md` | 1.6 | README minimal (installation, tests) ; version complète en Phase 12 |
| `.git/` | 1.6 | Dépôt Git local (`git init`, branche `main`) |
| `scripts/inspect_pdfs.py` | 2.1 | Script d'exploration : pages, métadonnées, aperçu brut du texte de chaque PDF |
| `app/models.py` | 2.2 | Dataclass `DocumentPage` (document_id, source, page_number, text), immuable et validée |
| `tests/unit/test_models.py` | 2.2 | 6 tests : valeurs, 3 validations, immuabilité, `replace()` |
| `app/ingestion/pdf_loader.py` | 2.3 | `compute_document_id`, `load_pdf`, `load_pdfs_from_directory`, `PDFLoadError` |
| `tests/unit/test_pdf_loader.py` | 2.3 | 9 tests sur des PDF générés dans `tmp_path` |
| `app/ingestion/text_cleaner.py` | 2.4 | `normalize_unicode`, `join_wrapped_lines`, `clean_text`, `remove_repeated_lines`, `clean_pages` |
| `tests/unit/test_text_cleaner.py` | 2.4 | 14 tests : Unicode, recollage des lignes, titres, en-têtes répétés, pipeline complet |
| `scripts/ingest_preview.py` | 2.5 | Point d'entrée : PDF → pages nettoyées → un JSON par document dans `data/processed/` (`export_pages`) |
| `tests/integration/test_ingestion_pipeline.py` | 2.5 | 2 tests d'intégration : chargeur + nettoyage, puis export JSON, sur un PDF réaliste généré |
| `app/core/config.py` (modifié) | 3.1 | + `chunk_size=800`, `chunk_overlap=150`, `chunk_strategy="sentence"`, validateur `overlap < size` |
| `.env.example` (modifié) | 3.1 | + variables `RAG_CHUNK_SIZE`, `RAG_CHUNK_OVERLAP`, `RAG_CHUNK_STRATEGY` |
| `tests/unit/test_config.py` (modifié) | 3.1 | + 4 tests sur les paramètres de chunking (8 au total) |
| `app/models.py` (modifié) | 3.2 | + dataclass `Chunk` (propriété calculée `chunk_id`) ; validation commune extraite dans `_validate_origin()` |
| `tests/unit/test_models.py` (modifié) | 3.2 | + 6 tests sur `Chunk` (12 au total) |
| `app/ingestion/chunker.py` | 3.3 | `split_text_fixed` (texte → fenêtres), `chunk_page_fixed` (page → `Chunk`), `_validate_chunk_params` |
| `tests/unit/test_chunker.py` | 3.3 | 13 tests (dont 4 cas paramétrés de paramètres invalides) |
| `app/ingestion/chunker.py` (modifié) | 3.4 | + `split_sentences`, `split_text_sentence`, `_overlap_tail`, `_joined_length` ; table `SPLITTERS` ; `chunk_page_fixed` remplacé par `chunk_page(..., strategy)` ; + `chunk_pages` |
| `tests/unit/test_chunker.py` (modifié) | 3.4 | 25 tests : anciens tests adaptés à `chunk_page(strategy="fixed")`, + 12 nouveaux |
| `scripts/compare_chunking.py` | 3.5 | Point d'entrée : compare « fixed » et « sentence » (`ChunkingStats`, `compute_stats`, options `--size` et `--overlap`) |
| `tests/integration/test_chunking_pipeline.py` | 3.5 | 4 tests d'intégration : PDF → chargeur → nettoyage → chunks → statistiques |
| `app/ingestion/chunker.py`, `text_cleaner.py` (modifiés) | 3.5 | + `attach_headings()` ; `_is_heading` → `is_heading` (publique) |
| `tests/unit/test_chunker.py` (modifié) | 3.5 | + 4 tests sur les titres (29 au total) |
| `app/core/config.py`, `.env.example`, `tests/unit/test_config.py` (modifiés) | 4.1 | + `embedding_model_name`, `embedding_device`, `embedding_batch_size` ; + 1 test (9 au total) |
| `app/embeddings/embedding_model.py` | 4.2 | `EmbeddingModel` (`embed_documents`, `embed_query`, `dimension`, chargement paresseux), `prefixes_for_model`, `cosine_similarity`, protocole `TextEncoder` |
| `tests/unit/test_embedding_model.py` | 4.2 | 11 tests avec un faux encodeur (aucun téléchargement) |
| `pytest.ini` | 4.3 | Marqueur `slow` ; les tests lents sont exclus par défaut (`-m "not slow"`) |
| `tests/integration/test_embeddings_real_model.py` | 4.3 | 2 tests `slow` avec le vrai modèle (dimension, norme, pertinence) |
| `scripts/inspect_embeddings.py` | 4.3 | Mesures : tokens par chunk, troncature, vitesse, similarités |
| `app/models.py` (modifié) | 5.1 | + `Chunk.citation` (« fichier.pdf, p. N ») ; + dataclass `SearchResult(chunk, score)` |
| `app/core/config.py`, `.env.example` (modifiés) | 5.1 | + `chroma_collection_name="rag_chunks"` |
| `tests/unit/test_models.py` (modifié) | 5.1 | + 2 tests (14 au total) |
| `app/vectorstore/chroma_store.py` | 5.2 | `ChromaStore` : `add_chunks` (upsert par lots), `search`, `count`, `has_document`, `delete_document`, `list_documents` ; `EmbeddingModelMismatchError` |
| `tests/integration/test_chroma_store.py` | 5.2 | 9 tests avec une vraie ChromaDB dans `tmp_path` |
| `app/rag/pipeline.py` | 5.3 | `IngestionPipeline` (`ingest_pdf`, `ingest_directory`), `IngestionReport` |
| `scripts/build_index.py` | 5.3 | Point d'entrée : indexe `data/raw/` (option `--replace`) |
| `tests/fakes.py` | 5.3 | `KeywordEncoder` : faux modèle d'embeddings par mots-clés, partagé par les tests |
| `tests/integration/test_ingestion_to_index.py` | 5.3 | 5 tests : dossier, doublons, `--replace`, recherche, dossier absent |
| `app/retrieval/retriever.py` | 6.1 | `Retriever(embedder, store, top_k, min_score).retrieve(question, top_k=None)` |
| `tests/integration/test_retriever.py` | 6.1 | 4 tests (ordre, top_k par appel, seuil, top_k invalide) |
| `app/evaluation/` (nouveau package) | 6.2 | `metrics.py` (Precision@K, Recall@K, RR, MRR), `dataset.py` (`EvalQuestion`, `load_questions`, `find_missing_evidence`), `retrieval_eval.py` (`evaluate_retrieval`, `RetrievalEvaluation`) |
| `evaluation/questions.json` | 6.2 | 20 questions : 7 faciles, 6 paraphrases, 3 multi-documents, 4 sans réponse ; preuves = extraits exacts du corpus |
| `tests/unit/test_metrics.py`, `tests/unit/test_dataset.py` | 6.2 | 8 + 2 tests (exemples chiffrés du document 3 du corpus) |
| `tests/integration/test_retrieval_eval.py` | 6.3 | 1 test de la boucle d'évaluation |
| `scripts/evaluate_retrieval.py` | 6.3 | Compare 4 réglages de chunking × K ∈ {3, 5} ; écrit `evaluation/results/retrieval.json` |
| `evaluation/results/retrieval.json` | 6.3 | Trace versionnée des mesures |
| `app/core/config.py`, `.env.example`, `tests/unit/test_config.py` (modifiés) | 6.3 | Chunking **400/50** (au lieu de 800/150) ; + `retrieval_top_k=5`, `retrieval_min_score=0.0` ; + 2 tests (11 au total) |
| `app/core/config.py`, `.env.example`, `tests/unit/test_config.py` (modifiés) | 7.1 | + `ollama_base_url`, `ollama_model="qwen2.5:3b"`, `llm_temperature=0.1`, `llm_num_ctx=4096`, `llm_timeout_seconds=120` ; + 1 test (12 au total) |
| `app/generation/prompts.py` | 7.2 | `SYSTEM_PROMPT`, `NO_ANSWER_MESSAGE`, `build_context`, `build_user_prompt`, `extract_citations`, `is_no_answer` |
| `tests/unit/test_prompts.py` | 7.2 | 7 tests (numérotation, injection neutralisée, citations inventées ignorées, abstention) |
| `app/generation/llm.py` | 7.3 | Protocole `LLMClient` ; `OllamaClient` (`generate`, `is_available`) ; `LLMError`, `LLMUnavailableError` |
| `tests/unit/test_llm.py` | 7.3 | 5 tests avec `httpx.MockTransport` (requête envoyée, serveur éteint, modèle absent, délai, réponse invalide, disponibilité) |
| `scripts/check_ollama.py` | 7.3 | Diagnostic : serveur joignable ? modèle installé ? génération OK ? |
| `app/models.py` (modifié) | 8.1 | + `RAGAnswer` (question, answer, sources, cited, abstained, retrieval_ms, generation_ms, `cited_sources`) |
| `app/rag/pipeline.py` (modifié) | 8.2 | + `QuestionAnsweringPipeline.ask`, `RAGPipeline` (façade : ask, ingest_pdf, ingest_directory, list_documents, delete_document), `build_pipeline(settings, llm=None)` |
| `tests/fakes.py` (modifié) | 8.2 | + `FakeLLM` (réponse scénarisée, mémorise les prompts) |
| `tests/integration/test_rag_pipeline.py` | 8.2 | 7 tests de bout en bout (faux LLM) |
| `scripts/ask.py` | 8.3 | CLI : question → réponse + sources + latences ; sans Ollama, affiche les passages retrouvés |
| `scripts/build_index.py` (modifié) | 8.3 | Utilise `build_pipeline` |
| `requirements.txt` (modifié) | 9.1 | + `fastapi==0.143.1`, `uvicorn==0.54.0`, `python-multipart==0.0.32` |
| `app/core/config.py`, `.env.example` (modifiés) | 9.1 | + `max_upload_mb=20` ; URL Ollama par défaut → `http://127.0.0.1:11434` |
| `app/api/schemas.py` | 9.1 | `AskRequest`, `AskResponse` (+`SourceOut`), `IngestResponse`, `DocumentOut`, `DeleteResponse`, `HealthResponse` |
| `app/api/routes.py` | 9.2 | `GET /health`, `POST /ask`, `GET /documents`, `POST /documents`, `DELETE /documents/{id}` ; dépendances `PipelineDep`, `SettingsDep` |
| `app/main.py` | 9.2 | `create_app(settings, pipeline)` avec cycle de vie (logging, pipeline, préchauffage du modèle) ; `app` pour uvicorn |
| `tests/fakes.py` (modifié) | 9.3 | + `make_fake_pipeline`, `pdf_bytes` |
| `tests/integration/test_api.py` | 9.3 | 16 tests (santé, envoi, doublon, 4 envois invalides, conflit de nom, traversée de chemin, question, 3 questions invalides, 503/502, suppression, OpenAPI) |
| `app/ingestion/pdf_loader.py` (modifié) | 9.3 | PDF ouvert depuis la mémoire (`stream=`) : plus de fichier verrouillé sous Windows |
| `requirements.txt` (modifié) | 10.1 | + `streamlit==1.66.0` |
| `app/core/config.py`, `.env.example` (modifiés) | 10.1 | + `api_base_url="http://127.0.0.1:8000"` |
| `frontend/__init__.py`, `frontend/api_client.py` | 10.1 | `RAGApiClient` (`health`, `list_documents`, `upload`, `delete`, `ask`), `ApiError` |
| `frontend/streamlit_app.py` | 10.2 | Barre latérale (état, envoi, liste + suppression), conversation (`st.chat_input`), réponse + sources dépliables avec ✅ pour les sources citées |
| `.streamlit/config.toml` | 10.3 | `gatherUsageStats = false`, `maxUploadSize = 20` |
| `tests/unit/test_api_client.py` | 10.3 | 5 tests (`httpx.MockTransport`) |
| `tests/integration/test_streamlit_app.py` | 10.3 | 1 test de fumée `AppTest` (API injoignable → message clair, pas d'exception) |
| `app/generation/llm.py` (modifié) | 9.3 | Délai de connexion de 1 s (`CONNECT_TIMEOUT_SECONDS`) ; `ConnectTimeout` → `LLMUnavailableError` ; + 1 test (6 au total) |
| `app/__init__.py` + 8 sous-packages (`core`, `ingestion`, `embeddings`, `vectorstore`, `retrieval`, `generation`, `rag`, `api`) | 1.2 | Packages Python (fichiers `__init__.py` vides) |
| `data/raw/.gitkeep`, `data/processed/.gitkeep`, `storage/chroma/.gitkeep` | 1.2 | Conserver les dossiers de données dans Git |
| Dossiers `frontend/`, `scripts/`, `tests/unit/`, `tests/integration/` | 1.2 | Squelette (vides) |

## Décisions techniques

- **Python 3.13** (déjà installé) plutôt que 3.12 : compatible avec PyTorch, ChromaDB et sentence-transformers. Repli sur 3.12 si une dépendance échoue à l'étape 1.4.
- Python 3.10 est aussi installé et c'est lui que `python` appelle par défaut. Il est trop ancien (le projet exige 3.11+). Tant que le venv n'existe pas, toujours utiliser `py -3.13`.
- L'arborescence de référence est celle de `CLAUDE.md`.
- **Dépendances** : `requirements.txt` (exécution) et `requirements-dev.txt` (dev) ; seules les dépendances directes sont figées en `==`. Pas de `pyproject.toml` pour l'instant.
- **PyTorch en version CPU** : sous Windows, c'est celle que fournit PyPI. Elle suffit pour les embeddings, et le GPU (4 Go) reste disponible pour Ollama.
- **`httpx` plutôt que le paquet `ollama`** : on appelle l'API REST d'Ollama explicitement, ce qui est plus pédagogique. `httpx` resservira pour tester FastAPI.
- FastAPI et Streamlit seront ajoutés en Phases 9 et 10, quand on en aura besoin.
- **Configuration** : pydantic-settings, préfixe `RAG_`, priorité variable d'environnement > `.env` > défaut. Les chemins relatifs sont résolus depuis `PROJECT_ROOT`. Les paramètres de chaque phase (chunking, embeddings, Ollama…) seront ajoutés à `Settings` au moment où on les étudiera.
- **Logging** : module standard `logging`, sans bibliothèque externe. `setup_logging()` n'est appelée qu'aux points d'entrée ; les modules utilisent `logging.getLogger(__name__)`. Sortie console sur stderr seulement (pas de fichier de log pour le MVP). Le fichier s'appelle `logging_config.py` pour ne pas masquer le module standard `logging`.
- **`app/models.py`** (écart avec l'arborescence de CLAUDE.md) : module commun pour les structures de données partagées (page, puis chunk et résultat de recherche). Il évite que `vectorstore` ou `retrieval` importent `ingestion`. On utilise des **dataclasses** (bibliothèque standard), et non Pydantic, qui sera réservé aux frontières de l'API (Phase 9).
- **`DocumentPage` immuable** (`frozen=True`) : chaque étape crée une nouvelle page (`dataclasses.replace`) au lieu de modifier l'existante.
- **`document_id`** = les 16 premiers caractères hexadécimaux du SHA-256 du **contenu** du fichier. Deux fichiers identiques portant des noms différents ont donc le même id, et le doublon n'est chargé qu'une fois.
- **Gestion des erreurs du chargeur** : une seule exception métier, `PDFLoadError` (fichier absent, corrompu ou protégé). Le chargement d'un dossier ignore les fichiers en erreur (`logger.error`) sans s'arrêter.
- **Pages sans texte** : ignorées avec un `logger.warning`, car elles sont peut-être scannées. Pas d'OCR pour le MVP.
- **Nettoyage par heuristiques simples et explicables** :
  - en-têtes et pieds de page = lignes présentes dans les 3 premières ou 3 dernières lignes de **toutes** les pages d'un document (chiffres masqués : « Page 1 » = « Page 2 ») ;
  - un saut de ligne est gardé après `. ! ? : »` ou autour d'un titre numéroté court ; sinon les lignes sont recollées ;
  - normalisation NFKC et apostrophes `’` → `'`.
  Pas de recollage des césures (`mot-\nsuite`), pour ne pas abîmer les mots composés ; nos PDF n'en contiennent pas.
- **Chunking — unité = caractères** : simple et sans dépendance. Le lien avec la limite en **tokens** du modèle d'embeddings sera **mesuré** en Phase 4 (estimation actuelle, non mesurée : 800 caractères ≈ 200 tokens).
- **Chunking — valeurs par défaut** : `chunk_size=800`, `chunk_overlap=150` (environ 19 %), `chunk_strategy="sentence"`. **Remplacées en 6.3 par 400/50, après mesure** (voir plus bas). Un chunk ne traverse jamais deux pages, pour que la citation de page reste exacte.
- **Deux stratégies** implémentées pour pouvoir les **comparer** : « fixed » (référence naïve) et « sentence » (par défaut).
- **`Chunk`** : des champs « à plat » (`document_id`, `source`, `page_number`, `chunk_index`, `text`), faciles à stocker comme métadonnées dans ChromaDB. `chunk_id` = `"<document_id>-p<page>-c<index>"` est une **propriété calculée**, donc toujours cohérente avec les champs. Comme il est déterministe, réindexer le même document produira les mêmes ids (dédoublonnage en Phase 5). `chunk_index` commence à 0 (identifiant interne), `page_number` à 1 (lu par les humains).
- **Chunker indépendant de la configuration** : `chunk_size` et `chunk_overlap` sont passés en paramètres explicites, et le chunker n'appelle pas `get_settings()`. Il revalide quand même ses paramètres (`_validate_chunk_params`), parce qu'un pas ≤ 0 provoquerait une boucle infinie si on l'appelait sans passer par `Settings`.
- **Stratégie « fixed »** : les fenêtres sont des tranches brutes (`text[start:end]`), sans `strip()`, ce qui permet de vérifier exactement la formule et le chevauchement. Une fenêtre faite uniquement d'espaces est ignorée, et la numérotation reste continue.
- **Stratégie « sentence »** :
  - découpage en phrases par une expression régulière : on coupe après `. ! ? …` suivi d'espaces puis d'une majuscule, sauf après « chiffre + point » (numéros de titre), et à chaque saut de ligne ;
  - les phrases sont regroupées de façon **gloutonne** jusqu'à `chunk_size` ;
  - le chevauchement se fait par **phrases entières** dans la limite de `chunk_overlap`, et il est réduit si nécessaire pour respecter `chunk_size` ;
  - une phrase plus longue que `chunk_size` est coupée par « fixed », seul cas où une phrase est coupée ;
  - les phrases sont recollées avec une espace, donc un titre se retrouve collé à la phrase qui le suit.
  Pas de NLTK ni de spaCy : une dépendance lourde n'est pas justifiée pour des textes propres.
- **`chunk_page(page, size, overlap, strategy)`** remplace `chunk_page_fixed` (3.3) : un seul point d'entrée et une table `SPLITTERS` (nom → fonction). Le type `ChunkStrategy` est importé depuis `config.py`, pour n'être défini qu'une fois.
- **Modèle d'embeddings : `intfloat/multilingual-e5-small`** (4.1). Il est multilingue (nos PDF sont en français), produit **384 dimensions**, accepte **512 tokens** et pèse environ 470 Mo. Il tourne sur CPU.
  - Rejeté : `paraphrase-multilingual-MiniLM-L12-v2`. Sa limite de 128 tokens aurait **tronqué** nos chunks (mesurés ensuite à 170 tokens en moyenne).
  - Rejeté : `BAAI/bge-m3`. Il est trop lourd (environ 2,2 Go) pour 8 Go de RAM partagés avec Ollama.
- **Préfixes E5** : `"query: "` pour les questions, `"passage: "` pour les chunks. Ils sont ajoutés **dans** `EmbeddingModel`, que l'appelant ne peut donc pas oublier. La fonction `prefixes_for_model()` les désactive pour un modèle non-E5.
- **Vecteurs normalisés** (`normalize_embeddings=True`) : la norme vaut 1, donc cosinus = produit scalaire. **Métrique de similarité : cosinus.**
- **Chargement paresseux** : le modèle (15 s) n'est chargé qu'au premier usage. **Injection** d'un encodeur (`encoder=`), qui permet des tests unitaires instantanés avec un faux encodeur. Le `Protocol` `TextEncoder` décrit ce dont on a besoin, sans dépendre de la classe `SentenceTransformer`.
- **Tests lents séparés** : ceux qui chargent le vrai modèle sont marqués `slow` et exclus par défaut (`pytest.ini`). On les lance avec `python -m pytest -m slow`.
- **ChromaDB** (5.2) :
  - client **persistant** (`storage/chroma/`) et une collection `rag_chunks` en espace **cosinus** (`configuration={"hnsw": {"space": "cosine"}}`) ;
  - `embedding_function=None`, car c'est notre `EmbeddingModel` qui calcule les vecteurs (sinon Chroma téléchargerait son propre modèle) ;
  - ChromaDB renvoie une **distance** $d = 1 - \cos$, convertie en **score** $s = 1 - d$ (plus grand = plus proche) ;
  - le nom du modèle d'embeddings est enregistré dans les métadonnées de la collection, et la rouvrir avec un autre modèle lève `EmbeddingModelMismatchError`. C'est la règle 6.3 de CLAUDE.md, vérifiée par le code.
- **Dédoublonnage** (5.3) : à deux niveaux.
  1. Par document : un `document_id` (hash du contenu) déjà présent est **sauté**, sans rien recalculer.
  2. Par chunk : `upsert` sur des `chunk_id` déterministes.
  `--replace` **supprime** d'abord les chunks du document : avec d'autres paramètres de chunking, d'anciens `chunk_id` resteraient sinon orphelins.
- **`app/rag/pipeline.py`** contient l'orchestration de l'ingestion (règle 5.1 de CLAUDE.md : `rag/` orchestre). La partie « question → réponse » y sera ajoutée en Phase 8.
- **Définition de la pertinence** (6.2) : un chunk est pertinent s'il **contient une preuve**, c'est-à-dire un extrait exact du corpus noté dans `questions.json`. Cette définition est **indépendante du découpage**, ce qui permet de comparer équitablement les stratégies de chunking. `find_missing_evidence` vérifie que chaque preuve existe vraiment dans le corpus.
- **Nouveau package `app/evaluation/`** (écart avec l'arborescence de CLAUDE.md) : l'évaluation est une responsabilité à part (règle 6.7) et ne doit pas se mélanger au retriever. Le jeu de questions est dans `evaluation/` (versionné), et non dans `data/` (ignoré par Git).
- **Réglages par défaut choisis par mesure** (6.3, évaluation du 2026-10-15) :
  - **chunking « sentence » 400/50** (au lieu de 800/150) : meilleur MRR (0,755 contre 0,630) et meilleur Recall@3 (0,844, à égalité avec « fixed » 800/150) ;
  - **Top-K = 5** : Recall@5 = 0,906 contre 0,844 avec K = 3. Pour un petit LLM, rater la preuve coûte plus cher qu'un peu de bruit en plus ; 5 chunks × environ 330 caractères ≈ 420 tokens de contexte ;
  - **pas de seuil de score** (`min_score=0.0`) : sur 3 des 4 réglages, une question **sans réponse** obtient un meilleur score qu'une question avec réponse. Sur le réglage retenu, la séparation n'est que de 0,010 (0,829 contre 0,819), mesurée sur 20 questions : bien trop fragile. L'abstention sera confiée aux **consignes du prompt** (Phase 7).
  - **Limite** : 16 questions avec réponse seulement, et 1 question = 0,0625 de rappel. Les écarts observés sont **indicatifs**, pas statistiquement significatifs.
- **Prompt** (7.2) :
  - un message *system* fixe donne 5 règles : sources uniquement, citer `[n]`, phrase d'abstention imposée, sources = données et non instructions, réponse en français ;
  - un message *user* contient les sources numérotées, puis la question ;
  - chaque chunk est encadré par `<source id="n" document="…" page="…">…</source>`, et toute balise `<source>` présente **dans** un chunk est remplacée par `[balise retirée]` (anti-injection) ;
  - la phrase d'abstention est **fixe** (« Je ne trouve pas la réponse dans les documents fournis. »), donc détectable par le code (`is_no_answer`) et mesurable en Phase 11.
- **Citations vérifiables** : `extract_citations` ne garde que les numéros qui existent (1…n). Un `[7]` avec 5 sources est une citation **inventée**, donc ignorée.
- **Client Ollama** (7.3) : appel direct de `POST /api/chat` (`stream: false`) avec httpx, plutôt que via le paquet `ollama` (décision de 1.4). Les erreurs réseau sont traduites en `LLMUnavailableError` / `LLMError`, avec un message qui dit **quoi faire** (`ollama pull …`). Le pipeline ne dépend que du `Protocol` `LLMClient`, ce qui permet d'injecter un faux LLM en test.
- **Température 0,1** : pour un RAG, on veut des réponses stables et collées au contexte, pas de créativité.
- **Pipeline Q/R** (8.2) : retriever → `build_user_prompt` → `llm.generate` → `extract_citations` + `is_no_answer`.
  - **Index vide ou aucune source** : abstention **sans appeler le LLM**. Un LLM sans contexte répondrait de mémoire, ce qui est exactement ce qu'on veut éviter.
  - Les erreurs LLM (`LLMError`) **remontent** à l'appelant : l'API les traduira en HTTP 503, et la CLI affiche alors les passages.
- **Façade `RAGPipeline`** : un seul objet pour l'API et l'interface. **`build_pipeline`** est le seul endroit qui lit la configuration pour assembler les composants, et il crée **un seul** `EmbeddingModel` partagé par l'ingestion et la recherche (règle d'or vérifiée par un test).
- **API** (Phase 9) :
  - Pydantic **seulement à la frontière** (schémas d'API), et dataclasses à l'intérieur (décision de 2.2) ;
  - les routes ne contiennent aucune logique RAG : validation → `RAGPipeline` → conversion ;
  - codes HTTP : 422 (question invalide, PDF illisible), 415 (pas un PDF : extension **et** signature `%PDF-` vérifiées), 413 (> `max_upload_mb`), 409 (même nom mais autre contenu, pour ne jamais écraser), 404 (document inconnu), 503 (Ollama injoignable), 502 (Ollama répond mais échoue) ;
  - **sécurité des envois** : `Path(filename).name` neutralise la traversée de chemin (`../../evil.pdf` → `data/raw/evil.pdf`) ; lecture limitée à `max_bytes + 1` octets ; un PDF illisible est supprimé après l'échec ;
  - `DELETE` supprime aussi le PDF de `data/raw/`, sinon il serait réindexé au prochain `build_index` ;
  - dépendances FastAPI sous la forme `Annotated[..., Depends(...)]` (forme recommandée ; règle Ruff B008) ; `create_app(settings, pipeline)` permet d'injecter un pipeline de test ;
  - **préchauffage** du modèle d'embeddings au démarrage du serveur, pour que la première question ne paie pas les 15 s de chargement.
- **Interface découplée** (Phase 10) : Streamlit ne parle au RAG **que par l'API HTTP** (`frontend/api_client.py`). Elle n'importe jamais le pipeline, ChromaDB ni le modèle, seulement `app.core.config` pour l'adresse de l'API. On pourrait remplacer l'interface (React…) sans toucher au backend. Lancement : `python -m streamlit run frontend/streamlit_app.py` (`-m` rend `app` et `frontend` importables).
- **Statistiques d'usage de Streamlit désactivées** (`.streamlit/config.toml`) : elles sont activées par défaut, ce qui est contraire au principe « 100 % local ».
- **Style de code** (demande de l'étudiant, 2026-10-11) : « une ligne = un commentaire ». Chaque ligne importante a son `# commentaire` juste au-dessus, en français.
- **Scripts lancés avec `python -m scripts.<nom>`** : comme pour pytest, `-m` rend le package `app` importable depuis la racine.
- **Lancer les tests avec `python -m pytest`** (et non `pytest` seul) : `-m` ajoute le dossier courant à `sys.path`, ce qui rend `app` importable sans configuration supplémentaire.
- **LLM : Ollama uniquement** (décision de l'étudiant, 2026-10-11). C'est une solution 100 % locale et gratuite. Avec 8 Go de RAM et une GTX 1650 (4 Go de VRAM), on vise un modèle d'environ 3B paramètres. Le module `generation/llm.py` restera derrière une interface simple, pour pouvoir changer de fournisseur plus tard si besoin.
- **Uniquement des modèles open source et gratuits, aucune API payante** (confirmé par l'étudiant, 2026-10-15). L'« API » d'Ollama est une API REST **locale** (`http://localhost:11434`), sans clé ni Internet. Modèles envisagés, non encore mesurés :
  - embeddings (Phase 4, `sentence-transformers`, CPU) : un modèle **multilingue**, par exemple `paraphrase-multilingual-MiniLM-L12-v2` ou `multilingual-e5-small` ;
  - LLM (Phase 7, Ollama) : environ 3B paramètres, quantifié. `qwen2.5:3b` est le candidat principal (bon en français), `llama3.2:3b` l'alternative, `gemma2:2b` le secours si la mémoire manque.
  Le choix final se fera par mesure, en Phase 4 et en Phase 7.

## Vérifications effectuées (résultats réels)

Étape 1.1, commandes exécutées le 2026-10-11 :

- `py --list` : 3.13-64, 3.10-64
- `python --version` : Python 3.10.7 (version par défaut du PATH)
- `git --version` : 2.52.0.windows.1 ; `user.name`, `user.email` et `init.defaultBranch=main` sont configurés
- `code --version` : 1.141.0
- `ollama --version` : non installé
- Matériel : environ 8 Go de RAM, GPU NVIDIA GeForce GTX 1650 (4 Go de VRAM) + iGPU AMD Radeon

Étape 1.2, vérifiée le 2026-10-11 :

- `py -3.13 -c "import app, app.core, ..., app.api"` : OK, `app.__file__` = `C:\dev\rag-project\app\__init__.py`
- Les 9 `__init__.py` et les 3 `.gitkeep` sont présents
- Des dossiers `__pycache__/` sont apparus après l'import (normal, à ignorer dans `.gitignore` à l'étape 1.6)

Étape 1.3, vérifiée le 2026-10-11 :

- `py -3.13 -m venv .venv` : OK
- `.venv\Scripts\python.exe --version` : Python 3.13.14
- `sys.prefix` : `C:\dev\rag-project\.venv`
- `pip list` : uniquement `pip 26.2.1` après mise à jour (isolation confirmée)
- Python d'origine : version **Microsoft Store** (`WindowsApps`)
- `LongPathsEnabled` = 0 (chemins longs désactivés)
- Reste à confirmer par l'étudiant : activation dans son terminal et sélection de l'interpréteur dans VS Code

Étape 1.4, vérifiée le 2026-10-11 :

- `python -m pip install -r requirements-dev.txt` : code de sortie 0
- Versions installées : pymupdf 1.28.2, sentence-transformers 6.1.0, chromadb 1.5.9, pydantic-settings 2.15.0, httpx 0.28.1, pytest 9.1.1, ruff 0.17.0
- `torch 2.14.1+cpu` (installé automatiquement), `torch.cuda.is_available()` = False : version CPU, c'est voulu
- `pip check` : « No broken requirements found »
- 106 paquets au total (dépendances transitives comprises) ; le venv pèse environ 1,3 Go
- `pip install -r requirements-dev.txt --dry-run` après figeage : rien à installer, les fichiers correspondent à l'environnement
- Les craintes liées au Python du Microsoft Store et à `LongPathsEnabled=0` ne se sont pas concrétisées

Étape 1.5-A, vérifiée le 2026-10-11 :

- `get_settings().model_dump()` : chemins absolus corrects (`C:/dev/rag-project/...`), `log_level=INFO`
- `python -m pytest tests -v` : **4 passed**
- `ruff check app tests` : All checks passed
- `ruff format --check` : 2 lignes trop longues dans `test_config.py`, corrigées avec `ruff format` ; ensuite 11 fichiers déjà formatés, 4 tests toujours au vert
- Nouveaux dossiers générés : `.pytest_cache/`, `.ruff_cache/` (à ignorer à l'étape 1.6)

Étape 1.5-B, vérifiée le 2026-10-11 :

- Démonstration : au niveau INFO, le message DEBUG est masqué ; INFO, WARNING et ERROR s'affichent au format `date | NIVEAU | logger | message`
- `python -m pytest tests -v` : **8 passed** (4 config + 4 logging)
- `ruff check` : All checks passed ; `ruff format --check` : 13 fichiers déjà formatés

Étape 1.6, vérifiée le 2026-10-11 :

- `git init` : dépôt créé ; `core.autocrlf = true`
- `git status --short --untracked-files=all` : 24 fichiers candidats, sans PDF, `.venv/`, caches ni `__pycache__`
- `git check-ignore -v` : `.venv`, `.env`, `data/raw/*.pdf`, `__pycache__`, `.pytest_cache`, `.ruff_cache`, `storage/chroma/*` sont bien ignorés
- `python -m pytest -q` avant le commit : 8 passed
- Premier commit `b289182` « chore: initialisation du projet (structure, config, logging, tests) » : 24 fichiers, 1577 insertions
- Avertissements `LF will be replaced by CRLF` : normaux avec `autocrlf=true`
- `git push -u origin main` : OK, `main` suit `origin/main` ; `git ls-remote` confirme `b289182` sur GitHub

Étape 2.1, vérifiée le 2026-10-11 (`python -m scripts.inspect_pdfs`) :

- 3 PDF de 2 pages chacun, environ 72 Ko, au format PDF 1.4
- Texte bien extrait : PDF natifs, pas scannés, donc pas besoin d'OCR
- Métadonnées vides (aucun titre ni auteur) : le titre devra venir du nom de fichier ou du contenu
- Défauts repérés, à traiter en 2.4 :
  - en-tête répété sur chaque page : `Corpus pédagogique RAG • Document de démonstration\nPage N\n`
  - sauts de ligne `\n` au milieu des phrases (retours à la ligne de mise en page)
  - apostrophe typographique `’` (U+2019) au lieu de `'`
- `ruff check` et `ruff format --check` sur `scripts/` : OK

Étape 2.2, vérifiée le 2026-10-11 :

- `python -m pytest tests -v` : **14 passed** (8 + 6 nouveaux)
- `ruff check` : OK ; `ruff format --check` : 16 fichiers déjà formatés
- Démonstration : `DocumentPage(..., page_number=0, ...)` lève bien `ValueError: page_number doit être >= 1 (reçu : 0)`

Étape 2.3, vérifiée le 2026-10-11 :

- `ruff format` a reformaté 2 fichiers (lignes trop longues) ; `ruff check` : OK
- `python -m pytest tests -v` : **23 passed** (14 + 9 nouveaux) en 0.59s
- Sur les vrais PDF (`load_pdfs_from_directory`) : 3 documents, 6 pages ; ids `49289fd3ade5e236`, `b2304beac24baf07`, `8a9457a4c9ec61c1`

Étape 2.4, vérifiée le 2026-10-11 :

- 2 erreurs dans mes propres tests repérées à la relecture, avant la première exécution, et corrigées (résultat attendu de doc2 ; signatures « Ligne #. » identiques)
- Ruff `SIM103` (renvoyer directement la condition) : corrigé
- `python -m pytest tests -q` : **37 passed** (23 + 14 nouveaux) en 0.46s ; `ruff check` et `ruff format --check` : OK
- Sur les vrais PDF : en-tête `Corpus pédagogique RAG • Document de démonstration` et `Page #` retirés des 3 documents ; 6 pages en entrée, 6 en sortie ; lignes recollées en paragraphes, titres de section gardés sur leur propre ligne, apostrophes normalisées
- Limite observée : le titre du document est recollé à son sous-titre (`Introduction au Retrieval-Augmented Generation Document 1/3 • ...`). Acceptable pour le MVP.

Étape 2.5, vérifiée le 2026-10-11 :

- 1re exécution : **2 tests d'intégration en échec** (`assert [] == [1, 2]`). Logs capturés : « page 1 vide après nettoyage ». Cause : mon PDF de test avait 2 pages identiques aux chiffres près, et des pages de 5 lignes, entièrement couvertes par les zones haut/bas de 3 lignes. Toutes les lignes ont donc été prises pour des en-têtes. Correction : un contenu différent par page (réaliste).
- Après correction : `python -m pytest tests -q` → **39 passed** (37 unitaires + 2 d'intégration) en 0.49s ; `ruff check` : OK
- `python -m scripts.ingest_preview` sur les vrais PDF : 3 JSON écrits dans `data/processed/` (2 pages chacun), accents lisibles ; `git check-ignore` confirme qu'ils sont ignorés

Étape 3.1, vérifiée le 2026-10-11 :

- Mesures sur les pages nettoyées : pages de 536 à 2 454 caractères ; paragraphes de 357 caractères au maximum ; environ 9 000 caractères au total
- `python -m pytest tests -q` : **43 passed** (39 + 4 nouveaux) ; `ruff check` : OK
- `get_settings()` → `800 150 sentence`

Étape 3.2, vérifiée le 2026-10-12 :

- `python -m pytest tests/unit/test_models.py -v` : 12 passed (les 6 anciens tests de `DocumentPage` passent toujours après la factorisation)
- `python -m pytest tests -q` : **49 passed** ; `ruff check` : OK
- Démonstration : `Chunk('49289fd3ade5e236', '01_introduction_rag.pdf', 1, 0, ...).chunk_id` → `49289fd3ade5e236-p1-c0`
- Commit `cd6289b` (pas encore poussé sur GitHub)

Étape 3.3, vérifiée le 2026-10-15 :

- `ruff check` : 1 remarque `RUF007` (`zip(pieces, pieces[1:])` → `itertools.pairwise`), corrigée ; ensuite All checks passed ; `ruff format --check` : 24 fichiers déjà formatés
- `python -m pytest tests/unit/test_chunker.py -v` : 13 passed ; `python -m pytest tests -q` : **62 passed**
- Sur les vrais PDF (800 / 150) : **15 chunks** au total. Les pages de 2 386, 2 315 et 2 454 caractères donnent 4 chunks chacune (derniers : 436, 365, 504 caractères), et chaque page 2 donne 1 chunk. C'est conforme à la formule $\lceil (L-o)/(s-o) \rceil$.
- Limite observée : la fin du chunk `49289fd3ade5e236-p1-c0` est `"...Il charge les fic"`, coupé au milieu d'un mot. C'est attendu avec « fixed », et c'est justement ce que la stratégie « sentence » (3.4) doit corriger.
- Commit `f5cae44`

Étape 3.4, vérifiée le 2026-10-15 :

- `ruff check` : All checks passed (après `ruff format`)
- `python -m pytest tests/unit/test_chunker.py -v` : 25 passed ; `python -m pytest tests -q` : **74 passed**
- Sur les vrais PDF (800 / 150, « sentence ») : **15 chunks**, comme avec « fixed ». Tailles : 382 à 794 caractères ; les grandes pages font 24 à 27 phrases. La phrase la plus longue fait 221 caractères, donc le repli sur « fixed » n'est jamais utilisé sur ce corpus.
- Toutes les frontières tombent en fin de phrase : c0 finit par `"...prépare les documents."` et c1 commence par `"2. Les deux pipelines fondamentaux Le pipeline d'ingestion..."` (chevauchement = titre + 1 phrase).
- Commit `9af6bde`

Étape 3.5, vérifiée le 2026-10-15 :

- `ruff check` : All checks passed ; `python -m pytest tests/integration -v` : 6 passed (4 nouveaux) ; `python -m pytest tests -q` : **78 passed**
- `python -m scripts.compare_chunking` (mesures réelles, 6 pages) :

  | Mesure | fixed 800/150 | sentence 800/150 | fixed 400/50 | sentence 400/50 |
  |---|---|---|---|---|
  | Nombre de chunks | 15 | 15 | 28 | 28 |
  | Taille min / moy. / max | 365 / 692 / 800 | 382 / 663 / 794 | 94 / 362 / 400 | 93 / 327 / 399 |
  | Redondance (stocké/texte) | 1.15 | 1.10 | 1.12 | 1.01 |
  | Débuts propres | 40 % | 100 % | 21 % | 100 % |
  | Fins propres | 40 % | 93 % | 21 % | 86 % |

- Fins non propres de « sentence » : **toutes** sont des **titres orphelins**. Un titre numéroté termine le chunk et son contenu part dans le chunk suivant (ex. `8a9457a4c9ec61c1-p1-c2` finit par `"...reconnaître cette limite. 5. Protocole de comparaison"`). Il y en a 1 sur 15 à 800/150 et 4 sur 28 à 400/50.
- Avec 400/50, le chevauchement de « sentence » est presque nul (redondance 1.01) : la plupart des phrases font plus de 50 caractères, donc aucune phrase entière ne tient dans le chevauchement.
- Ces mesures portent sur la **forme** des chunks. L'effet sur la **qualité de la recherche** n'est pas encore mesuré ; il le sera en Phase 6 et en Phase 11.
- **Correction des titres orphelins (option A, choisie le 2026-10-15)** : la nouvelle fonction `attach_headings()` colle chaque titre numéroté à la phrase qui le suit. `_is_heading` de `text_cleaner` devient publique (`is_heading`), pour que la règle soit la même partout. 4 tests unitaires ont été ajoutés.
- Mesures **après** correction (`python -m scripts.compare_chunking`) :

  | Mesure | sentence 800/150 avant → après | sentence 400/50 avant → après |
  |---|---|---|
  | Nombre de chunks | 15 → **14** | 28 → 28 |
  | Redondance | 1.10 → **1.05** | 1.01 → 1.00 |
  | Débuts propres | 100 % → 100 % | 100 % → 100 % |
  | Fins propres | 93 % → **100 %** | 86 % → **100 %** |

- `python -m pytest tests -q` : **82 passed** ; `ruff check` : OK
- Commit `798dac1`

Phase 4, vérifiée le 2026-10-15 :

- Environnement : `ollama` **absent**, `docker` **absent**, Hugging Face accessible (HTTP 200). Premier téléchargement du modèle : 43,6 s ; chargements suivants depuis le cache : 15,6 s. Avertissement Windows sans conséquence : « symlinks not supported » (le cache Hugging Face copie les fichiers au lieu de créer des liens).
- Inspection du modèle : `max_seq_length = 512`, `similarity_fn_name = cosine`, `prompts = {'query': '', 'document': ''}`. Le modèle ne déclare **pas** ses préfixes, d'où leur ajout manuel.
- `ruff check` : OK ; `python -m pytest -q` : **94 passed, 2 deselected** ; `python -m pytest -m slow -q` : **2 passed** en 17,3 s
- `python -m scripts.inspect_embeddings` (14 chunks, « sentence » 800/150) :
  - dimension 384 ; tokens par chunk : min 95, **moyenne 170, max 209** ; **0 chunk tronqué** (limite 512) ;
  - **3,98 caractères par token** : l'estimation de 3.1 (800 car. ≈ 200 tokens) est confirmée ;
  - vectorisation : 0,60 s pour 14 chunks (**43 ms/chunk** sur CPU) ;
  - question « Pourquoi faut-il normaliser les vecteurs ? » : les 3 meilleurs chunks viennent tous du document 2 (embeddings), avec des scores de 0,833, 0,830 et 0,826 ; le moins proche obtient 0,784.
- Constat : les scores cosinus de E5 sont **compressés** (environ 0,78 à 0,84) : même un chunk hors sujet obtient plus de 0,78. Un seuil absolu de « pertinence » devra donc être **calibré** sur nos données (Phase 8), et non fixé à 0,5 par intuition.
- Commit `2ee3559`

Phase 5, vérifiée le 2026-10-15 :

- Exploration de l'API ChromaDB 1.5.9 : un nom de collection de moins de 3 caractères est refusé (`InvalidArgumentError`) ; `query` renvoie des listes de listes (une par question) ; la distance cosinus entre (1, 0) et (1, 0.1) vaut 0.005.
- **Incident** : en ajoutant 2 tests à `test_models.py` avec PowerShell 5.1 (`Get-Content`/`Set-Content`), le fichier a été relu en ANSI et tous les accents ont été abîmés (`Ã©`). Détecté avec `git diff`, fichier restauré (`git checkout`), puis modification refaite avec l'outil d'édition. Leçon : ne pas modifier de fichiers UTF-8 avec les cmdlets de PowerShell 5.1.
- `ruff check` : OK ; `python -m pytest -q` : **110 passed, 2 deselected** (2,58 s)
- `python -m scripts.build_index` (vrais PDF) : 3 documents indexés (5 + 4 + 5 = **14 chunks**) en **17,5 s**, chargement du modèle compris.
- 2e exécution : 3 × `skipped` (« déjà indexé ») en **0,0 s**. Le modèle n'est même pas chargé (chargement paresseux), et l'index contient toujours 14 chunks.
- `storage/chroma/` contient `chroma.sqlite3` et un dossier d'index HNSW ; il est ignoré par Git.
- Commit `cddc139`

Phase 6, vérifiée le 2026-10-15 :

- Jeu de questions : `find_missing_evidence` sur le corpus nettoyé → **0 preuve manquante** (22 preuves pour 16 questions avec réponse)
- `python -m scripts.evaluate_retrieval` (modèle E5 réel, 20 questions, une base temporaire par réglage) :

  | Mesure | sentence 800/150 | fixed 800/150 | **sentence 400/50** | fixed 400/50 |
  |---|---|---|---|---|
  | Chunks | 14 | 15 | 28 | 28 |
  | Precision@3 | 0,271 | 0,312 | **0,312** | 0,229 |
  | Recall@3 | 0,719 | 0,844 | **0,844** | 0,656 |
  | Precision@5 | 0,188 | 0,213 | 0,200 | 0,175 |
  | Recall@5 | 0,812 | **0,938** | 0,906 | 0,781 |
  | **MRR** | 0,630 | 0,693 | **0,755** | 0,533 |
  | Recall@5 paraphrases | 0,667 | 1,000 | 1,000 | 0,667 |
  | Recall@5 multi-documents | 0,667 | 0,667 | 0,500 | 0,500 |
  | Plus petit top-score (avec réponse) | 0,822 | 0,833 | 0,829 | 0,832 |
  | Plus grand top-score (sans réponse) | 0,827 | 0,817 | 0,819 | 0,827 |
  | Latence de recherche / question | 18,9 ms | 19,3 ms | 19,1 ms | 18,7 ms |

- Analyse question par question (sentence 800 contre les autres) : « sentence » 800/150 rate **q03** et **q08**, deux paraphrases, que les autres réglages retrouvent. Ses chunks plus longs (4 à 5 sujets chacun) ont un vecteur plus « dilué ».
- Constat surprenant, gardé tel quel : à 800/150, « fixed » fait **mieux** que « sentence » en rappel. Avoir des bords propres ne garantit donc pas une meilleure recherche. **C'est la mesure qui tranche**, pas l'intuition de la Phase 3.
- Après le changement de configuration : `python -m scripts.build_index --replace` → 9 + 9 + 10 = **28 chunks** (l'ancien index de 14 chunks a été entièrement remplacé, sans orphelin) ; `compare_chunking` en 400/50 donne 100 % de bords propres pour « sentence ».
- `ruff check` : OK (1 tri d'imports `I001` corrigé à la main pour garder les commentaires) ; `python -m pytest -q` : **127 passed, 2 deselected**
- Commit `e5f51c4`

Phase 7, vérifiée le 2026-10-15 :

- `ruff check` : OK ; `python -m pytest -q` : **140 passed, 2 deselected** (3,07 s)
- `python -m scripts.check_ollama` → `❌ Ollama injoignable à http://localhost:11434 ou modèle 'qwen2.5:3b' absent.`, code de sortie 1. C'est le comportement **attendu** sur cette machine (Ollama non installé). Le message donne les 3 commandes à lancer.
- Commit `6575be9`
- **Non vérifié** : aucune génération réelle n'a pu être faite. Le format de l'API (`/api/chat`, `message.content`, `/api/tags`) est reproduit dans les faux serveurs des tests à partir de la documentation d'Ollama, mais il n'a pas été confronté à un vrai serveur.

Phase 8, vérifiée le 2026-10-15 :

- `ruff check` : OK ; `python -m pytest -q` : **147 passed, 2 deselected** (3,39 s)
- `python -m scripts.ask "Que risque-t-on si l'on récupère trop de passages ?"` sur le vrai index (28 chunks) : la recherche fonctionne et Ollama est absent. On obtient le message `⚠️ Ollama est injoignable…`, suivi des 5 passages retrouvés (scores 0,842 à 0,829). Le passage [2] (`02_embeddings_recherche_vectorielle.pdf, p. 1`) contient la preuve attendue (« un nombre K trop élevé peut ajouter du bruit »).
- `python -m scripts.build_index` (après le passage à `build_pipeline`) : 3 × `skipped`, 28 chunks, 0,0 s.
- **Non vérifié** : la qualité des réponses générées (Ollama absent). Elle sera mesurable avec `scripts/evaluate_rag.py` (Phase 11) dès qu'Ollama sera installé.
- Commit `37f488f`

Phase 9, vérifiée le 2026-10-15 :

- `pip install fastapi python-multipart` : fastapi 0.143.1, starlette 1.8.0, python-multipart 0.0.32 ; uvicorn 0.54.0 était déjà installé (dépendance de chromadb) ; `pip check` : OK
- Constantes HTTP dépréciées dans Starlette 1.8 (vérifié avec `-W error`) : `HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT`, `HTTP_413_REQUEST_ENTITY_TOO_LARGE` → `HTTP_413_CONTENT_TOO_LARGE`
- 1re exécution des tests de l'API : **1 échec** (`casse.pdf` → `PermissionError: [WinError 32]`). **Vrai bug** : sous Windows, quand `pymupdf.open(chemin)` échoue sur un PDF corrompu, le fichier reste verrouillé et l'API ne peut plus le supprimer. Correction dans `load_pdf` : lecture des octets, puis `pymupdf.open(stream=…, filetype="pdf")`.
- Autre incident : la sortie de pytest faisait 2 Mo, parce que l'identifiant automatique du cas « fichier trop gros » contenait 1 Mo de zéros. Corrigé avec `ids=[...]`.
- `ruff check` : 5 × B008 (`Depends` en valeur par défaut) → passage à `Annotated` ; `python -m pytest -q` : **164 passed, 2 deselected**, 1 avertissement de bibliothèque (`StarletteDeprecationWarning` : TestClient recommande `httpx2`, sans effet ; non traité pour ne pas ajouter de dépendance).
- **Vrai serveur** (`uvicorn app.main:app --port 8765`, vrai index de 28 chunks) :
  - `GET /health` → `{"status":"ok","documents":3,"chunks":28,"llm_available":false,"llm_model":"qwen2.5:3b"}`
  - `GET /documents` → les 3 PDF (9, 9 et 10 chunks) ; `GET /docs` → 200
  - `POST /ask` → **503** avec le message « Ollama est injoignable… » (attendu) ; question vide → 422 ; envoi d'un `.txt` → 415
  - `POST /documents` avec un PDF généré → `indexed`, 1 chunk ; `DELETE` → `deleted_chunks: 1` ; ensuite `/health` = 28 chunks et `data/raw/` contient les 3 PDF d'origine (état restauré)
- **Mesures de latence → 2 corrections** :

  | Situation | Avant | Après |
  |---|---|---|
  | `/ask` avec Ollama absent | 4,1 s | **1,0 s** |
  | 1er `/ask` après le démarrage | 20,2 s | **1,4 s** (démarrage du serveur : ~13 s) |

  - Cause 1 : sous Windows, une connexion refusée coûte environ 2 s par adresse (mesuré : `localhost` 4,42 s, contre 2,26 s pour `127.0.0.1`, car `localhost` essaie IPv6 puis IPv4). Corrections : URL par défaut `127.0.0.1` + délai de **connexion** de 1 s (le délai de génération reste de 120 s).
  - Cause 2 : chargement paresseux du modèle à la 1re question. Correction : préchauffage au démarrage de l'API.
- Commit `20328d8`

Phase 10, vérifiée le 2026-10-15 :

- `pip install streamlit` → 1.66.0 (+ pandas, pyarrow, altair… ; 118 paquets au total dans le venv) ; `pip check` : OK
- 1re exécution : 1 échec. `AppTest.from_file("frontend/...")` résout un chemin relatif **depuis le fichier de test**. Corrigé avec un chemin absolu depuis `PROJECT_ROOT`.
- `ruff check` : OK ; `python -m pytest -q` : **170 passed, 2 deselected** (7,9 s)
- **Essai réel** (API uvicorn sur :8000 + Streamlit sur :8501, vrai index) :
  - `GET :8501/_stcore/health` → `ok`
  - Interface pilotée par `AppTest` contre la vraie API : aucune exception ; légende « 3 document(s), 28 chunk(s) indexé(s) » ; avertissement « LLM « qwen2.5:3b » indisponible… » ; liste des 3 PDF (9, 9 et 10 chunks)
  - Question saisie dans `chat_input` → message « Erreur 503 : Ollama est injoignable à http://127.0.0.1:11434… » (attendu, Ollama absent)
- Le 1er journal de Streamlit affichait « Collecting usage statistics » → `.streamlit/config.toml` ajouté ; au relancement, ce message n'apparaît plus (0 occurrence), et `/_stcore/health` répond `ok`.
- **Non vérifié** : l'affichage d'une vraie réponse générée (Ollama absent). La mise en forme des réponses (`render_answer`) n'est exercée qu'à travers le code, sans rendu réel.

## Données de travail

- `data/raw/` contient 3 PDF en **français** : `01_introduction_rag.pdf`, `02_embeddings_recherche_vectorielle.pdf`, `03_evaluation_rag.pdf`. Il faudra donc un modèle d'embeddings multilingue en Phase 4.
- Ces PDF sont **exclus de Git** par défaut (règle CLAUDE.md : pas de documents privés dans le dépôt). Si leur licence le permet, on pourra plus tard versionner un petit jeu de démonstration.

## Problèmes connus / décisions en attente

- ~~**Titres orphelins**~~ (mesuré en 3.5) : **corrigé** par `attach_headings()`. Il y a maintenant 100 % de fins propres.
- **Limite de `remove_repeated_lines`** : une ligne identique (chiffres masqués) dans les 3 premières ou 3 dernières lignes de **toutes** les pages est retirée, même si c'est du contenu. Risque surtout pour les documents aux pages très courtes et très similaires. Pas de souci sur le corpus actuel.
- Avec PyMuPDF, utiliser `import pymupdf` : l'ancien nom `import fitz` affiche un avertissement de dépréciation.
- Seules les dépendances directes sont figées ; les dépendances transitives ne le sont pas. Un fichier de verrouillage complet (`pip freeze`) pourra être ajouté en Phase 12 (Docker).
- **BLOCAGE — Ollama n'est pas installé** (vérifié le 2026-10-15). Tout le code LLM est écrit et testé avec un faux serveur, mais **aucune réponse réelle n'a été générée**. Je n'ai pas installé de logiciel système sans l'accord de l'étudiant. Pour lever le blocage :
  ```powershell
  winget install Ollama.Ollama      # ou l'installeur de https://ollama.com/download
  ollama pull qwen2.5:3b            # environ 1,9 Go
  python -m scripts.check_ollama    # doit afficher ✅
  ```

## Prochaine sous-étape

Phase 11 — Tests et évaluation du RAG (réponses).
