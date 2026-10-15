"""Interface web du RAG (Streamlit).

Lancement (depuis la racine du projet, venv activé, API démarrée) :
    python -m streamlit run frontend/streamlit_app.py
« python -m » ajoute la racine du projet au chemin d'import (pour « frontend » et « app »).

L'interface ne parle au RAG QUE par l'API HTTP (frontend/api_client.py).
"""

# Any : les réponses JSON sont des dictionnaires aux valeurs variées
from typing import Any

# Streamlit : chaque interaction relance ce script de haut en bas
import streamlit as st

# Seule la CONFIGURATION est lue côté application (adresse de l'API), jamais le pipeline
from app.core.config import get_settings

# Client HTTP de l'API
from frontend.api_client import ApiError, RAGApiClient

# Titre et icône de l'onglet du navigateur ; mise en page large
st.set_page_config(page_title="RAG — mes PDF", page_icon="📚", layout="wide")


@st.cache_resource
def get_client() -> RAGApiClient:
    """Client créé une seule fois (cache_resource), puis réutilisé à chaque relance du script."""
    # Adresse de l'API lue dans la configuration centralisée
    return RAGApiClient(get_settings().api_base_url)


def render_sidebar(client: RAGApiClient) -> None:
    """Barre latérale : état du système, envoi de PDF, documents indexés."""
    # Titre de la barre latérale
    st.sidebar.header("📂 Documents")

    # État de l'API et du LLM
    try:
        # GET /health
        health = client.health()
    except ApiError as error:
        # API éteinte : on l'explique et on s'arrête là pour la barre latérale
        st.sidebar.error(str(error))
        return

    # Résumé de l'index
    st.sidebar.caption(
        f"{health['documents']} document(s), {health['chunks']} chunk(s) indexé(s)"
    )

    # Avertit si le LLM n'est pas disponible (la recherche fonctionne quand même côté API)
    if not health["llm_available"]:
        # Message d'aide
        st.sidebar.warning(
            f"LLM « {health['llm_model']} » indisponible : installez Ollama puis "
            f"`ollama pull {health['llm_model']}`."
        )

    # Envoi d'un PDF
    uploaded = st.sidebar.file_uploader("Ajouter un PDF", type=["pdf"])

    # Bouton d'indexation, actif seulement si un fichier est choisi
    if uploaded is not None and st.sidebar.button("Indexer ce PDF", type="primary"):
        # Indexation (peut prendre quelques secondes)
        with st.sidebar.status("Indexation en cours..."):
            try:
                # POST /documents
                report = client.upload(uploaded.name, uploaded.getvalue())
            except ApiError as error:
                # Erreur lisible (415, 409, 413, 422...)
                st.sidebar.error(str(error))
            else:
                # Compte rendu
                if report["status"] == "skipped":
                    st.sidebar.info(f"{report['source']} est déjà indexé.")
                else:
                    st.sidebar.success(
                        f"{report['source']} : {report['chunk_count']} chunk(s) indexé(s)."
                    )

    # Liste des documents, avec un bouton de suppression pour chacun
    for document in client.list_documents():
        # Nom du fichier et nombre de chunks côte à côte avec le bouton
        left, right = st.sidebar.columns([4, 1])
        left.write(f"📄 {document['source']} ({document['chunk_count']} chunks)")

        # key unique : Streamlit doit distinguer les boutons
        if right.button(
            "🗑️", key=f"delete-{document['document_id']}", help="Retirer de l'index"
        ):
            # DELETE /documents/{id}, puis relance du script pour rafraîchir la liste
            client.delete(document["document_id"])
            st.rerun()


def render_answer(result: dict[str, Any]) -> None:
    """Affiche une réponse : texte, abstention éventuelle, sources numérotées."""
    # Le texte de la réponse (avec ses citations [n])
    st.markdown(result["answer"])

    # Abstention : le système dit ne pas savoir plutôt que d'inventer
    if result["abstained"]:
        st.info(
            "Les documents ne contiennent pas d'information suffisante pour répondre."
        )

    # Sources fournies au LLM, repliées par défaut
    with st.expander(
        f"Sources ({len(result['sources'])}) — recherche {result['retrieval_ms']:.0f} ms, génération {result['generation_ms']:.0f} ms"
    ):
        # Une entrée par source
        for source in result["sources"]:
            # ✅ si la réponse cite cette source
            mark = "✅ citée" if source["cited"] else "non citée"
            st.markdown(
                f"**[{source['number']}] {source['source']}, p. {source['page_number']}** "
                f"— score {source['score']:.3f} — {mark}"
            )

            # Le texte exact du passage, pour vérifier la réponse
            st.caption(source["text"])


def main() -> None:
    """Page principale : historique des échanges et zone de question."""
    # Titre de la page
    st.title("📚 Questions sur vos PDF")
    st.caption(
        "Réponses rédigées UNIQUEMENT à partir de vos documents, avec leurs sources."
    )

    # Client de l'API
    client = get_client()

    # Barre latérale
    render_sidebar(client)

    # Historique de la conversation, conservé entre deux relances du script
    if "history" not in st.session_state:
        # Liste de (question, réponse)
        st.session_state.history = []

    # Réaffiche les échanges précédents
    for question, result in st.session_state.history:
        # Bulle de l'utilisateur
        st.chat_message("user").write(question)

        # Bulle de l'assistant
        with st.chat_message("assistant"):
            render_answer(result)

    # Zone de saisie en bas de page
    question = st.chat_input("Posez une question sur vos documents...")

    # Rien de saisi : fin du script
    if not question:
        return

    # Affiche la question
    st.chat_message("user").write(question)

    # Interroge l'API et affiche la réponse
    with st.chat_message("assistant"):
        try:
            # POST /ask (peut prendre plusieurs secondes : génération par le LLM)
            with st.spinner("Recherche et rédaction de la réponse..."):
                result = client.ask(question)
        except ApiError as error:
            # 503 (LLM absent), 422 (question invalide), API éteinte...
            st.error(str(error))
            return

        # Affiche puis mémorise l'échange
        render_answer(result)
        st.session_state.history.append((question, result))


# Streamlit exécute le script : on lance la page
main()
