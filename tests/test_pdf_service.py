"""Tests for PDF text extraction."""

from pathlib import Path

from backend.services.pdf_service import extract_pages


def test_extract_pages_preserves_page_numbers_and_text(tmp_path, sample_pdf_bytes):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(sample_pdf_bytes)

    pages = extract_pages(pdf_path)

    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert pages[1].page_number == 2
    assert "Photosynthesis" in pages[0].text
    assert "TCP" in pages[1].text


def test_extract_pages_on_blank_document(tmp_path):
    import fitz

    doc = fitz.open()
    doc.new_page()  # a single blank page with no text
    blank_path = tmp_path / "blank.pdf"
    doc.save(blank_path)
    doc.close()

    pages = extract_pages(blank_path)
    assert len(pages) == 1
    assert pages[0].text == ""
