# db/documents.py — CRUD for the `documents` table

import hashlib

import psycopg2

from db.connection import get_connection


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def exists(file_bytes: bytes) -> bool:
    """Return True if this exact file (by SHA-256) is already stored."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM documents WHERE file_hash = %s LIMIT 1;",
                (sha256(file_bytes),),
            )
            return cur.fetchone() is not None


def save(filename: str, file_bytes: bytes, raw_text: str) -> int:
    """
    Insert a document row and return its id.
    If the same file (same SHA-256) already exists, return the existing id.
    """
    file_hash = sha256(file_bytes)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO documents (filename, file_hash, raw_text)
                VALUES (%s, %s, %s)
                ON CONFLICT (file_hash) DO NOTHING
                RETURNING id;
                """,
                (filename, file_hash, raw_text),
            )
            row = cur.fetchone()
            if row is None:  # conflict branch — fetch existing id
                cur.execute(
                    "SELECT id FROM documents WHERE file_hash = %s;",
                    (file_hash,),
                )
                row = cur.fetchone()
        conn.commit()

    return row[0]


def list_all() -> list[dict]:
    """Return all documents ordered by insertion time (newest first)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, filename, created_at FROM documents ORDER BY created_at DESC;"
            )
            cols = [desc[0] for desc in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def get_text(doc_id: int) -> str | None:
    """Fetch the raw_text of a specific document, or None if not found."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT raw_text FROM documents WHERE id = %s;", (doc_id,))
            row = cur.fetchone()
            return row[0] if row else None


def delete(doc_id: int) -> None:
    """Delete a document and cascade-delete its chunks."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM documents WHERE id = %s;", (doc_id,))
        conn.commit()