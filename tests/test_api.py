"""End-to-end API tests using FastAPI's TestClient (mocks embeddings + LLM)."""

import io
import random

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import embedding_service, llm_service

client = TestClient(app)


def _fake_embedding(text: str) -> list:
    random.seed(abs(hash(text)) % (2**32))
    return [random.random() for _ in range(384)]


@pytest.fixture(autouse=True)
def mock_embeddings(monkeypatch):
    monkeypatch.setattr(
        embedding_service, "embed_texts", lambda texts: [_fake_embedding(t) for t in texts]
    )
    monkeypatch.setattr(embedding_service, "embed_query", lambda q: _fake_embedding(q))


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_list_and_delete_document(sample_pdf_bytes):
    # Upload
    files = {"files": ("api_test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 200
    documents = response.json()["documents"]
    assert any(d["filename"] == "api_test.pdf" for d in documents)
    doc_id = next(d["id"] for d in documents if d["filename"] == "api_test.pdf")

    # List
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert any(d["id"] == doc_id for d in response.json()["documents"])

    # Delete
    response = client.delete(f"/api/documents/{doc_id}")
    assert response.status_code == 200
    assert response.json() == {"id": doc_id, "deleted": True}

    # Deleting again should 404
    response = client.delete(f"/api/documents/{doc_id}")
    assert response.status_code == 404


def test_upload_rejects_non_pdf():
    files = {"files": ("notes.txt", io.BytesIO(b"just text"), "text/plain")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 400


def test_ask_question_returns_answer_and_sources(sample_pdf_bytes, monkeypatch):
    monkeypatch.setattr(
        llm_service, "generate_answer", lambda prompt: "Photosynthesis converts light into energy."
    )

    files = {"files": ("chat_test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")}
    upload_response = client.post("/api/documents/upload", files=files)
    doc_id = next(
        d["id"] for d in upload_response.json()["documents"] if d["filename"] == "chat_test.pdf"
    )

    try:
        response = client.post("/api/chat/ask", json={"question": "What is photosynthesis?"})
        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == "Photosynthesis converts light into energy."
        assert body["grounded"] is True
        assert len(body["sources"]) > 0
        assert body["sources"][0]["filename"] == "chat_test.pdf"
    finally:
        # Clean up so this document doesn't leak into other tests in this module.
        client.delete(f"/api/documents/{doc_id}")


def test_ask_question_with_no_documents_is_not_grounded():
    # Runs against whatever is left in the (session-scoped) vector store.
    # Every other test in this module cleans up the documents it creates,
    # so at this point the store should be empty and retrieval returns
    # nothing, regardless of the question asked.
    response = client.post("/api/chat/ask", json={"question": "Anything at all?"})
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
