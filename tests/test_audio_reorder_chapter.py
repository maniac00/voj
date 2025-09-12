import sys
import os
import uuid
import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services.books import BookService  # noqa: E402
from app.models.audio_chapter import AudioChapter, FileInfo, AudioMetadata  # noqa: E402


@pytest.fixture(autouse=True)
def _local_setup():
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    yield


def _ensure_tables():
    from app.models.book import Book
    if not Book.exists():
        Book.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
    if not AudioChapter.exists():
        AudioChapter.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)


def test_reorder_chapter_success():
    _ensure_tables()
    client = TestClient(app)
    book = BookService.create_book(user_id=settings.LOCAL_BYPASS_SUB, title="B", author="A")
    c = AudioChapter(
        chapter_id=str(uuid.uuid4()),
        book_id=book.book_id,
        chapter_number=1,
        title="Ch1",
        status="ready",
        file_info=FileInfo(original_name="001.m4a", file_size=100, mime_type="audio/mp4"),
        audio_metadata=AudioMetadata(duration=120),
    )
    c.save()

    r = client.put(f"/api/v1/audio/{book.book_id}/chapters/{c.chapter_id}?new_number=3")
    assert r.status_code == 200, r.text
    assert r.json()["chapter_number"] == 3


def test_reorder_chapter_for_not_owned_book_returns_404():
    _ensure_tables()
    client = TestClient(app)
    # another user's book
    other_book = BookService.create_book(user_id="someone", title="B", author="A")
    c = AudioChapter(
        chapter_id=str(uuid.uuid4()),
        book_id=other_book.book_id,
        chapter_number=1,
        title="Ch1",
        status="ready",
        file_info=FileInfo(original_name="001.m4a", file_size=100, mime_type="audio/mp4"),
        audio_metadata=AudioMetadata(duration=120),
    )
    c.save()

    r = client.put(f"/api/v1/audio/{other_book.book_id}/chapters/{c.chapter_id}?new_number=2")
    assert r.status_code == 404
