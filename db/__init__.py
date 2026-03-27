# db/__init__.py
#
# Public facade — exposes the same names that the rest of the codebase uses,
# so nothing outside this package needs to know about the internal split.
#
# Old name              → New location
# ─────────────────────────────────────────────────────────────
# init_db()             → db.connection.init_db
# get_connection()      → db.connection.get_connection
#
# document_exists()     → db.documents.exists
# save_document()       → db.documents.save
# list_documents()      → db.documents.list_all
# get_document_text()   → db.documents.get_text
# delete_document()     → db.documents.delete
#
# save_chunks()         → db.chunks.save
# load_chunks()         → db.chunks.load
# load_all_chunks()     → db.chunks.load_many
#
# save_faiss_index()    → db.faiss_index.save
# load_faiss_index()    → db.faiss_index.load
# delete_faiss_index()  → db.faiss_index.delete

from db.connection import get_connection, init_db
from db.documents import delete as delete_document
from db.documents import exists as document_exists
from db.documents import get_text as get_document_text
from db.documents import list_all as list_documents
from db.documents import save as save_document
from db.chunks import load as load_chunks
from db.chunks import load_many as load_all_chunks
from db.chunks import save as save_chunks
from db.faiss_index import delete as delete_faiss_index
from db.faiss_index import load as load_faiss_index
from db.faiss_index import save as save_faiss_index

__all__ = [
    # connection
    "get_connection",
    "init_db",
    # documents
    "document_exists",
    "save_document",
    "list_documents",
    "get_document_text",
    "delete_document",
    # chunks
    "save_chunks",
    "load_chunks",
    "load_all_chunks",
    # faiss
    "save_faiss_index",
    "load_faiss_index",
    "delete_faiss_index",
]