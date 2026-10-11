"""Configuration du logging de l'application.

``setup_logging()`` est appelée UNE seule fois, au point d'entrée du programme
(script CLI, API FastAPI, interface Streamlit). Les autres modules n'appellent
jamais cette fonction ; ils se contentent de :

    import logging
    logger = logging.getLogger(__name__)
    logger.info("Message")

Le fichier ne s'appelle pas ``logging.py`` pour ne pas masquer le module
``logging`` de la bibliothèque standard.
"""

import logging
import sys

from app.core.config import get_settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
HANDLER_NAME = "rag_console"

# Bibliothèques tierces très bavardes : on ne garde que leurs avertissements.
NOISY_LIBRARIES = ("httpx", "httpcore", "urllib3")


def setup_logging(level: str | None = None) -> None:
    """Configure le logger racine : niveau, format et sortie console.

    La fonction peut être rappelée sans dupliquer les messages (utile avec
    Streamlit, qui ré-exécute le script à chaque interaction).

    Args:
        level: Niveau à appliquer ("DEBUG", "INFO"...). Par défaut, la valeur
            de ``RAG_LOG_LEVEL`` lue dans la configuration.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level or get_settings().log_level)

    # Retire notre handler s'il existe déjà, sans toucher aux autres
    # (ex. celui de pytest qui capture les logs pendant les tests).
    for handler in root_logger.handlers[:]:
        if handler.get_name() == HANDLER_NAME:
            root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.set_name(HANDLER_NAME)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)

    for library in NOISY_LIBRARIES:
        logging.getLogger(library).setLevel(logging.WARNING)
