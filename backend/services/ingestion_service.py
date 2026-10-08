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


def _build_corpus_index() -> None:
    """Rebuild TF-IDF and Chroma from every uploaded document."""
    documents = database.list_documents()

    corpus = []

    for document in documents:
        stored_path = Path(document["stored_path"])

        if not stored_path.exists():
            logger.warning(
                "Skipping missing document during reindex: %s",
                document["filename"],
            )
            continue

        pages = pdf_service.extract_pages(stored_path)
        chunks = chunk_document(
            pages,
            document_id=document["id"],
        )

        corpus.append(
            {
                "document": document,
                "chunks": chunks,
            }
        )

    all_chunks = [
        chunk
        for item in corpus
        for chunk in item["chunks"]
    ]

    if not all_chunks:
        vector_store_service.reset_collection()
        embedding_service.delete_vectorizer()
        logger.info("Corpus is empty; vector store and vectorizer reset.")
        return

    texts = [chunk.text for chunk in all_chunks]

    # Fit ONE vocabulary across the entire uploaded-document corpus.
    embedding_service.fit_vectorizer(texts)
    vectors = embedding_service.embed_texts(texts)

    vector_store_service.reset_collection()

    start = 0

    for item in corpus:
        document = item["document"]
        chunks = item["chunks"]

        if not chunks:
            continue

        end = start + len(chunks)

        chunk_vectors = vectors[start:end]
        chunk_texts = texts[start:end]

        ids = [chunk.chunk_id for chunk in chunks]

        metadatas = [
            {
                "document_id": chunk.document_id,
                "filename": document["filename"],
                "page_number": chunk.page_number,
                "chunk_id": chunk.chunk_id,
            }
            for chunk in chunks
        ]

        vector_store_service.add_chunks(
            ids=ids,
            embeddings=chunk_vectors,
            documents=chunk_texts,
            metadatas=metadatas,
        )

        database.mark_document_ready(
            document["id"],
            num_chunks=len(chunks),
        )

        start = end

    logger.info(
        "Rebuilt corpus index: %d documents, %d chunks, %d features",
        len(corpus),
        len(all_chunks),
        len(vectors[0]),
    )


def ingest_pdf(filename: str, file_bytes: bytes) -> dict:
    """Persist a PDF, rebuild the corpus index, and return its metadata row."""
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
        _build_corpus_index()

        row = database.get_document(doc_id)

        if row is None:
            raise RuntimeError(
                f"Document {doc_id} disappeared during indexing."
            )

        logger.info(
            "Ingested '%s' -> %d pages, %d chunks",
            safe_name,
            num_pages,
            row["num_chunks"],
        )

        return dict(row)

    except Exception:
        database.mark_document_failed(doc_id)

        if stored_path.exists():
            stored_path.unlink()

        logger.exception("Failed to ingest %s", safe_name)
        raise


def delete_document(doc_id: str) -> bool:
    """Delete a document and rebuild the remaining corpus index."""
    row = database.get_document(doc_id)

    if row is None:
        return False

    stored_path = Path(row["stored_path"])

    if stored_path.exists():
        stored_path.unlink()

    database.delete_document(doc_id)

    _build_corpus_index()

    return True