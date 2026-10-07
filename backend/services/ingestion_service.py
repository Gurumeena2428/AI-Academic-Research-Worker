"""PDF ingestion: extraction -> chunking -> embeddings -> storage."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

from backend.models import database
from backend.services import embedding_service, pdf_service, vector_store_service
from backend.services.chunking_service import chunk_document
from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _safe_filename(filename: str) -> str:
    """Keep only a safe local filename while preserving its extension."""
    original = Path(filename or "document.pdf").name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", original).strip("._")
    if not cleaned.lower().endswith(".pdf"):
        cleaned += ".pdf"
    return cleaned or "document.pdf"


def ingest_pdf(filename: str, file_bytes: bytes) -> dict:
    """Persist a PDF, index it, and return its SQLite metadata row."""
    if not file_bytes:
        raise ValueError("The uploaded PDF is empty.")

    safe_name = _safe_filename(filename)
    storage_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    stored_path = settings.UPLOAD_DIR / storage_name
    stored_path.write_bytes(file_bytes)

    pages = pdf_service.extract_pages(stored_path)
    num_pages = len(pages)
    doc_id = database.create_document(
        filename=safe_name,
        stored_path=str(stored_path),
        num_pages=num_pages,
    )

    try:
        chunks = chunk_document(pages, document_id=doc_id)
        if chunks:
            texts = [chunk.text for chunk in chunks]
            vectors = embedding_service.embed_texts(texts)
            ids = [chunk.chunk_id for chunk in chunks]
            metadatas = [
                {
                    "document_id": chunk.document_id,
                    "filename": safe_name,
                    "page_number": chunk.page_number,
                    "chunk_id": chunk.chunk_id,
                }
                for chunk in chunks
            ]
            vector_store_service.add_chunks(
                ids=ids,
                embeddings=vectors,
                documents=texts,
                metadatas=metadatas,
            )

        database.mark_document_ready(doc_id, num_chunks=len(chunks))
        logger.info(
            "Ingested '%s' -> %d pages, %d chunks",
            safe_name,
            num_pages,
            len(chunks),
        )
    except Exception:
        database.mark_document_failed(doc_id)
        if stored_path.exists():
            stored_path.unlink()
        logger.exception("Failed to ingest %s", safe_name)
        raise

    row = database.get_document(doc_id)
    return dict(row)


def delete_document(doc_id: str) -> bool:
    """Delete a document's vector chunks, file, and metadata row."""
    row = database.get_document(doc_id)
    if row is None:
        return False

    vector_store_service.delete_document_chunks(doc_id)

    stored_path = Path(row["stored_path"])
    if stored_path.exists():
        stored_path.unlink()

    database.delete_document(doc_id)
    return True
