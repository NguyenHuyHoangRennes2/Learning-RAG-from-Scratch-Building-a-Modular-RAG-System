# PROJECT_PROGRESS.md — Suivi du projet RAG

Dépôt GitHub : https://github.com/NguyenHuyHoangRennes2/Learning-RAG-from-Scratch-Building-a-Modular-RAG-System

## Phase en cours

**Phase 3 — Chunking**

| Étape | Titre | Statut |
|---|---|---|
| 3.1 | Principes du chunking + paramètres dans la configuration | ✅ Validée (2026-10-12) |
| 3.2 | Structure de données `Chunk` (`app/models.py`) | ✅ Validée (2026-10-15) |
| 3.3 | Chunker, stratégie « fixed » (`app/ingestion/chunker.py`) | ✅ Validée (2026-10-15) |
| 3.4 | Chunker, stratégie « sentence » (`app/ingestion/chunker.py`) | ✅ Validée (2026-10-15) |
| 3.5 | Comparaison des stratégies sur les vrais PDF (script + test d'intégration) + correction des titres orphelins | ✅ Terminée (2026-10-15, mode autonome) |

**Phase 3 terminée le 2026-10-15.**

> **Mode autonome (2026-10-15)** : l'étudiant a demandé de terminer le projet jusqu'à la Phase 12 **sans validation intermédiaire**. Il évaluera l'ensemble à la fin. Les étapes suivantes sont donc marquées « Terminée (mode autonome) » et non « Validée ». Chaque étape reste documentée ici (résultats réels) et dans `NOTES_APPRENTISSAGE.md`.

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
- **Chunking — valeurs par défaut** : `chunk_size=800`, `chunk_overlap=150` (environ 19 %), `chunk_strategy="sentence"`. Un chunk ne traverse jamais deux pages, pour que la citation de page reste exacte.
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

## Données de travail

- `data/raw/` contient 3 PDF en **français** : `01_introduction_rag.pdf`, `02_embeddings_recherche_vectorielle.pdf`, `03_evaluation_rag.pdf`. Il faudra donc un modèle d'embeddings multilingue en Phase 4.
- Ces PDF sont **exclus de Git** par défaut (règle CLAUDE.md : pas de documents privés dans le dépôt). Si leur licence le permet, on pourra plus tard versionner un petit jeu de démonstration.

## Problèmes connus / décisions en attente

- ~~**Titres orphelins**~~ (mesuré en 3.5) : **corrigé** par `attach_headings()`. Il y a maintenant 100 % de fins propres.
- **Limite de `remove_repeated_lines`** : une ligne identique (chiffres masqués) dans les 3 premières ou 3 dernières lignes de **toutes** les pages est retirée, même si c'est du contenu. Risque surtout pour les documents aux pages très courtes et très similaires. Pas de souci sur le corpus actuel.
- Avec PyMuPDF, utiliser `import pymupdf` : l'ancien nom `import fitz` affiche un avertissement de dépréciation.
- Seules les dépendances directes sont figées ; les dépendances transitives ne le sont pas. Un fichier de verrouillage complet (`pip freeze`) pourra être ajouté en Phase 12 (Docker).
- Ollama n'est pas encore installé. Ce sera nécessaire au plus tard en Phase 7.

## Prochaine sous-étape

Décision sur les titres orphelins (corriger maintenant ou plus tard), puis validation de 3.5 → fin de la Phase 3 → Phase 4 (embeddings).
