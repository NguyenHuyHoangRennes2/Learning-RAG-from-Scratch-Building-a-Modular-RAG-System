# RAG Student Project — questions-réponses sur vos PDF, 100 % local

Assistant qui répond à des questions **à partir de vos documents PDF**, en citant ses sources
(fichier et page). Il repose sur le **Retrieval-Augmented Generation (RAG)** et tourne
**entièrement en local**, avec des modèles open source et gratuits, sans clé ni API payante :

| Brique | Outil |
|---|---|
| Extraction PDF | PyMuPDF |
| Embeddings | Sentence Transformers — `intfloat/multilingual-e5-small` (384 dim., multilingue) |
| Base vectorielle | ChromaDB (persistante, espace cosinus) |
| LLM | Ollama — `qwen2.5:3b` |
| API | FastAPI + Uvicorn |
| Interface | Streamlit |
| Tests | Pytest (178 tests, couverture 95 %) |

> Projet pédagogique construit étape par étape : le journal complet des décisions et des
> mesures est dans [`PROJECT_PROGRESS.md`](PROJECT_PROGRESS.md), et les notions expliquées
> dans [`NOTES_APPRENTISSAGE.md`](NOTES_APPRENTISSAGE.md).

## Fonctionnement

```
INDEXATION   PDF ─► extraction ─► nettoyage ─► découpage (chunks) ─► embeddings ─► ChromaDB
                                                                                    │
QUESTION     question ─► embedding ─► recherche des 5 chunks les plus proches ◄─────┘
                                         │ sources numérotées [1]..[5]
                                         ▼
                              prompt (règles + sources + question) ─► LLM ─► réponse citée
```

- Le LLM n'a le droit de répondre **qu'à partir des sources**, et il les cite (`[1]`, `[2]`…).
- Si les sources ne suffisent pas, il doit répondre : « Je ne trouve pas la réponse dans les documents fournis. »
- Le texte des documents est traité comme une **donnée**, jamais comme une instruction (protection contre l'injection de prompt).

## Installation (Windows / PowerShell)

Prérequis : Python 3.11 ou plus récent (testé avec 3.13), Git, et environ 3 Go d'espace disque.

```powershell
git clone https://github.com/NguyenHuyHoangRennes2/Learning-RAG-from-Scratch-Building-a-Modular-RAG-System.git
cd Learning-RAG-from-Scratch-Building-a-Modular-RAG-System
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt     # ou requirements-lock.txt pour l'environnement exact testé
Copy-Item .env.example .env                       # facultatif : toutes les valeurs ont un défaut
```

**LLM local** (indispensable pour générer des réponses ; la recherche fonctionne sans) :

```powershell
winget install Ollama.Ollama          # ou https://ollama.com/download
ollama pull qwen2.5:3b                # ~1,9 Go
python -m scripts.check_ollama        # doit afficher ✅
```

## Utilisation

Placez vos PDF dans `data/raw/`, puis :

```powershell
python -m scripts.build_index                    # indexe les nouveaux PDF (--replace pour tout réindexer)
python -m scripts.ask "Qu'est-ce que le RAG ?"   # question en ligne de commande
```

**Application web** (deux terminaux) :

```powershell
uvicorn app.main:app                                # API → http://127.0.0.1:8000/docs
python -m streamlit run frontend/streamlit_app.py   # interface → http://localhost:8501
```

### API REST

| Méthode | Route | Rôle |
|---|---|---|
| GET | `/health` | État : documents, chunks, LLM disponible |
| POST | `/ask` | `{"question": "..."}` → réponse, sources numérotées, citations, latences |
| GET | `/documents` | Documents indexés |
| POST | `/documents` | Envoi d'un PDF (multipart, champ `file`) → indexation |
| DELETE | `/documents/{document_id}` | Retire un document (index + fichier) |

Codes d'erreur : 422 (entrée invalide), 415 (pas un PDF), 413 (trop gros), 409 (nom déjà pris),
404 (inconnu), 503 (Ollama injoignable), 502 (Ollama a échoué).

## Configuration

Toutes les valeurs sont dans [`app/core/config.py`](app/core/config.py) et se surchargent par
variable d'environnement (préfixe `RAG_`) ou dans `.env` (voir [`.env.example`](.env.example)).

| Variable | Défaut | Rôle |
|---|---|---|
| `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` | 400 / 50 | Taille et chevauchement des chunks (caractères) |
| `RAG_CHUNK_STRATEGY` | `sentence` | `sentence` (phrases entières) ou `fixed` |
| `RAG_EMBEDDING_MODEL_NAME` | `intfloat/multilingual-e5-small` | Changer de modèle impose `build_index --replace` |
| `RAG_RETRIEVAL_TOP_K` | 5 | Nombre de chunks transmis au LLM |
| `RAG_OLLAMA_MODEL` | `qwen2.5:3b` | Modèle Ollama |
| `RAG_LLM_TEMPERATURE` | 0.1 | Réponses stables, collées aux sources |
| `RAG_MAX_UPLOAD_MB` | 20 | Taille maximale d'un PDF envoyé à l'API |

Les réglages de chunking et de Top-K ont été **choisis par mesure** (voir ci-dessous).

## Évaluation (résultats mesurés)

Jeu de 20 questions de référence ([`evaluation/questions.json`](evaluation/questions.json)) :
7 faciles, 6 paraphrases, 3 multi-documents, 4 sans réponse dans le corpus.

**Recherche** (`python -m scripts.evaluate_retrieval`, corpus de démonstration de 3 PDF) :

| Réglage | Recall@3 | Recall@5 | MRR |
|---|---|---|---|
| sentence 800/150 | 0,719 | 0,812 | 0,630 |
| fixed 800/150 | 0,844 | 0,938 | 0,693 |
| **sentence 400/50 (retenu)** | **0,844** | 0,906 | **0,755** |
| fixed 400/50 | 0,656 | 0,781 | 0,533 |

**Réponses** (`python -m scripts.evaluate_rag`) : seule la **référence extractive sans LLM**
a été mesurée (précision des citations 0,562 ; abstention sur les questions hors corpus 0 %),
car Ollama n'était pas installé sur la machine de développement. Avec Ollama :
`python -m scripts.evaluate_rag --llm ollama`.

> Avec 16 questions avec réponse, une question vaut 0,0625 de rappel : ces écarts sont des
> observations sur ce corpus, pas des garanties générales.

**Performance mesurée** (CPU, 8 Go de RAM) : chargement du modèle d'embeddings ~15 s (une
seule fois, au démarrage de l'API) ; indexation de 3 PDF (28 chunks) ~17 s, modèle compris ;
recherche ~20 ms par question.

## Tests

```powershell
python -m pytest                                    # 176 tests rapides (~8 s)
python -m pytest -m slow                            # 2 tests avec le vrai modèle d'embeddings
python -m pytest -m "" --cov=app --cov=frontend     # tout + couverture
ruff check app tests scripts frontend               # qualité du code
```

## Déploiement avec Docker

```powershell
docker compose up -d --build
docker compose exec ollama ollama pull qwen2.5:3b
docker compose exec api python -m scripts.build_index
```

Trois services : `ollama` (LLM), `api` (FastAPI, port 8000) et `ui` (Streamlit, port 8501).
Les PDF (`./data`), l'index (`./storage`) et les modèles sont conservés dans des volumes.

> ⚠️ Les fichiers Docker ont été écrits et vérifiés syntaxiquement, mais **l'image n'a pas
> été construite** : Docker n'était pas installé sur la machine de développement.

## Structure du projet

```
app/
  core/          configuration (config.py) et logging
  ingestion/     pdf_loader, text_cleaner, chunker
  embeddings/    embedding_model (E5, préfixes, normalisation)
  vectorstore/   chroma_store
  retrieval/     retriever (Top-K)
  generation/    prompts, llm (client Ollama)
  rag/           pipeline (ingestion + questions-réponses)
  evaluation/    métriques de recherche et de réponse, jeu de questions
  api/           routes et schémas FastAPI
  models.py      structures de données partagées (DocumentPage, Chunk, SearchResult, RAGAnswer)
  main.py        application FastAPI
frontend/        interface Streamlit + client HTTP de l'API
scripts/         build_index, ask, check_ollama, evaluate_retrieval, evaluate_rag, inspections
evaluation/      questions de référence et résultats mesurés
tests/           unit/ et integration/ (+ faux composants dans fakes.py)
```

## Limites connues

- **Génération non mesurée** : Ollama absent pendant le développement (voir `PROJECT_PROGRESS.md`).
- **PDF scannés** : pas d'OCR, les pages sans texte sont ignorées.
- **Découpage en phrases par règles** : « M. Dupont » serait coupé à tort.
- **Pas de détection d'absence de réponse par score** : sur ce corpus, les scores cosinus des
  questions avec et sans réponse se chevauchent ; c'est le prompt qui gère l'abstention.
- **Petit jeu d'évaluation** (20 questions, 3 PDF) : résultats indicatifs.

## Pistes d'amélioration

Recherche hybride (BM25 + embeddings), reranking, OCR des PDF scannés, évaluation des
réponses par un juge humain ou un modèle plus grand, jeu de questions plus large.
