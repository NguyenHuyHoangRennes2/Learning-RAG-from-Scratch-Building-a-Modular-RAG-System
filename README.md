# RAG Student Project

Assistant de questions-réponses sur des documents PDF, basé sur le
**Retrieval-Augmented Generation (RAG)**. Il est entièrement local : Ollama, ChromaDB et Sentence Transformers.

> 🚧 Projet en cours de développement. Le README complet sera rédigé en fin de projet.

## Installation (Windows / PowerShell)

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

## Tests

```powershell
python -m pytest -v
```
