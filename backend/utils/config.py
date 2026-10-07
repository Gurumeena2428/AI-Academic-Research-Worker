"""Application configuration loaded from the project-root .env file."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    # LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    # Optional OpenAI compatibility
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Retrieval
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "150"))
    TOP_K: int = int(os.getenv("TOP_K", "4"))
    MIN_RETRIEVAL_SIMILARITY: float = float(os.getenv("MIN_RETRIEVAL_SIMILARITY", "0.20"))

    # Storage
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    CHROMA_DIR: Path = DATA_DIR / "chroma"
    SQLITE_PATH: Path = DATA_DIR / "app.db"
    CHROMA_COLLECTION_NAME: str = os.getenv(
        "CHROMA_COLLECTION_NAME", "academic_documents"
    )

    # Server
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
        if origin.strip()
    ]


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
