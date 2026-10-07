"""
SQLite persistence for document metadata.

WHY a relational table in addition to ChromaDB?
ChromaDB is good at "find me the chunks closest to this vector" but it is
not a great place to answer "what documents has this user uploaded?" or to
enforce simple relational rules (e.g. delete all chunks belonging to one
file). So we keep two stores with two different jobs:

  - SQLite (`documents` table): one row per uploaded PDF. Source of truth
    for the sidebar's document list and for cascading deletes.
  - ChromaDB (`rag/vector_store.py`): one entry per chunk, used only for
    similarity search.

This mirrors how production RAG systems are usually built: a normal
database for bookkeeping, a vector database purely for retrieval.
"""

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional

from backend.utils.config import settings


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they don't already exist. Called once on startup."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id            TEXT PRIMARY KEY,
                filename      TEXT NOT NULL,
                stored_path   TEXT NOT NULL,
                num_pages     INTEGER NOT NULL,
                num_chunks    INTEGER NOT NULL DEFAULT 0,
                uploaded_at   TEXT NOT NULL,
                status        TEXT NOT NULL DEFAULT 'processing'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_history (
                id            TEXT PRIMARY KEY,
                question      TEXT NOT NULL,
                answer        TEXT NOT NULL,
                sources_json  TEXT NOT NULL,
                created_at    TEXT NOT NULL
            )
            """
        )


# ---------------------------------------------------------------------
# Document CRUD
# ---------------------------------------------------------------------

def create_document(filename: str, stored_path: str, num_pages: int) -> str:
    doc_id = str(uuid.uuid4())
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO documents (id, filename, stored_path, num_pages, num_chunks, uploaded_at, status)
            VALUES (?, ?, ?, ?, 0, ?, 'processing')
            """,
            (doc_id, filename, stored_path, num_pages, datetime.now(timezone.utc).isoformat()),
        )
    return doc_id


def mark_document_ready(doc_id: str, num_chunks: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE documents SET num_chunks = ?, status = 'ready' WHERE id = ?",
            (num_chunks, doc_id),
        )


def mark_document_failed(doc_id: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE documents SET status = 'failed' WHERE id = ?", (doc_id,))


def list_documents() -> list[sqlite3.Row]:
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM documents ORDER BY uploaded_at DESC")
        return cur.fetchall()


def get_document(doc_id: str) -> Optional[sqlite3.Row]:
    with get_connection() as conn:
        cur = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        return cur.fetchone()


def delete_document(doc_id: str) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))


# ---------------------------------------------------------------------
# Chat history (used to show a persistent chat log; optional feature)
# ---------------------------------------------------------------------

def save_chat_turn(question: str, answer: str, sources_json: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_history (id, question, answer, sources_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), question, answer, sources_json, datetime.now(timezone.utc).isoformat()),
        )


def list_chat_history(limit: int = 50) -> list[sqlite3.Row]:
    with get_connection() as conn:
        cur = conn.execute(
            "SELECT * FROM chat_history ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return cur.fetchall()
