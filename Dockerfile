# Image unique du RAG : sert l'API (par défaut) ou l'interface Streamlit (voir docker-compose.yml).
# Construction : docker build -t rag-student .

# Python 3.13 (comme en développement), variante « slim » : image de base légère
FROM python:3.13-slim-bookworm

# Pas de fichiers .pyc ; journaux affichés immédiatement ; pas de cache pip (image plus petite) ;
# cache Hugging Face dans /app/.cache (monté en volume : le modèle n'est téléchargé qu'une fois)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface

# Dossier de travail = racine du projet dans le conteneur
WORKDIR /app

# PyTorch en version CPU AVANT le reste : sous Linux, PyPI fournirait la version CUDA (plusieurs Go en plus)
RUN pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu

# Dépendances copiées seules d'abord : cette couche reste en cache tant que requirements.txt ne change pas
COPY requirements.txt .
RUN pip install -r requirements.txt

# Code de l'application (les données et l'index viennent de volumes, pas de l'image)
COPY app ./app
COPY frontend ./frontend
COPY scripts ./scripts
COPY evaluation ./evaluation
COPY .streamlit ./.streamlit

# Utilisateur sans privilèges (bonne pratique de sécurité) et dossiers de données
RUN useradd --create-home appuser \
    && mkdir -p data/raw data/processed storage/chroma .cache \
    && chown -R appuser /app
USER appuser

# Ports : API FastAPI (8000) et interface Streamlit (8501)
EXPOSE 8000 8501

# Commande par défaut : l'API, accessible depuis l'extérieur du conteneur (0.0.0.0)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
