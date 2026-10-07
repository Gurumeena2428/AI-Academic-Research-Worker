"""Shared pytest fixtures.

We point the app at a throwaway data directory for the duration of the
test session, so tests never touch (or get confused by) whatever is in
the real `data/` folder, and can be re-run repeatedly.
"""

import shutil
import sys
from pathlib import Path

import pytest

# Make the project root importable as `backend.*` when running `pytest`
# from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.utils.config import settings  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def isolated_data_dir(tmp_path_factory):
    test_dir = tmp_path_factory.mktemp("rag_test_data")

    settings.DATA_DIR = test_dir
    settings.UPLOAD_DIR = test_dir / "uploads"
    settings.CHROMA_DIR = test_dir / "chroma"
    settings.SQLITE_PATH = test_dir / "app.db"
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    from backend.models.database import init_db

    init_db()

    yield test_dir

    shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def sample_pdf_bytes(tmp_path) -> bytes:
    """Generate a tiny 2-page PDF in-memory using PyMuPDF, so tests don't
    need a binary fixture file checked into the repo."""
    import fitz

    doc = fitz.open()
    page1 = doc.new_page()
    page1.insert_text(
        (50, 72),
        "Photosynthesis is the process by which green plants convert light "
        "energy into chemical energy using chlorophyll.",
        fontsize=11,
    )
    page2 = doc.new_page()
    page2.insert_text(
        (50, 72),
        "TCP is connection-oriented and reliable. UDP is connectionless and faster but unreliable.",
        fontsize=11,
    )
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes
