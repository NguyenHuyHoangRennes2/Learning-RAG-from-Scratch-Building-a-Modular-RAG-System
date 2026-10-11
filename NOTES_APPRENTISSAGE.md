# Notes d'apprentissage — Projet RAG

> Carnet de révision : pour chaque étape, **ce que j'ai fait** (actions et commandes) et **ce que j'ai appris** (définitions et notions).
> L'état d'avancement du projet est suivi à part, dans `PROJECT_PROGRESS.md`.

## Sommaire

- [Phase 1 — Initialisation](#phase-1--initialisation)
  - [1.1 — Préparation de l'environnement](#étape-11--préparation-de-lenvironnement-de-développement)
  - [1.2 — Arborescence et packages](#étape-12--arborescence-du-projet-et-packages-python)
  - [1.3 — Environnement virtuel](#étape-13--environnement-virtuel-python)
  - [1.4 — Gestion des dépendances](#étape-14--gestion-des-dépendances)
  - [1.5-A — Configuration centralisée](#étape-15-a--configuration-centralisée)
  - [1.5-B — Logging](#étape-15-b--logging)
  - [1.6 — Git et GitHub](#étape-16--git-et-github)
- [Registre des tests (pytest)](#registre-des-tests-pytest)
- [Glossaire](#glossaire)

---

# Phase 1 — Initialisation

## Étape 1.1 — Préparation de l'environnement de développement

### Ce que j'ai fait

- Vérifié les outils installés : Python 3.13 et 3.10, Git 2.52, VS Code 1.141.
- Configuré Git (une fois par machine) :
  ```powershell
  git config --global user.name "Hoang"
  git config --global user.email "..."
  git config --global init.defaultBranch main
  ```
- Décidé d'utiliser **Python 3.13** pour le projet (3.10 est trop ancien, le projet exige 3.11+).

### Notions apprises

**Interpréteur Python**
- **Définition** : le programme (`python.exe`) qui lit et exécute le code Python.
- **Pourquoi c'est important** : les bibliothèques de ML (PyTorch…) ne publient des paquets précompilés (*wheels*) que pour certaines versions de Python.
- **À retenir** : la version de Python est un choix technique, pas un détail.

**Py launcher (`py.exe`)**
- **Définition** : outil Windows qui permet de choisir une version précise de Python quand plusieurs sont installées.
- **Exemple** : `py --list` liste les versions ; `py -3.13 script.py` force Python 3.13.
- **Pourquoi** : sur ma machine, `python` lance 3.10 (le premier trouvé dans le `PATH`). `py -3.13` contourne ce problème.

**Variable `PATH`**
- **Définition** : liste de dossiers où Windows cherche un programme quand on tape son nom.
- **Fonctionnement** : le **premier** `python.exe` trouvé dans l'ordre du `PATH` est celui qui est lancé.

**Git**
- **Définition** : système de contrôle de version qui enregistre l'historique du code sous forme de *commits* (des instantanés du projet).
- **Pourquoi** : revenir en arrière, suivre la progression, publier sur GitHub.
- **Dans le projet** : un commit par sous-étape validée.

**LLM local vs API**
- **Ollama (local)** : gratuit, les données restent sur ma machine, mais la qualité dépend du matériel (8 Go de RAM → modèles d'environ 3B paramètres).
- **API (OpenAI…)** : très bonne qualité, rien à installer, mais payant et les données partent chez le fournisseur.

### À retenir

- `py -3.13` plutôt que `python` tant que le venv n'existe pas.
- Vérifier ses outils avec `--version` avant de commencer un projet.

---

## Étape 1.2 — Arborescence du projet et packages Python

### Ce que j'ai fait

- Créé les packages Python de `app/` : `core`, `ingestion`, `embeddings`, `vectorstore`, `retrieval`, `generation`, `rag`, `api`, chacun avec un `__init__.py` vide.
- Créé les dossiers `frontend/`, `scripts/`, `tests/unit/`, `tests/integration/`, `data/raw/`, `data/processed/`, `storage/chroma/`.
- Ajouté des `.gitkeep` dans `data/raw/`, `data/processed/` et `storage/chroma/`.
- Vérifié les imports :
  ```powershell
  py -3.13 -c "import app, app.core, app.ingestion; print('OK')"
  ```

### Notions apprises

**Module**
- **Définition** : un fichier `.py`.
- **Exemple** : `app/core/config.py` est le module `app.core.config`.

**Package**
- **Définition** : un dossier qui regroupe des modules et contient un fichier `__init__.py`.
- **Pourquoi** : organiser le code par responsabilité et écrire des imports clairs (`from app.ingestion.pdf_loader import ...`).
- **Fonctionnement** : pour `import app.ingestion`, Python cherche `app/` dans `sys.path`, exécute `app/__init__.py`, puis `app/ingestion/__init__.py`.

**`__init__.py`**
- **Définition** : fichier (souvent vide) qui marque un dossier comme package Python.
- **Pourquoi le mettre alors que Python 3.3+ s'en passe** : l'intention est explicite, pytest, mypy et l'IDE sont plus fiables, et on évite les collisions entre *namespace packages*.

**`sys.path`**
- **Définition** : liste des dossiers où Python cherche les modules à importer.
- **Conséquence** : le dossier courant en fait partie, d'où la règle **toujours exécuter depuis la racine du projet**.

**Imports absolus vs relatifs**
- **Absolu** : `from app.core.config import settings`. Lisible, c'est la règle du projet.
- **Relatif** : `from ..core import config`. Il casse facilement si on déplace un fichier.

**`.gitkeep`**
- **Définition** : fichier vide, simple convention (pas une fonctionnalité de Git).
- **Pourquoi** : Git ne suit que des fichiers, pas les dossiers. Un dossier vide disparaîtrait du dépôt.

**`__pycache__/`**
- **Définition** : dossier créé automatiquement par Python. Il contient le *bytecode* compilé (`.pyc`) pour accélérer les imports suivants.
- **À faire** : l'exclure de Git (via `.gitignore`, étape 1.6).

### À retenir

- Package = dossier + `__init__.py` ; module = fichier `.py`.
- Chaque brique du RAG est un package séparé : séparation des responsabilités.
- `rag/` orchestre, les autres packages ne se connaissent pas entre eux.

---

## Étape 1.3 — Environnement virtuel Python

> Statut : validée le 2026-10-11

### Ce que j'ai fait

- Autorisé les scripts PowerShell (une seule fois) :
  ```powershell
  Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
  ```
- Créé `.venv` et mis pip à jour :
  ```powershell
  py -3.13 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  ```
- Résultat réel : Python **3.13.14**, `sys.prefix` = `C:\dev\rag-project\.venv`, et `pip list` ne montre que `pip 26.2.1`. Le venv est bien isolé.
- Sélectionner l'interpréteur dans VS Code : `Ctrl+Shift+P` → « Python: Select Interpreter » → `.venv`.

**Contenu réel de mon `pyvenv.cfg` :**
```
home = C:\Users\hoang\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.13_...
include-system-site-packages = false
version = 3.13.14
```
- `home` : le Python d'origine. Le mien vient du **Microsoft Store** (dossier `WindowsApps`).
- `include-system-site-packages = false` : les paquets du Python global sont invisibles. C'est l'isolation.

### Notions apprises

**Environnement virtuel (venv)**
- **Définition** : un dossier (ici `.venv/`) qui contient son propre interpréteur Python et son propre répertoire de paquets installés (`site-packages`), séparés du Python système.
- **Pourquoi** :
  - éviter les conflits de versions entre projets ;
  - rendre l'environnement reproductible (avec `requirements.txt`) ;
  - ne pas polluer le Python système (pour réinitialiser, il suffit de supprimer `.venv/`).
- **Fonctionnement interne** :
  - `pyvenv.cfg` indique le chemin du Python d'origine ;
  - `Scripts\python.exe` démarre Python en mode venv, avec `sys.prefix` = `.venv` ;
  - les paquets s'installent dans `.venv\Lib\site-packages` ;
  - la bibliothèque standard (`os`, `json`…) n'est pas copiée.
- **Exemple** :
  - avant activation : `python` → `Python310\python.exe` (3.10.7)
  - après activation : `python` → `.venv\Scripts\python.exe` (3.13)
- **Rôle dans le RAG** : toutes les dépendances (PyTorch, ChromaDB, FastAPI…) seront installées uniquement dans ce venv.

**Activation d'un venv**
- **Définition** : exécuter `Activate.ps1`, qui place `.venv\Scripts` **en tête du `PATH`**.
- **Signe visible** : le préfixe `(.venv)` dans le terminal.
- **Désactiver** : `deactivate`.

**Politique d'exécution PowerShell (`ExecutionPolicy`)**
- **Définition** : règle de sécurité Windows qui bloque les scripts `.ps1` par défaut.
- **`RemoteSigned`** : autorise les scripts locaux ; seuls les scripts téléchargés doivent être signés.

**`python -m pip` plutôt que `pip`**
- **Pourquoi** : `python -m pip` installe dans **le Python appelé**. `pip` seul peut pointer vers un autre Python du `PATH`.

**Chemins longs Windows (`LongPathsEnabled`)**
- **Définition** : par défaut, Windows limite les chemins de fichiers à 260 caractères (`MAX_PATH`).
- **Pourquoi c'est important** : de gros paquets comme PyTorch contiennent des chemins très profonds. Si l'installation échoue avec « No such file or directory » ou « path too long », c'est souvent la cause.
- **Sur ma machine** : désactivé (`0`). Ce n'est pas bloquant tant que le projet reste à un chemin court (`C:\dev\rag-project`).

### À retenir

- Un venv, c'est un `python.exe`, un `pyvenv.cfg` et un `site-packages` isolé.
- Activer un venv revient seulement à modifier le `PATH`.
- `.venv/` est jetable, ne se déplace pas et ne va **jamais** dans Git.

---

## Étape 1.4 — Gestion des dépendances

> Statut : validée le 2026-10-11

### Ce que j'ai fait

1. **Déclaré** les dépendances dans deux fichiers :
   - `requirements.txt` : ce dont l'application a besoin pour tourner ;
   - `requirements-dev.txt` : `-r requirements.txt` + les outils de dev (pytest, ruff).
2. **Installé tout en une seule commande** :
   ```powershell
   python -m pip install -r requirements-dev.txt
   ```
3. **Vérifié** :
   ```powershell
   python -m pip check        # → No broken requirements found.
   python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
   # → 2.14.1+cpu False
   ```
4. **Figé** les versions réellement installées (`>=` remplacé par `==`) et vérifié avec `--dry-run` que rien ne serait réinstallé.

**Mes dépendances et leur rôle :**

| Paquet | Version | Rôle dans le RAG |
|---|---|---|
| `pymupdf` | 1.28.2 | Extraire le texte des PDF, page par page (Phase 2) |
| `sentence-transformers` | 6.1.0 | Transformer un texte en vecteur (Phase 4) |
| `chromadb` | 1.5.9 | Stocker et rechercher les vecteurs (Phase 5) |
| `pydantic-settings` | 2.15.0 | Configuration typée depuis `.env` (étape 1.5) |
| `httpx` | 0.28.1 | Appeler l'API HTTP locale d'Ollama (Phase 7) |
| `pytest` | 9.1.1 | Tests automatisés (dev) |
| `ruff` | 0.17.0 | Vérifier et formater le code (dev) |

Résultat : 7 dépendances déclarées, mais **106 paquets installés** et environ 1,3 Go.

### Notions apprises

**Dépendance**
- **Définition** : une bibliothèque externe dont mon code a besoin pour fonctionner.
- **Exemple** : mon futur `pdf_loader.py` fera `import pymupdf`. Sans ce paquet, le programme plante avec `ModuleNotFoundError`.

**Dépendance directe vs transitive**
- **Directe** : celle que j'utilise moi-même dans mon code et que je déclare (ex. `chromadb`).
- **Transitive** : une dépendance de mes dépendances, installée automatiquement par pip (ex. `chromadb` → `kubernetes` → `requests` → `oauthlib`).
- **Pourquoi c'est important** : 7 lignes déclarées ont donné 106 paquets. Chaque paquet est une source possible de conflit ou de faille.

**`requirements.txt`**
- **Définition** : fichier texte qui liste les dépendances, une par ligne. pip le lit avec `pip install -r`.
- **Pourquoi** : c'est la **source de vérité** de l'environnement. On partage ce fichier, jamais le dossier `.venv/`.
- **Pourquoi deux fichiers** : en production, on n'a pas besoin de pytest ni de ruff. `-r requirements.txt` inclut un fichier dans un autre, ce qui évite les doublons.

**Spécificateurs de version**

| Écriture | Signification | Usage |
|---|---|---|
| `pymupdf` | N'importe quelle version | ❌ Pas reproductible |
| `pymupdf>=1.24` | 1.24 ou plus récent | Version minimale, avant le figeage |
| `pymupdf~=1.28.0` | ≥ 1.28.0 et < 1.29 | Accepte seulement les correctifs |
| `pymupdf==1.28.2` | Exactement 1.28.2 | ✅ Reproductible, mon choix |

**Versionnement sémantique (SemVer) `MAJEUR.MINEUR.CORRECTIF`**
- **MAJEUR** (1.x → 2.x) : changements incompatibles, mon code peut casser.
- **MINEUR** (1.27 → 1.28) : nouvelles fonctionnalités, normalement compatibles.
- **CORRECTIF** (1.28.1 → 1.28.2) : corrections de bugs.
- Ce n'est qu'une convention : tous les projets ne la respectent pas strictement, d'où l'intérêt de figer avec `==`.

**Figer les versions (*pinning*)**
- **Définition** : noter la version exacte de chaque dépendance (`==`).
- **Pourquoi** : sans cela, une réinstallation dans 6 mois prendrait les dernières versions. Une mise à jour majeure pourrait alors casser le projet (« ça marchait sur ma machine… »).
- **Compromis** : je ne reçois plus automatiquement les correctifs, il faut mettre à jour volontairement.
- **Limite** : seules les dépendances **directes** sont figées. Pour tout figer, transitives comprises, on utilise un *lock file* (`pip freeze > requirements-lock.txt`), prévu pour Docker en Phase 12.

**PyPI et wheels**
- **PyPI** : le dépôt public d'où pip télécharge les paquets (pypi.org).
- **Wheel (`.whl`)** : un paquet **précompilé** pour un OS et une version de Python donnés. Pas besoin de compilateur C : l'installation est rapide.

**PyTorch CPU vs GPU (CUDA)**
- **PyTorch** : la bibliothèque de calcul sur laquelle s'appuie sentence-transformers.
- **Version installée** : `2.14.1+cpu`. Le suffixe `+cpu` indique une version sans support GPU. Sous Windows, c'est celle que PyPI fournit par défaut.
- **Pourquoi c'est un bon choix ici** : la version CUDA pèse plusieurs Go de plus, et mon GPU (GTX 1650, 4 Go) sera occupé par Ollama. Les embeddings de quelques PDF restent rapides sur CPU.

**`pip check`**
- **Définition** : vérifie que toutes les dépendances installées sont compatibles entre elles.
- **Résultat attendu** : `No broken requirements found.`

**`--dry-run`**
- **Définition** : simule l'installation sans rien modifier.
- **Usage** : j'ai vérifié qu'après le figeage, mes fichiers correspondaient exactement à mon environnement.

### À retenir

- **D'abord déclarer** dans `requirements.txt`, **puis installer** en une commande (`pip install -r`).
- Figer avec `==` pour la reproductibilité.
- 7 dépendances directes peuvent en entraîner des centaines de transitives.
- On n'ajoute un paquet que si on sait **pourquoi** on en a besoin (FastAPI et Streamlit viendront en Phases 9 et 10).
- Avec PyMuPDF, écrire `import pymupdf` : l'ancien `import fitz` est déprécié.

---

## Étape 1.5-A — Configuration centralisée

> Statut : validée le 2026-10-11

### Ce que j'ai fait

- Créé `app/core/config.py` : classe `Settings`, constante `PROJECT_ROOT`, fonction `get_settings()`.
- Créé `.env.example` : modèle documenté des variables (commité dans Git, sans secrets).
- Créé `tests/unit/test_config.py` : mes 4 premiers tests automatisés.
- Vérifié :
  ```powershell
  python -c "from app.core.config import get_settings; print(get_settings().model_dump())"
  python -m pytest tests -v      # → 4 passed
  ruff check app tests           # → All checks passed!
  ruff format app tests          # → reformate automatiquement le code
  ```

### Tests (pytest)

**Fichier** : `tests/unit/test_config.py` · **Module testé** : `app/core/config.py`

| Test | Ce qu'il vérifie | Pourquoi c'est important |
|---|---|---|
| `test_default_values` | Sans `.env` ni variable, `log_level == "INFO"` et `chroma_dir` = `<racine>/storage/chroma` | Le projet fonctionne « out of the box », sans configuration |
| `test_environment_variable_overrides_default` | `RAG_LOG_LEVEL=debug` donne `log_level == "DEBUG"` | L'environnement passe avant la valeur par défaut, et la casse est normalisée |
| `test_relative_path_is_resolved_from_project_root` | `RAG_CHROMA_DIR=storage/test_chroma` donne `<racine>/storage/test_chroma` | Les chemins ne dépendent pas du dossier de lancement |
| `test_invalid_log_level_is_rejected` | `RAG_LOG_LEVEL=VERBOSE` lève une `ValidationError` | *Fail fast* : une configuration invalide est refusée au démarrage |

**Techniques utilisées :**
- `make_settings()` appelle `Settings(_env_file=None)`, qui ignore mon vrai `.env`. Les tests donnent donc le même résultat sur toutes les machines.
- `monkeypatch.setenv("RAG_...", "...")` crée une variable d'environnement temporaire, annulée à la fin du test.
- `with pytest.raises(ValidationError):` vérifie qu'une erreur **doit** être levée. Le test échoue si elle ne l'est pas.

**Lancer seulement ces tests :**
```powershell
python -m pytest tests/unit/test_config.py -v
```

**Résultat réel (2026-10-11)** : `4 passed in 0.26s`

### Notions apprises

**Configuration centralisée**
- **Définition** : un seul endroit du code (`app/core/config.py`) où sont définis tous les paramètres modifiables.
- **Pourquoi** : sans cela, des valeurs comme `"storage/chroma"` ou `chunk_size=800` seraient éparpillées en dur dans dix fichiers. Changer un paramètre obligerait à les chercher partout, avec un risque d'oubli.
- **Règle du projet** : aucun module ne lit `os.environ` lui-même ; tous passent par `get_settings()`.

**Variable d'environnement**
- **Définition** : une paire `NOM=valeur` fournie au programme par le système d'exploitation, hors du code.
- **Exemple** : `$env:RAG_LOG_LEVEL = "DEBUG"` (PowerShell), puis lancer Python.
- **Pourquoi** : changer le comportement sans modifier le code, et garder les secrets (clés API) hors de Git.

**Fichier `.env` et `.env.example`**
- **`.env`** : mes valeurs locales (et plus tard mes secrets). **Jamais commité.**
- **`.env.example`** : modèle **commité** qui montre quelles variables existent, sans valeurs sensibles.
- **Créer son `.env`** : `Copy-Item .env.example .env`.

**Priorité des sources de configuration**
1. Variable d'environnement (la plus forte)
2. Fichier `.env`
3. Valeur par défaut dans `Settings` (la plus faible)

**pydantic-settings / `BaseSettings`**
- **Définition** : bibliothèque qui lit les variables d'environnement et le `.env`, puis les **convertit** et les **valide** selon les types déclarés.
- **Fonctionnement** : pour le champ `log_level`, elle cherche `RAG_LOG_LEVEL` (préfixe + nom du champ). Une variable d'environnement est toujours une chaîne (`"120"`) ; Pydantic la convertit selon l'annotation (`int`, `Path`…).
- **Validation** : `RAG_LOG_LEVEL=VERBOSE` lève une `ValidationError` **au démarrage**, plutôt qu'un bug obscur plus tard (*fail fast*).

**Préfixe `RAG_`**
- **Pourquoi** : éviter les collisions avec d'autres variables du système (beaucoup de programmes utilisent `LOG_LEVEL`).

**`Literal`**
- **Définition** : type qui n'accepte qu'une liste fermée de valeurs, ici `Literal["DEBUG", "INFO", ...]`.

**`field_validator`**
- **Définition** : fonction appelée par Pydantic pour transformer ou vérifier un champ.
- **Dans mon code** :
  - `mode="before"` convertit `"debug"` en `"DEBUG"` **avant** la vérification du type ;
  - par défaut (`mode="after"`), un chemin relatif est transformé en chemin depuis `PROJECT_ROOT`.

**`PROJECT_ROOT` et `Path(__file__).resolve().parents[2]`**
- `__file__` : chemin du fichier en cours (`.../app/core/config.py`).
- `.resolve()` : le rend absolu.
- `.parents[0]` = `app/core`, `.parents[1]` = `app`, `.parents[2]` = **racine du projet**.
- **Pourquoi** : les chemins sont alors corrects quel que soit le dossier depuis lequel on lance le programme.

**`@lru_cache` sur `get_settings()`**
- **Définition** : mémorise le résultat de la fonction. Le premier appel crée `Settings()`, les suivants renvoient **le même objet**.
- **Pourquoi** : le `.env` n'est lu qu'une fois. FastAPI utilise ce même schéma en Phase 9.
- **En test** : `get_settings.cache_clear()` vide le cache.

**Test unitaire (pytest)**
- **Définition** : une fonction `test_...` qui vérifie un petit comportement précis avec `assert`.
- **Structure** : *Arrange* (préparer) → *Act* (exécuter) → *Assert* (vérifier).
- **`monkeypatch.setenv(...)`** : définit une variable d'environnement **seulement pendant le test**, puis la restaure.
- **`pytest.raises(ValidationError)`** : vérifie qu'une erreur est bien levée.
- **`Settings(_env_file=None)`** : ignore mon vrai `.env`, pour que les tests soient **déterministes**.

**`python -m pytest` plutôt que `pytest`**
- `python -m` ajoute le dossier courant à `sys.path`, donc `import app` fonctionne depuis les tests.

**Ruff : `check` vs `format`**
- `ruff check` : **linter**, il détecte les erreurs probables (import inutilisé, variable non définie…).
- `ruff format` : **formateur**, il réécrit la mise en forme (ex. lignes de plus de 88 caractères coupées).

### À retenir

- Un seul endroit pour la configuration, un accès unique : `get_settings()`.
- Priorité : environnement > `.env` > défaut.
- Valider la configuration au démarrage (*fail fast*).
- `.env` jamais dans Git, `.env.example` toujours dans Git.
- Les paramètres de chaque phase seront ajoutés à `Settings` au fur et à mesure.

---

## Étape 1.5-B — Logging

> Statut : validée le 2026-10-11

### Ce que j'ai fait

- Créé `app/core/logging_config.py` avec la fonction `setup_logging()`.
- Créé `tests/unit/test_logging_config.py` (4 tests).
- Vérifié : `python -m pytest tests -v` → **8 passed**.
- Démonstration réelle (niveau INFO) :
  ```
  2026-10-11 22:11:44 | INFO     | app.demo | Démarrage de l application
  2026-10-11 22:11:44 | WARNING  | app.demo | Aucun PDF trouvé dans data/raw
  2026-10-11 22:11:44 | ERROR    | app.demo | Ollama injoignable
  ```
  Le message DEBUG n'apparaît pas : il est sous le niveau configuré.

### Tests (pytest)

**Fichier** : `tests/unit/test_logging_config.py` · **Module testé** : `app/core/logging_config.py`

| Test | Ce qu'il vérifie | Pourquoi c'est important |
|---|---|---|
| `test_root_level_is_applied` | Après `setup_logging("DEBUG")`, le logger racine est au niveau DEBUG | Le niveau demandé est bien appliqué |
| `test_repeated_calls_do_not_duplicate_handler` | Deux appels à `setup_logging()` laissent **un seul** handler `rag_console` | Idempotence : pas de messages en double avec Streamlit |
| `test_noisy_libraries_only_show_warnings` | Même en DEBUG, le logger `httpx` reste au niveau WARNING | Les logs du projet ne sont pas noyés sous ceux des bibliothèques |
| `test_messages_below_level_are_filtered` | Au niveau WARNING, `logger.warning` est capturé mais pas `logger.info` | Le filtrage par niveau fonctionne réellement |

**Techniques utilisées :**
- **Fixture `restore_root_logger`** (`autouse=True` + `yield`) : elle sauvegarde le niveau et les handlers du logger racine avant chaque test, puis les restaure après. Les tests restent **indépendants** les uns des autres.
- **Fixture `caplog`** (fournie par pytest) : elle capture les messages de log ; `caplog.text` contient tout ce qui a été journalisé.

**Lancer seulement ces tests :**
```powershell
python -m pytest tests/unit/test_logging_config.py -v
```

**Résultat réel (2026-10-11)** : 4 passed (8 au total avec `test_config.py`, en 0.25s)

### Notions apprises

**Logging**
- **Définition** : enregistrer des messages horodatés et classés par gravité sur ce que fait le programme.
- **Pourquoi pas `print()`** :

  | `print()` | `logging` |
  |---|---|
  | Pas de date, pas de gravité, pas d'origine | Date, niveau, nom du module automatiques |
  | Pour le masquer, il faut supprimer la ligne | On change `RAG_LOG_LEVEL`, sans toucher au code |
  | Mélangé à la sortie normale (stdout) | Va sur stderr, séparé des résultats |
  | Une seule destination | Console, fichier, service distant… (handlers) |

- **Rôle dans le RAG** : suivre l'ingestion (« 3 PDF chargés, 42 chunks créés ») et diagnostiquer les erreurs (« Ollama injoignable »).

**Niveaux de log** (du moins grave au plus grave)

| Niveau | Valeur | Usage | Exemple dans le RAG |
|---|---|---|---|
| DEBUG | 10 | Détail pour le développeur | « Chunk 12 : 784 caractères » |
| INFO | 20 | Étapes normales | « 3 PDF chargés » |
| WARNING | 30 | Anormal mais on continue | « Page 5 vide, ignorée » |
| ERROR | 40 | Une opération a échoué | « Impossible de lire fichier.pdf » |
| CRITICAL | 50 | Le programme ne peut plus fonctionner | « Base vectorielle corrompue » |

- **Règle** : un message s'affiche si son niveau est **≥** au niveau configuré. Au niveau INFO (20), DEBUG (10) est masqué.

**Les 3 objets du module `logging`**
- **Logger** : l'objet qui reçoit les messages (`logger.info(...)`). Il est identifié par un nom.
- **Handler** : *où* envoyer les messages (`StreamHandler` → console, `FileHandler` → fichier).
- **Formatter** : *comment* les écrire (`"%(asctime)s | %(levelname)-8s | ..."`).
- **Chaîne** : `logger.info()` → Logger (filtre par niveau) → Handler(s) → Formatter → sortie.

**Hiérarchie des loggers et `getLogger(__name__)`**
- `__name__` vaut le nom du module, ex. `app.ingestion.pdf_loader`.
- Les noms à points forment une **hiérarchie** : `app.ingestion.pdf_loader` → `app.ingestion` → `app` → **logger racine**.
- Un message **remonte** jusqu'au logger racine, où se trouve notre handler. Il suffit donc de configurer la racine **une seule fois**.
- **Avantage** : chaque ligne indique de quel module elle vient.

**Point d'entrée**
- **Définition** : le fichier que l'on lance (script CLI, API, interface).
- **Règle** : seul le point d'entrée appelle `setup_logging()`. Un module de bibliothèque (ex. `chunker.py`) ne configure jamais le logging : il ne fait que `getLogger(__name__)`.

**Idempotence**
- **Définition** : appeler une fonction plusieurs fois donne le même résultat que l'appeler une fois.
- **Dans mon code** : avant d'ajouter le handler `rag_console`, on retire l'ancien. Sans cela, Streamlit, qui ré-exécute le script à chaque clic, afficherait chaque message 2, 3, 4… fois.

**Masquage d'un module standard (*shadowing*)**
- Un fichier nommé `logging.py` dans le projet pourrait être importé à la place du vrai module `logging` de Python. D'où le nom `logging_config.py`.

**Fixture pytest**
- **Définition** : une fonction qui prépare (et nettoie) l'environnement d'un test.
- **`yield`** : le code avant `yield` s'exécute **avant** le test, le code après s'exécute **après**, même si le test échoue.
- **`autouse=True`** : la fixture s'applique automatiquement à tous les tests du fichier.
- **Dans mon test** : elle restaure le logger racine, pour que les tests ne s'influencent pas entre eux.

**`caplog`**
- Fixture fournie par pytest qui **capture les logs** pendant un test (`caplog.text`).

### À retenir

- `print()` pour un script jetable ; `logging` pour une application.
- Dans chaque module : `logger = logging.getLogger(__name__)`.
- `setup_logging()` une seule fois, au point d'entrée.
- Choisir le bon niveau : INFO pour les étapes, WARNING pour l'anormal, ERROR pour les échecs.

---

## Étape 1.6 — Git et GitHub

> Statut : en cours (dépôt initialisé ; premier commit et push à faire)

### Ce que j'ai fait

- Créé `.gitignore` et un `README.md` minimal.
- Initialisé le dépôt : `git init` (branche `main`).
- **Vérifié avant de commiter** :
  ```powershell
  git status --short --untracked-files=all   # → 24 fichiers, aucun PDF ni .venv
  git check-ignore -v .venv .env data/raw/01_introduction_rag.pdf
  # → .gitignore:6:.venv/   .venv   (indique la règle qui exclut chaque fichier)
  ```
- Premier commit et push GitHub : *à compléter*.

### Tests (pytest)

Pas de nouveau test à cette étape. La vérification se fait avec `git status` et `git check-ignore`. Avant le commit, on relance quand même `python -m pytest`, pour ne jamais commiter du code cassé.

### Notions apprises

**Les 3 zones de Git**
```
Répertoire de travail ──git add──► Zone de staging (index) ──git commit──► Dépôt (.git/)
  (mes fichiers)                  (ce qui ira dans le               (historique des
                                   prochain commit)                  commits)
```
- **Répertoire de travail** : mes fichiers tels qu'ils sont sur le disque.
- **Staging** : la sélection des modifications pour le prochain commit. On prépare son commit comme un colis.
- **Dépôt** : l'historique permanent, dans le dossier caché `.git/`.

**Commit**
- **Définition** : un instantané du projet, identifié par un **hash** (ex. `a3f9c1e`), avec un auteur, une date et un message.
- **Bon message** (convention *Conventional Commits*) : `type: description`
  - `feat:` nouvelle fonctionnalité · `fix:` correction · `test:` tests · `docs:` documentation · `chore:` maintenance/configuration
  - Exemple : `feat: extraction du texte des PDF page par page`

**`.gitignore`**
- **Définition** : liste de motifs de fichiers que Git doit **ignorer** (jamais proposés au commit).
- **Syntaxe** :

  | Motif | Signification |
  |---|---|
  | `.env` | Ce fichier précis |
  | `.venv/` | Ce dossier (le `/` final = dossier uniquement) |
  | `*.py[cod]` | Tous les `.pyc`, `.pyo`, `.pyd` (`*` = n'importe quoi, `[cod]` = un caractère parmi c, o, d) |
  | `data/raw/*` | Tout le **contenu** du dossier |
  | `!data/raw/.gitkeep` | `!` = **exception** : ce fichier n'est pas ignoré |

- **Pourquoi `data/raw/*` et non `data/raw/`** : si on ignore le dossier lui-même, Git n'y regarde plus du tout et l'exception `!` ne peut pas fonctionner.
- **Limite importante** : `.gitignore` n'agit que sur les fichiers **pas encore suivis**. Un fichier déjà commité reste suivi ; il faut alors `git rm --cached fichier`.

**Ce qui va (ou non) dans Git**

| ✅ Versionné | ❌ Ignoré | Pourquoi |
|---|---|---|
| Code source, tests | `.venv/` | Le venv se recrée avec `requirements*.txt` |
| `requirements*.txt` | `__pycache__/`, caches | Fichiers générés automatiquement |
| `.env.example` | `.env` | Secrets et réglages personnels |
| `.gitkeep` | PDF de `data/raw/` | Documents potentiellement privés ou volumineux |
| Documentation | `storage/chroma/` | Base générée, reconstruisible par l'ingestion |

**`core.autocrlf`**
- Windows termine les lignes par `CRLF` (`\r\n`), Linux et macOS par `LF` (`\n`).
- `autocrlf=true` : Git stocke en `LF` et redonne du `CRLF` sur Windows. Le dépôt reste propre pour Docker (Linux) en Phase 12.

**Dépôt distant (*remote*), `origin`, `push`**
- **Remote** : une copie du dépôt sur un serveur (GitHub).
- **`origin`** : nom conventionnel du remote principal.
- **`git push -u origin main`** : envoie la branche `main` vers `origin`. `-u` mémorise ce lien, ensuite `git push` suffit.

### À retenir

- Toujours vérifier `git status` **avant** `git commit`.
- `.gitignore` en **premier**, avant le premier `git add`.
- Jamais de `.env`, de `.venv/` ni de documents privés dans Git.
- Un commit = une étape cohérente, avec un message clair.

---

# Registre des tests (pytest)

## Commandes essentielles

À lancer depuis la racine du projet, avec le venv activé (`(.venv)` dans l'invite) :

| Commande | Effet |
|---|---|
| `python -m pytest` | Lance **tous** les tests (résumé court) |
| `python -m pytest -v` | Mode *verbose* : affiche chaque test avec PASSED/FAILED |
| `python -m pytest tests/unit/test_config.py` | Lance un seul fichier |
| `python -m pytest tests/unit/test_config.py::test_default_values` | Lance un seul test |
| `python -m pytest -k "logging"` | Lance les tests dont le nom contient « logging » |
| `python -m pytest -x` | S'arrête au premier échec |
| `python -m pytest -s` | Affiche les `print()` (normalement capturés par pytest) |

> Toujours `python -m pytest` et non `pytest` seul : `-m` ajoute la racine du projet à `sys.path`, donc `import app` fonctionne.

## Comment pytest trouve les tests

- Il cherche les fichiers nommés `test_*.py`.
- Dans ces fichiers, il exécute les fonctions nommées `test_*`.
- Un test **réussit** si aucune exception n'est levée. Il **échoue** si un `assert` est faux ou si une erreur inattendue survient.

## Organisation des dossiers

| Dossier | Type de test | Caractéristiques |
|---|---|---|
| `tests/unit/` | Tests unitaires | Une seule fonction ou classe, rapide, sans réseau ni modèle lourd |
| `tests/integration/` | Tests d'intégration | Plusieurs modules ensemble (ex. PDF → chunks → ChromaDB) |

## Catalogue des tests

| Fichier | Module testé | Nb | Étape | Détail |
|---|---|---|---|---|
| `tests/unit/test_config.py` | `app/core/config.py` | 4 | 1.5-A | [voir](#étape-15-a--configuration-centralisée) |
| `tests/unit/test_logging_config.py` | `app/core/logging_config.py` | 4 | 1.5-B | [voir](#étape-15-b--logging) |
| **Total** | | **8** | | |

## Historique des exécutions (résultats réels)

| Date | Étape | Commande | Résultat |
|---|---|---|---|
| 2026-10-11 | 1.5-A | `python -m pytest tests -v` | 4 passed in 0.26s |
| 2026-10-11 | 1.5-A | après `ruff format` | 4 passed in 0.24s |
| 2026-10-11 | 1.5-B | `python -m pytest tests -v` | 8 passed in 0.25s |

## Lire un résultat pytest

```
tests/unit/test_config.py::test_default_values PASSED     [ 12%]
└── fichier ──────────────┘ └── fonction ─────┘ └statut┘  └progression┘
```

| Symbole | Signification |
|---|---|
| `.` ou `PASSED` | Test réussi |
| `F` ou `FAILED` | Un `assert` est faux |
| `E` ou `ERROR` | Erreur avant le test (ex. dans une fixture, import impossible) |
| `s` ou `SKIPPED` | Test volontairement ignoré |

---

# Glossaire

| Terme | Définition courte | Étape |
|---|---|---|
| Interpréteur | Programme qui exécute le code Python | 1.1 |
| Py launcher | `py.exe`, choisit une version de Python sous Windows | 1.1 |
| `PATH` | Liste des dossiers où Windows cherche les programmes | 1.1 |
| Git / commit | Contrôle de version / instantané du projet | 1.1 |
| Module | Fichier `.py` | 1.2 |
| Package | Dossier + `__init__.py` | 1.2 |
| `sys.path` | Dossiers où Python cherche les modules | 1.2 |
| `.gitkeep` | Fichier vide pour garder un dossier dans Git | 1.2 |
| `__pycache__` | Bytecode compilé, généré automatiquement | 1.2 |
| venv | Environnement Python isolé par projet | 1.3 |
| `site-packages` | Dossier où sont installés les paquets | 1.3 |
| Activation | Ajout de `.venv\Scripts` en tête du `PATH` | 1.3 |
| `pyvenv.cfg` | Fichier de config du venv (Python d'origine, isolation) | 1.3 |
| `MAX_PATH` | Limite de 260 caractères des chemins Windows | 1.3 |
| Dépendance directe | Paquet que j'utilise et déclare moi-même | 1.4 |
| Dépendance transitive | Dépendance d'une dépendance, installée automatiquement | 1.4 |
| `requirements.txt` | Liste des dépendances, lue par `pip install -r` | 1.4 |
| Pinning (`==`) | Figer une version exacte pour la reproductibilité | 1.4 |
| SemVer | Convention `MAJEUR.MINEUR.CORRECTIF` | 1.4 |
| Wheel | Paquet Python précompilé (`.whl`) | 1.4 |
| PyPI | Dépôt public des paquets Python | 1.4 |
| `pip check` | Vérifie la compatibilité des paquets installés | 1.4 |
| Lock file | Fichier figeant **toutes** les versions, transitives comprises | 1.4 |
| Configuration centralisée | Tous les paramètres au même endroit (`config.py`) | 1.5-A |
| Variable d'environnement | `NOM=valeur` fourni par l'OS, hors du code | 1.5-A |
| `.env` / `.env.example` | Valeurs locales (non commitées) / modèle (commité) | 1.5-A |
| `BaseSettings` | Classe pydantic-settings : lit et valide la configuration | 1.5-A |
| Fail fast | Échouer tôt, au démarrage, si la configuration est invalide | 1.5-A |
| `lru_cache` | Mémorise le résultat d'une fonction | 1.5-A |
| Test unitaire | Petite fonction qui vérifie un comportement avec `assert` | 1.5-A |
| `monkeypatch` | Outil pytest pour modifier temporairement l'environnement | 1.5-A |
| Linter / formateur | `ruff check` (erreurs) / `ruff format` (mise en forme) | 1.5-A |
| Logging | Messages horodatés classés par gravité | 1.5-B |
| Niveau de log | DEBUG < INFO < WARNING < ERROR < CRITICAL | 1.5-B |
| Logger / Handler / Formatter | Qui reçoit / où envoyer / comment écrire | 1.5-B |
| Logger racine | Sommet de la hiérarchie ; tous les messages y remontent | 1.5-B |
| Point d'entrée | Fichier lancé ; seul endroit où l'on configure le logging | 1.5-B |
| Idempotence | Plusieurs appels donnent le même effet qu'un seul | 1.5-B |
| Shadowing | Un fichier local qui masque un module standard du même nom | 1.5-B |
| Fixture | Préparation/nettoyage d'un test (`yield`) | 1.5-B |
| `caplog` | Fixture pytest qui capture les logs | 1.5-B |
| `pytest.raises` | Vérifie qu'une exception est bien levée | 1.5-A |
| Test déterministe | Donne toujours le même résultat, sur toutes les machines | 1.5-A |
| Test d'intégration | Teste plusieurs modules ensemble | Registre |
| Staging (index) | Zone de préparation du prochain commit (`git add`) | 1.6 |
| `.gitignore` | Motifs des fichiers que Git ignore | 1.6 |
| Conventional Commits | Convention de messages `type: description` | 1.6 |
| CRLF / LF | Fins de ligne Windows / Linux | 1.6 |
| Remote / `origin` | Copie distante du dépôt / son nom conventionnel | 1.6 |
| `push` | Envoyer ses commits vers le remote | 1.6 |
** Pourquoi utiliser config.py ? **
Imaginons que ton RAG utilise :
- Un modèle d'embeddings : all-MiniLM-L6-v2
- Une taille de chunk : 800
- Un overlap : 150
- Un nombre de documents récupérés (Top-K) : 5
- Une base vectorielle : ChromaDB
Sans fichier de configuration, tu risques de répéter ces valeurs dans plusieurs fichiers.
Avec config.py, tu peux modifier un paramètre à un seul endroit.