# db/connection.py — connection factory and schema bootstrap

import os

import psycopg2
from psycopg2.extras import RealDictCursor


def get_connection() -> psycopg2.extensions.connection:
    """Return a new psycopg2 connection using environment variables."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "pdf_chatbot"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )


_DDL = """
CREATE TABLE IF NOT EXISTS documents (
    id          SERIAL      PRIMARY KEY,
    filename    TEXT        NOT NULL,
    file_hash   CHAR(64)    NOT NULL,
    raw_text    TEXT        NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (file_hash)
);

CREATE TABLE IF NOT EXISTS chunks (
    id          SERIAL  PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);

CREATE TABLE IF NOT EXISTS faiss_index (
    id           SERIAL      PRIMARY KEY,
    index_name   TEXT        NOT NULL UNIQUE,
    index_blob   BYTEA       NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def init_db() -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_DDL)
        conn.commit()