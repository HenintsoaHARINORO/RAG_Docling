# db/faiss_index.py — CRUD for the `faiss_index` table

import logging
import pickle

import psycopg2

from db.connection import get_connection

logger = logging.getLogger(__name__)


def save(index_name: str, vectorstore) -> None:
    """Serialize and upsert a FAISS vectorstore."""
    blob = pickle.dumps(vectorstore)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO faiss_index (index_name, index_blob)
                VALUES (%s, %s)
                ON CONFLICT (index_name) DO UPDATE
                    SET index_blob = EXCLUDED.index_blob,
                        updated_at = NOW();
                """,
                (index_name, psycopg2.Binary(blob)),
            )
        conn.commit()


def load(index_name: str):
    """
    Deserialize and return a FAISS vectorstore, or None if not found.

    If the blob was pickled from a different class path (e.g. a pre-refactor
    index) or is otherwise corrupt, the stale row is deleted and None is
    returned so the app rebuilds cleanly instead of crashing.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT index_blob FROM faiss_index WHERE index_name = %s;",
                (index_name,),
            )
            row = cur.fetchone()

    if row is None:
        return None

    try:
        return pickle.loads(bytes(row[0]))
    except Exception as exc:
        logger.warning(
            "Stale or corrupt FAISS index '%s' could not be loaded (%s). "
            "Deleting it — re-process your documents to rebuild.",
            index_name, exc,
        )
        delete(index_name)
        return None


def delete(index_name: str) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM faiss_index WHERE index_name = %s;",
                (index_name,),
            )
        conn.commit()