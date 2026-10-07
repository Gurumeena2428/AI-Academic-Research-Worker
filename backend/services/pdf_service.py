"""
PDF text extraction using PyMuPDF (imported as `fitz`).

PyMuPDF was chosen over alternatives (pdfminer, PyPDF2) because it:
  - is fast (C++ under the hood),
  - gives per-page text directly, which we need to preserve page numbers
    for citations, and
  - handles most "real world" academic PDFs (multi-column notes,
    scanned-but-text-layered slides, etc.) reasonably well without extra
    configuration.

We deliberately keep this file dumb: its only job is "PDF bytes on disk"
-> "list of (page_number, text)". All chunking/embedding logic lives
elsewhere so each stage of the pipeline can be tested independently.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List

import fitz  # PyMuPDF

from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PageText:
    page_number: int  # 1-indexed, matches what a human would read on the page
    text: str


def extract_pages(pdf_path: Path) -> List[PageText]:
    """Read a PDF file from disk and return cleaned text for every page.

    Pages with no extractable text (e.g. a blank page, or a page that is
    purely an image with no text layer) are still returned, with an empty
    string, so page numbering for later pages stays correct.
    """
    pages: List[PageText] = []

    with fitz.open(pdf_path) as doc:
        for index, page in enumerate(doc):
            raw_text = page.get_text("text")
            cleaned = _clean_text(raw_text)
            pages.append(PageText(page_number=index + 1, text=cleaned))

    logger.info("Extracted %d pages from %s", len(pages), pdf_path.name)
    return pages


def _clean_text(text: str) -> str:
    """Light normalization: collapse excessive whitespace/newlines.

    We don't do anything aggressive here (no stemming, no lowercasing)
    because the embedding model works on natural language and benefits
    from the original casing/punctuation.
    """
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]  # drop empty lines
    return "\n".join(lines)
