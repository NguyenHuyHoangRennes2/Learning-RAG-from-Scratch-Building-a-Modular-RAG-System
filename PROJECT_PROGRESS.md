# PROJECT_PROGRESS.md — Suivi du projet RAG

## Phase en cours

**Phase 2 — Ingestion**

| Étape | Titre | Statut |
|---|---|---|
| 2.1 | Le format PDF et exploration de nos documents | ✅ Validée (2026-10-11) |
| 2.2 | Structure de données d'une page (`app/models.py`) | 🔎 Implémentée, en attente de validation |
| 2.3 | Chargeur PDF (`app/ingestion/pdf_loader.py`) | ⬜ À faire |
| 2.4 | Nettoyage du texte (`app/ingestion/text_cleaner.py`) | ⬜ À faire |
| 2.5 | Validation sur les vrais PDF (test d'intégration + export `data/processed/`) | ⬜ À faire |

Dépôt GitHub : https://github.com/NguyenHuyHoangRennes2/Learning-RAG-from-Scratch-Building-a-Modular-RAG-System

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
- **Style de code** (demande de l'étudiant, 2026-10-11) : « une ligne = un commentaire ». Chaque ligne importante a son `# commentaire` juste au-dessus, en français.
- **Scripts lancés avec `python -m scripts.<nom>`** : comme pour pytest, `-m` rend le package `app` importable depuis la racine.
- **Lancer les tests avec `python -m pytest`** (et non `pytest` seul) : `-m` ajoute le dossier courant à `sys.path`, ce qui rend `app` importable sans configuration supplémentaire.
- **LLM : Ollama uniquement** (décision de l'étudiant, 2026-10-11). C'est une solution 100 % locale et gratuite. Avec 8 Go de RAM et une GTX 1650 (4 Go de VRAM), on vise un modèle d'environ 3B paramètres. Le module `generation/llm.py` restera derrière une interface simple, pour pouvoir changer de fournisseur plus tard si besoin.

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

## Données de travail

- `data/raw/` contient 3 PDF en **français** : `01_introduction_rag.pdf`, `02_embeddings_recherche_vectorielle.pdf`, `03_evaluation_rag.pdf`. Il faudra donc un modèle d'embeddings multilingue en Phase 4.
- Ces PDF sont **exclus de Git** par défaut (règle CLAUDE.md : pas de documents privés dans le dépôt). Si leur licence le permet, on pourra plus tard versionner un petit jeu de démonstration.

## Problèmes connus / décisions en attente

- Avec PyMuPDF, utiliser `import pymupdf` : l'ancien nom `import fitz` affiche un avertissement de dépréciation.
- Seules les dépendances directes sont figées ; les dépendances transitives ne le sont pas. Un fichier de verrouillage complet (`pip freeze`) pourra être ajouté en Phase 12 (Docker).
- Ollama n'est pas encore installé. Ce sera nécessaire au plus tard en Phase 7.

## Prochaine sous-étape

2.3 — Chargeur PDF (après validation de 2.2).
