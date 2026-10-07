"""Pydantic request/response models shared across the API routes."""

from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentOut(BaseModel):
    id: str
    filename: str
    num_pages: int
    num_chunks: int
    uploaded_at: str
    status: str


class UploadResponse(BaseModel):
    documents: List[DocumentOut]


class DeleteResponse(BaseModel):
    id: str
    deleted: bool


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The user's natural-language question")
    top_k: Optional[int] = Field(None, description="Override the default number of chunks to retrieve")
    document_ids: Optional[List[str]] = Field(
        None, description="Restrict retrieval to these document IDs. Omit to search all documents."
    )


class SourceChunk(BaseModel):
    document_id: str
    filename: str
    page_number: int
    chunk_id: str
    text: str
    similarity_score: float


class AskResponse(BaseModel):
    answer: str
    sources: List[SourceChunk]
    grounded: bool = Field(
        ..., description="False when no relevant context was found and the model declined to answer"
    )
