"""Document management endpoints: upload, list, delete."""

from typing import List

from fastapi import APIRouter, HTTPException, UploadFile

from backend.models import database
from backend.models.schemas import DeleteResponse, DocumentOut, UploadResponse
from backend.services import ingestion_service
from backend.utils.logger import get_logger

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = get_logger(__name__)

ALLOWED_CONTENT_TYPES = {"application/pdf"}


@router.post("/upload", response_model=UploadResponse)
async def upload_documents(files: List[UploadFile]):
    """Accept one or more PDF files, extract/chunk/embed each, and return the updated list."""
    for f in files:
        if f.content_type not in ALLOWED_CONTENT_TYPES and not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"'{f.filename}' is not a PDF file.")

    for f in files:
        file_bytes = await f.read()
        try:
            ingestion_service.ingest_pdf(filename=f.filename, file_bytes=file_bytes)
        except Exception as exc:  # noqa: BLE001 - surface a clean error to the client
            logger.exception("Upload failed for %s", f.filename)
            raise HTTPException(status_code=500, detail=f"Failed to process '{f.filename}': {exc}") from exc

    return UploadResponse(documents=_serialize_all())


@router.get("", response_model=UploadResponse)
def list_documents():
    return UploadResponse(documents=_serialize_all())


@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(document_id: str):
    deleted = ingestion_service.delete_document(document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return DeleteResponse(id=document_id, deleted=True)


def _serialize_all() -> List[DocumentOut]:
    rows = database.list_documents()
    return [
        DocumentOut(
            id=row["id"],
            filename=row["filename"],
            num_pages=row["num_pages"],
            num_chunks=row["num_chunks"],
            uploaded_at=row["uploaded_at"],
            status=row["status"],
        )
        for row in rows
    ]
