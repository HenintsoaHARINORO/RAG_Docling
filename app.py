# app.py — Streamlit entry point

import logging

from dotenv import load_dotenv
import streamlit as st

import db
from chain import get_conversationchain
from config import FAISS_INDEX_NAME
from htmlTemplates import css
from ui import handle_question, render_sidebar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def _init_session() -> None:
    """Initialise Streamlit session-state keys on first run."""
    st.session_state.setdefault("conversation", None)
    st.session_state.setdefault("chat_history", [])


def _autoload_index() -> None:
    """On startup, reload any previously persisted FAISS index from PostgreSQL."""
    if st.session_state.conversation is not None:
        return

    vectorstore = db.load_faiss_index(FAISS_INDEX_NAME)
    if vectorstore:
        st.session_state.conversation = get_conversationchain(vectorstore)
        st.sidebar.info("Loaded previous index from PostgreSQL.")


def main() -> None:
    load_dotenv()
    db.init_db()

    st.set_page_config(page_title="AskMyDocs", page_icon=":books:")
    st.write(css, unsafe_allow_html=True)

    _init_session()
    _autoload_index()

    # ── Main area ──────────────────────────────────────────────────────────
    st.header("AskMyDocs :books:")
    question = st.text_input("Ask a question about your documents:")
    if question:
        if st.session_state.conversation is None:
            st.warning("Please upload and process at least one document first.")
        else:
            handle_question(question)

    # ── Sidebar ────────────────────────────────────────────────────────────
    render_sidebar()


if __name__ == "__main__":
    main()