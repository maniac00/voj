import sys
import os
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services.books import BookService  # noqa: E402


def _ensure_book():
    # 로컬 바이패스 사용자ID로 책 하나 생성
    return BookService.create_book(user_id=settings.LOCAL_BYPASS_SUB, title="Test Book", author="Tester")


def test_upload_unsupported_extension_returns_400():
    client = TestClient(app)
    book = _ensure_book()

    # txt 확장자 업로드 → 400
    files = {
        "file": ("not-audio.txt", b"hello", "text/plain"),
    }
    resp = client.post(f"/api/v1/files/upload/audio?book_id={book.book_id}", files=files)
    assert resp.status_code == 400
    assert "Only .mp4/.m4a files are allowed" in resp.json().get("detail", "")


def test_upload_too_large_returns_413():
    client = TestClient(app)
    book = _ensure_book()

    # 100MB 초과 가짜 페이로드 (100MB + 1KB)
    oversized = b"0" * (100 * 1024 * 1024 + 1024)
    files = {
        "file": ("huge.m4a", oversized, "audio/mp4"),
    }

    resp = client.post(f"/api/v1/files/upload/audio?book_id={book.book_id}", files=files)
    assert resp.status_code == 413
    assert "File size exceeds limit" in resp.json().get("detail", "")


