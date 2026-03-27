# ui/sidebar.py — sidebar: document list, uploader, process button

import streamlit as st

import db
from config import FAISS_INDEX_NAME, SUPPORTED_EXTENSIONS
from pipeline import process_documents
from chain import get_conversationchain


def render_sidebar() -> None:
    """Render the full sidebar: stored docs list + upload / process widget."""
    with st.sidebar:
        st.subheader("Your documents")
        _render_stored_documents()
        st.divider()
        _render_upload_section()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _render_stored_documents() -> None:
    stored_docs = db.list_documents()
    if not stored_docs:
        return

    st.markdown("**Already in database:**")
    for doc in stored_docs:
        col1, col2 = st.columns([3, 1])
        col1.write(f"📄 {doc['filename']}")
        if col2.button("🗑", key=f"del_{doc['id']}"):
            _delete_document(doc["id"])


def _delete_document(doc_id: int) -> None:
    db.delete_document(doc_id)
    db.delete_faiss_index(FAISS_INDEX_NAME)
    st.session_state.conversation = None
    st.rerun()


def _render_upload_section() -> None:
    uploaded_files = st.file_uploader(
        "Upload documents and click 'Process'",
        accept_multiple_files=True,
        type=SUPPORTED_EXTENSIONS,
    )

    if not st.button("Process"):
        return

    if not uploaded_files:
        st.warning("Please upload at least one document.")
        return

    with st.spinner("Processing…"):
        vectorstore = process_documents(uploaded_files)
        if vectorstore:
            st.session_state.conversation = get_conversationchain(vectorstore)
            st.success("Ready to chat!")