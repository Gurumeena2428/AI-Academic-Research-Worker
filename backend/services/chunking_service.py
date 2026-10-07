"""
Text chunking.

WHY CHUNKING IS REQUIRED
-------------------------
An LLM (and the embedding model) can only "pay attention to" a limited
amount of text at once, and retrieval works best when each stored piece
of text is about ONE idea. If we embedded an entire 20-page PDF as a
single vector, that vector would be a blurry average of everything in
the document -- a question about "page 12" would retrieve the same vector
as a question about "page 2", because both live inside the same chunk.
Splitting the document into small, semantically-focused pieces lets the
vector database tell them apart.

HOW CHUNK SIZE AFFECTS RETRIEVAL
---------------------------------
- Too small (e.g. 100 characters): chunks lose context. A sentence
  fragment like "This is because it increases entropy." is meaningless
  on its own, so its embedding won't be a good semantic match for the
  original question, and the LLM won't have enough context to answer
  even if the chunk IS retrieved.
- Too large (e.g. 4000 characters): the chunk starts mixing multiple
  topics again, diluting the embedding (same problem as not chunking at
  all) and wasting LLM context window on irrelevant text.

We use CHUNK_SIZE = 800 characters (~150-200 words), which is roughly
one to two paragraphs of lecture notes -- big enough to contain a full
idea, small enough to stay focused.

WHY OVERLAP IS USEFUL
----------------------
If we chunk with hard, non-overlapping boundaries, a sentence that
straddles a chunk boundary gets split in half, and neither half makes
sense on its own or embeds well. A small overlap (CHUNK_OVERLAP = 150
characters) means the end of chunk N is repeated at the start of chunk
N+1, so an idea near a boundary still appears intact in at least one
chunk.

This implementation is a simple, transparent character-based sliding
window (rather than importing LangChain's splitter) so the logic is
visible and easy to explain in an interview.
"""

import re
from dataclasses import dataclass
from typing import List

from backend.services.pdf_service import PageText
from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Chunk:
    chunk_id: str          # e.g. "<document_id>_p3_c1"
    document_id: str
    page_number: int
    text: str


def _split_into_sentences(text: str) -> List[str]:
    """Very small sentence splitter (no external NLP dependency needed).

    Splits on '.', '?', '!' followed by whitespace, while keeping the
    punctuation attached to the sentence. This is good enough for
    lecture-note-style text; it doesn't need to be perfect because
    chunk boundaries just need to be "reasonable", not linguistically
    exact.
    """
    sentences = re.split(r"(?<=[.?!])\s+", text.strip())
    return [s for s in sentences if s]


def chunk_page_text(
    page: PageText,
    document_id: str,
    chunk_size: int = None,
    chunk_overlap: int = None,
) -> List[Chunk]:
    """Chunk a single page's text using a sliding window over characters.

    We chunk per-page (rather than concatenating the whole document
    first) specifically so every chunk can carry an accurate page number
    for citations -- this is what lets the UI show "Biology_Notes.pdf —
    Page 12" instead of just a filename.
    """
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    text = page.text
    if not text:
        return []

    chunks: List[Chunk] = []
    start = 0
    index = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        # Try not to cut a sentence mid-way: extend `end` to the nearest
        # sentence boundary within a small lookahead window, if one exists.
        window_end = min(end + 100, text_length)
        lookahead = text[end:window_end]
        boundary_match = re.search(r"[.?!]\s", lookahead)
        if boundary_match:
            end = end + boundary_match.end()

        chunk_text = text[start:end].strip()
        if chunk_text:
            chunk_id = f"{document_id}_p{page.page_number}_c{index}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    page_number=page.page_number,
                    text=chunk_text,
                )
            )
            index += 1

        if end >= text_length:
            break

        # Slide the window forward, stepping back by `chunk_overlap`
        # characters so the next chunk repeats the tail of this one.
        start = max(end - chunk_overlap, start + 1)

    return chunks


def chunk_document(pages: List[PageText], document_id: str) -> List[Chunk]:
    """Chunk every page of a document and return the flat list of chunks."""
    all_chunks: List[Chunk] = []
    for page in pages:
        all_chunks.extend(chunk_page_text(page, document_id))

    logger.info(
        "Chunked document %s into %d chunks (chunk_size=%d, overlap=%d)",
        document_id,
        len(all_chunks),
        settings.CHUNK_SIZE,
        settings.CHUNK_OVERLAP,
    )
    return all_chunks
