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
from app.services.storage import factory as storage_factory  # noqa: E402
from app.core.auth import simple as auth_simple  # noqa: E402


@pytest.fixture(autouse=True)
def _prod_setup():
    settings.ENVIRONMENT = "production"
    yield


def _ensure_tables():
    from app.models.book import Book
    if not Book.exists():
        Book.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
    if not AudioChapter.exists():
        AudioChapter.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)


def test_streaming_uses_cloudfront_signed_url(monkeypatch):
    _ensure_tables()
    client = TestClient(app)

    # override auth to return a fixed user
    def _claims_override():
        return {"sub": "user-x"}

    app.dependency_overrides[auth_simple.get_current_user_claims] = lambda: _claims_override()

    book = BookService.create_book(user_id="user-x", title="B", author="A")
    ch = AudioChapter(
        chapter_id=str(uuid.uuid4()),
        book_id=book.book_id,
        chapter_number=1,
        title="Ch1",
        status="ready",
        file_info=FileInfo(original_name="001.m4a", file_size=100, mime_type="audio/mp4", s3_key=f"book/{book.book_id}/media/001.m4a"),
        audio_metadata=AudioMetadata(duration=123),
    )
    ch.save()

    # monkeypatch storage service with a fake signer/download URL provider
    class _FakeStorage:
        async def get_cloudfront_signed_url(self, key, expires_in=3600):
            return f"https://d.example.net/{key}?Signature=abc"

        async def get_download_url(self, key, expires_in=3600):
            return f"https://s3.example.net/{key}?X-Amz-Signature=xyz"

    # Patch the storage_service used inside audio endpoint module
    from app.api.v1.endpoints import audio as audio_ep
    monkeypatch.setattr(audio_ep, "storage_service", _FakeStorage())

    r = client.get(f"/api/v1/audio/{book.book_id}/chapters/{ch.chapter_id}/stream")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["streaming_url"].startswith("https://d.example.net/")
    assert data["duration"] == 123

    # cleanup override
    app.dependency_overrides.pop(auth_simple.get_current_user_claims, None)


