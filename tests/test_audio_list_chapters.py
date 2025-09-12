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


def test_list_chapters_returns_data():
    _ensure_tables()
    client = TestClient(app)
    # seed book under local bypass user
    book = BookService.create_book(user_id=settings.LOCAL_BYPASS_SUB, title="B", author="A")
    # seed chapters
    ch1 = AudioChapter(
        chapter_id=str(uuid.uuid4()),
        book_id=book.book_id,
        chapter_number=1,
        title="Ch1",
        description=None,
        status="ready",
        file_info=FileInfo(original_name="001.m4a", file_size=100, mime_type="audio/mp4"),
        audio_metadata=AudioMetadata(duration=120),
    )
    ch1.save()
    ch2 = AudioChapter(
        chapter_id=str(uuid.uuid4()),
        book_id=book.book_id,
        chapter_number=2,
        title="Ch2",
        description=None,
        status="processing",
        file_info=FileInfo(original_name="002.m4a", file_size=200, mime_type="audio/mp4"),
        audio_metadata=AudioMetadata(duration=220),
    )
    ch2.save()

    r = client.get(f"/api/v1/audio/{book.book_id}/chapters")
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) >= 2
    assert any(it["title"] == "Ch1" for it in data)
    assert any(it["title"] == "Ch2" for it in data)


