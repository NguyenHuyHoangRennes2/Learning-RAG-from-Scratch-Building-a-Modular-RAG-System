"""Test de fumée de l'interface Streamlit avec AppTest (le script tourne sans navigateur).

L'API est volontairement injoignable (port fermé) : l'interface doit l'expliquer
proprement au lieu de planter.
"""

# pytest fournit monkeypatch
import pytest

# AppTest exécute un script Streamlit et expose ses éléments affichés
from streamlit.testing.v1 import AppTest

# Le cache de configuration doit être vidé pour prendre en compte la variable d'environnement
from app.core.config import PROJECT_ROOT, get_settings


def test_app_renders_and_reports_unreachable_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Pointe l'interface vers un port où aucune API n'écoute
    monkeypatch.setenv("RAG_API_BASE_URL", "http://127.0.0.1:9")
    get_settings.cache_clear()

    # Exécute le script une fois (timeout large : premier import de Streamlit)
    # (chemin absolu : AppTest résout un chemin relatif depuis le fichier de test)
    script = PROJECT_ROOT / "frontend" / "streamlit_app.py"
    app = AppTest.from_file(str(script), default_timeout=30).run()

    # Aucune exception non gérée, le titre est affiché
    assert not app.exception
    assert app.title[0].value == "📚 Questions sur vos PDF"

    # La barre latérale explique que l'API est injoignable et comment la lancer
    assert "API injoignable" in app.sidebar.error[0].value

    # Remet la configuration par défaut pour les autres tests
    get_settings.cache_clear()
