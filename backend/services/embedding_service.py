"""
Lightweight local TF-IDF embeddings.

This replaces Sentence Transformers so the backend does not require
PyTorch/CUDA and can run within a small Render instance.
"""

from pathlib import Path
from threading import Lock
from typing import List

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

_VECTOR_SIZE = 768
_vectorizer = None
_lock = Lock()

_VECTOR_FILE = Path(settings.CHROMA_DIR).parent / "tfidf_vectorizer.joblib"

def delete_vectorizer() -> None:
    """Delete the persisted TF-IDF vectorizer."""
    global _vectorizer

    with _lock:
        _vectorizer = None

        if _VECTOR_FILE.exists():
            _VECTOR_FILE.unlink()

        logger.info("Deleted persisted TF-IDF vectorizer")


def _get_vectorizer() -> TfidfVectorizer:
    """Load the persisted vectorizer if available."""
    global _vectorizer

    with _lock:
        if _vectorizer is not None:
            return _vectorizer

        if _VECTOR_FILE.exists():
            _vectorizer = joblib.load(_VECTOR_FILE)
            logger.info("Loaded TF-IDF vectorizer from %s", _VECTOR_FILE)
            return _vectorizer

        raise RuntimeError(
            "TF-IDF vectorizer is not initialized. "
            "Index documents before performing retrieval."
        )


def fit_vectorizer(texts: List[str]) -> None:
    """Fit the vectorizer on the document chunks and persist it."""
    global _vectorizer

    if not texts:
        raise ValueError("Cannot fit the vectorizer on empty text.")

    with _lock:
        vectorizer = TfidfVectorizer(
            max_features=_VECTOR_SIZE,
            ngram_range=(1, 2),
            sublinear_tf=True,
            norm="l2",
        )

        vectorizer.fit(texts)

        _VECTOR_FILE.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(vectorizer, _VECTOR_FILE)

        _vectorizer = vectorizer

        logger.info(
            "Fitted TF-IDF vectorizer with %d features",
            len(vectorizer.vocabulary_),
        )


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Convert text strings into TF-IDF vectors."""
    if not texts:
        return []

    vectorizer = _get_vectorizer()
    vectors = vectorizer.transform(texts)

    # Chroma accepts dense lists of floats.
    return vectors.toarray().astype(np.float32).tolist()


def embed_query(query: str) -> List[float]:
    """Convert a query into the same vector space as indexed documents."""
    return embed_texts([query])[0]