"""
ChromaDB wrapper -- the vector database layer.

WHY CHROMADB WAS SELECTED
---------------------------
- It runs embedded/in-process (like SQLite for vectors) -- no separate
  server to install or manage, which keeps this a "medium level" project
  instead of turning into infrastructure work.
- It persists to local disk (`data/chroma/`), so the index survives a
  server restart.
- It has a simple Python API purpose-built for exactly this RAG use case:
  add(embeddings, documents, metadatas, ids) and query(...).

WHAT IS STORED INSIDE IT
---------------------------
For every chunk we store four aligned pieces of data under the same id:
  1. The embedding vector (384 floats) -- used for similarity search.
  2. The original chunk text ("document") -- so we can hand it to the
     LLM as context and show it to the user as a citation.
  3. Metadata -- document_id, filename, page_number, chunk_id -- used to
     build the "Source: file.pdf, Page 12" citation and to support
     deleting/filtering by document.
  4. The id itself (the chunk_id), so a chunk can be looked up or
     deleted directly.

HOW SIMILARITY SEARCH WORKS
------------------------------
When we call `collection.query(query_embeddings=[...], n_results=k)`,
Chroma computes the distance between the query vector and every stored
vector (using cosine distance, matching the normalized embeddings we
generate) and returns the k closest matches, sorted nearest-first. This
is the "R" (Retrieval) step of RAG.
"""

import os
from typing import Dict, List, Optional

# Must be set before chromadb is imported for it to fully suppress the
# (harmless, but noisy) anonymous telemetry it tries to send on startup.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

_client = None
_collection = None


def get_collection():
    """Lazily create a persistent Chroma client + collection (singleton)."""
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DIR),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "Connected to Chroma collection '%s' (%d chunks currently stored)",
            settings.CHROMA_COLLECTION_NAME,
            _collection.count(),
        )
    return _collection


def add_chunks(
    ids: List[str],
    embeddings: List[List[float]],
    documents: List[str],
    metadatas: List[Dict],
) -> None:
    collection = get_collection()
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    logger.info("Added %d chunks to the vector store", len(ids))


def query(
    query_embedding: List[float],
    top_k: int,
    document_ids: Optional[List[str]] = None,
) -> Dict:
    """Return the top_k most similar chunks to the given query embedding.

    If `document_ids` is provided, restrict the search to chunks
    belonging to those documents (lets the UI support "ask only about
    this file" in the future; currently we default to searching
    everything the user has uploaded).
    """
    collection = get_collection()
    where_filter = {"document_id": {"$in": document_ids}} if document_ids else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
    )
    return results

def reset_collection() -> None:
    """Delete and recreate the entire vector collection."""
    global _collection

    if _client is None:
        get_collection()

    _client.delete_collection(name=settings.CHROMA_COLLECTION_NAME)
    _collection = _client.create_collection(
        name=settings.CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    logger.info("Reset Chroma collection '%s'", settings.CHROMA_COLLECTION_NAME)


def delete_document_chunks(document_id: str) -> None:
    """Delete every chunk belonging to a document (used when the user deletes a PDF)."""
    collection = get_collection()
    collection.delete(where={"document_id": document_id})
    logger.info("Deleted all chunks for document %s", document_id)


def count_chunks() -> int:
    return get_collection().count()
