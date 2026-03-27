# pipeline.py
import logging
import time

import streamlit as st
from langchain_community.vectorstores import faiss

import db
from config import FAISS_INDEX_NAME
from embeddings import warmup_embedder
from ingestion import get_chunks, get_documents_text
from vectorstore import get_vectorstore

logger = logging.getLogger(__name__)


def process_documents(uploaded_files) -> faiss.FAISS | None:
    _persist_new_documents(uploaded_files)
    warmup_embedder()
    return _build_and_save_index()


def _persist_new_documents(uploaded_files) -> None:
    doc_results = get_documents_text(uploaded_files)
    total_start = time.perf_counter()

    for filename, file_bytes, raw_text in doc_results:
        if db.document_exists(file_bytes):
            st.sidebar.info(f"'{filename}' already in DB — skipping re-ingestion.")
            continue

        doc_start = time.perf_counter()
        chunks = get_chunks(raw_text)
        doc_id = db.save_document(filename, file_bytes, raw_text)
        db.save_chunks(doc_id, chunks)
        elapsed = time.perf_counter() - doc_start

        st.sidebar.success(f"'{filename}' saved ({len(chunks)} chunks) — {elapsed:.2f}s")

    total_elapsed = time.perf_counter() - total_start
    st.sidebar.info(f"Total ingestion time: {total_elapsed:.2f}s")


def _build_and_save_index() -> faiss.FAISS | None:
    all_docs   = db.list_documents()
    all_chunks = db.load_all_chunks([d["id"] for d in all_docs])

    if not all_chunks:
        st.sidebar.warning("No chunks found in database.")
        return None

    vectorstore = get_vectorstore(all_chunks, source_name="mixed")
    db.save_faiss_index(FAISS_INDEX_NAME, vectorstore)
    st.sidebar.success(f"FAISS index saved to PostgreSQL ({len(all_chunks)} total chunks).")

    return vectorstore