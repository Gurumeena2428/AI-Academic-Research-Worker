"""Chat / question-answering endpoint -- this is where the RAG pipeline is invoked."""

import json

from fastapi import APIRouter, HTTPException

from backend.models import database
from backend.models.schemas import AskRequest, AskResponse, SourceChunk
from backend.rag import pipeline
from backend.services.llm_service import LLMConfigurationError
from backend.utils.logger import get_logger

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = get_logger(__name__)


@router.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    try:
        result = pipeline.answer_question(
            question=request.question,
            top_k=request.top_k,
            document_ids=request.document_ids,
        )
    except LLMConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to answer question")
        raise HTTPException(status_code=500, detail=f"Failed to generate an answer: {exc}") from exc

    sources = [
        SourceChunk(
            document_id=c.document_id,
            filename=c.filename,
            page_number=c.page_number,
            chunk_id=c.chunk_id,
            text=c.text,
            similarity_score=c.similarity_score,
        )
        for c in result.sources
    ]

    database.save_chat_turn(
        question=request.question,
        answer=result.answer,
        sources_json=json.dumps([s.model_dump() for s in sources]),
    )

    return AskResponse(answer=result.answer, sources=sources, grounded=result.grounded)


@router.get("/history")
def get_history():
    rows = database.list_chat_history()
    return [
        {
            "id": row["id"],
            "question": row["question"],
            "answer": row["answer"],
            "sources": json.loads(row["sources_json"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]
