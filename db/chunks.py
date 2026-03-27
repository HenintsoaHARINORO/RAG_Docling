# db/chunks.py — CRUD for the `chunks` table

import psycopg2
import psycopg2.extras

from db.connection import get_connection


def save(doc_id: int, chunks: list[str]) -> None:
    """
    Persist text chunks for *doc_id*.
    Replaces any existing chunks for that document first.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chunks WHERE document_id = %s;", (doc_id,))
            psycopg2.extras.execute_values(
                cur,
                "INSERT INTO chunks (document_id, chunk_index, chunk_text) VALUES %s;",
                [(doc_id, i, text) for i, text in enumerate(chunks)],
            )
        conn.commit()


def load(doc_id: int) -> list[str]:
    """Return chunks for a single document, ordered by chunk_index."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT chunk_text FROM chunks WHERE document_id = %s ORDER BY chunk_index;",
                (doc_id,),
            )
            return [row[0] for row in cur.fetchall()]


def load_many(doc_ids: list[int]) -> list[str]:
    """Return all chunks across multiple documents."""
    if not doc_ids:
        return []

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT chunk_text
                FROM   chunks
                WHERE  document_id = ANY(%s)
                ORDER  BY document_id, chunk_index;
                """,
                (doc_ids,),
            )
            return [row[0] for row in cur.fetchall()]