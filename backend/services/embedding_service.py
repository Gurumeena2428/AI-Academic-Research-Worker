"""
Embeddings via Sentence Transformers.

WHAT EMBEDDINGS ARE
--------------------
An embedding is a fixed-length list of numbers (a vector) that represents
the *meaning* of a piece of text. Instead of comparing text
character-by-character (like Ctrl+F), we compare these vectors
mathematically. Texts with similar meaning end up as vectors that point
in a similar direction in that high-dimensional space, even if they don't
share any exact words.

WHY EMBEDDINGS ARE REQUIRED
-----------------------------
The user's question and the relevant document chunk are rarely worded
identically. E.g. a question "How does the immune system fight viruses?"
should retrieve a chunk that talks about "antibodies neutralizing
pathogens" -- there's barely any word overlap, but the *meaning* overlaps
heavily. Keyword search (e.g. SQL LIKE, or an inverted index) would miss
this; embeddings + similarity search catch it because they compare
meaning, not exact words.

HOW TEXT BECOMES A VECTOR
----------------------------
We use the pretrained model `all-MiniLM-L6-v2` from the
`sentence-transformers` library. It's a small transformer (based on
distilled BERT) that has already been trained on millions of
sentence-pairs to place semantically similar sentences near each other
in a 384-dimensional vector space. We simply feed our chunk text through
this frozen, pretrained model -- no training is done in this project.

WHAT SEMANTIC SIMILARITY MEANS
---------------------------------
Once text is represented as vectors, "similarity" can be computed
mathematically -- we use cosine similarity, which measures the angle
between two vectors (1.0 = pointing in exactly the same direction /
same meaning, 0 = unrelated, -1 = opposite meaning). ChromaDB does this
comparison for us internally when we query it (see vector_store_service.py).
"""

from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the model once and reuse it (loading takes a few seconds)."""
    logger.info("Loading embedding model: %s", settings.EMBEDDING_MODEL)
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Convert a batch of text strings into embedding vectors."""
    model = get_embedding_model()
    # normalize_embeddings=True makes cosine similarity equivalent to a
    # simple dot product, which is what ChromaDB uses under the hood.
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query(query: str) -> List[float]:
    """Convenience wrapper for embedding a single question."""
    return embed_texts([query])[0]
