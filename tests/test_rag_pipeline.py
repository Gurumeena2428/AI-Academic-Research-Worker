"""
Integration tests for the RAG pipeline: ingestion -> retrieval -> prompt
construction -> (mocked) generation.

The embedding model and the LLM API are mocked here on purpose:
  - Embeddings: downloading/running the real sentence-transformers model
    in CI or in a network-restricted environment is slow/unavailable, and
    we're testing our *pipeline wiring*, not the pretrained model itself.
  - LLM: we don't want tests to require a real API key or make network
    calls, and we want deterministic assertions.

test_chunking_service.py and test_pdf_service.py already cover the parts
of the pipeline that don't need mocking.
"""

import random

import pytest

from backend.rag import pipeline
from backend.services import embedding_service, ingestion_service, llm_service


def _fake_embedding(text: str) -> list:
    """Deterministic pseudo-embedding: same text -> same vector, so we
    can still meaningfully test retrieval without a real model."""
    random.seed(abs(hash(text)) % (2**32))
    return [random.random() for _ in range(384)]


@pytest.fixture(autouse=True)
def mock_embeddings(monkeypatch):
    monkeypatch.setattr(
        embedding_service, "embed_texts", lambda texts: [_fake_embedding(t) for t in texts]
    )
    monkeypatch.setattr(embedding_service, "embed_query", lambda q: _fake_embedding(q))


@pytest.fixture
def ingested_doc(sample_pdf_bytes):
    doc = ingestion_service.ingest_pdf("pipeline_test.pdf", sample_pdf_bytes)
    yield doc
    ingestion_service.delete_document(doc["id"])


def test_ingestion_creates_expected_chunks(ingested_doc):
    assert ingested_doc["status"] == "ready"
    assert ingested_doc["num_pages"] == 2
    assert ingested_doc["num_chunks"] == 2  # one short paragraph per page


def test_retrieve_context_returns_chunks_with_metadata(ingested_doc):
    chunks = pipeline.retrieve_context("What is photosynthesis?")

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.filename == "pipeline_test.pdf"
        assert chunk.page_number in (1, 2)
        assert 0.0 <= chunk.similarity_score <= 1.0


def test_build_prompt_includes_context_and_question(ingested_doc):
    chunks = pipeline.retrieve_context("What is photosynthesis?")
    prompt = pipeline.build_prompt("What is photosynthesis?", chunks)

    assert "QUESTION:\nWhat is photosynthesis?" in prompt
    assert "using only the context provided" in prompt.lower()
    assert any(c.text in prompt for c in chunks)


def test_build_prompt_with_no_context_still_produces_valid_prompt():
    prompt = pipeline.build_prompt("Unanswerable question", [])
    assert "No relevant context" in prompt


def test_answer_question_with_no_documents_returns_not_found(monkeypatch):
    # No documents ingested in this test -> retrieval should come back empty
    # (the isolated_data_dir fixture guarantees a clean vector store per test
    # session; this test runs before any doc is added within its own scope).
    monkeypatch.setattr(pipeline, "retrieve_context", lambda *a, **k: [])
    result = pipeline.answer_question("Anything?")

    assert result.grounded is False
    assert "not found in the uploaded documents" in result.answer.lower()
    assert result.sources == []


def test_answer_question_end_to_end_with_mocked_llm(ingested_doc, monkeypatch):
    monkeypatch.setattr(
        llm_service, "generate_answer", lambda prompt: "Photosynthesis converts light into energy."
    )

    result = pipeline.answer_question("What is photosynthesis?")

    assert result.grounded is True
    assert result.answer == "Photosynthesis converts light into energy."
    assert len(result.sources) > 0


def test_hallucination_guard_marks_response_as_not_grounded(ingested_doc, monkeypatch):
    monkeypatch.setattr(
        llm_service,
        "generate_answer",
        lambda prompt: "The information was not found in the uploaded documents.",
    )

    result = pipeline.answer_question("What is quantum entanglement?")
    assert result.grounded is False
