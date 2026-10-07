"""
FastAPI application entry point.

Run with:
    uvicorn backend.main:app --reload --port 8000

(run from the project root so the `backend` package resolves correctly)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.models.database import init_db
from backend.routes import agent, chat, documents
from backend.utils.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Autonomous Academic Research Worker",
    description="A document-grounded RAG assistant with a bounded autonomous research worker.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(agent.router)
