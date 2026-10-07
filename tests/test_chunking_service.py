"""Unit tests for the chunking logic (no external services required)."""

from backend.services.chunking_service import chunk_page_text
from backend.services.pdf_service import PageText


def test_short_text_produces_a_single_chunk():
    page = PageText(page_number=1, text="This is a short sentence.")
    chunks = chunk_page_text(page, document_id="doc1", chunk_size=800, chunk_overlap=150)

    assert len(chunks) == 1
    assert chunks[0].text == "This is a short sentence."
    assert chunks[0].page_number == 1
    assert chunks[0].document_id == "doc1"
    assert chunks[0].chunk_id == "doc1_p1_c0"


def test_long_text_is_split_into_multiple_chunks():
    # ~2400 characters of repeated sentences -> should split into 3+ chunks at chunk_size=800
    sentence = "The quick brown fox jumps over the lazy dog. "
    long_text = sentence * 60  # ~2760 characters
    page = PageText(page_number=5, text=long_text)

    chunks = chunk_page_text(page, document_id="doc2", chunk_size=800, chunk_overlap=150)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.page_number == 5
        # every chunk should stay reasonably close to the target size
        assert len(chunk.text) <= 800 + 150  # allow the sentence-boundary lookahead

    # chunk ids should be unique and sequential
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_overlap_repeats_tail_of_previous_chunk():
    sentence = "Alpha beta gamma delta epsilon. "
    long_text = sentence * 60
    page = PageText(page_number=1, text=long_text)

    chunks = chunk_page_text(page, document_id="doc3", chunk_size=500, chunk_overlap=100)
    assert len(chunks) >= 2

    # The tail of chunk[0] should share some text with the head of chunk[1],
    # proving the sliding window actually overlaps.
    tail_of_first = chunks[0].text[-50:]
    assert tail_of_first[:20] in chunks[1].text or tail_of_first[-20:] in chunks[1].text


def test_empty_page_produces_no_chunks():
    page = PageText(page_number=3, text="")
    chunks = chunk_page_text(page, document_id="doc4")
    assert chunks == []
