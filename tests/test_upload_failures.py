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


def test_upload_transient_error_then_retry_success(monkeypatch):
    client = TestClient(app)
    book = _ensure_book()

    # 준비: 정상 작은 m4a 페이로드
    payload = b"0" * (64 * 1024)  # 64KB
    files = {
        "file": ("retry.m4a", payload, "audio/mp4"),
    }

    call_count = {"n": 0}

    # storage_service.upload_file에 일시 실패 → 성공 시뮬레이션
    from app.api.v1.endpoints import files as files_endpoint

    async def fake_upload_file(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise Exception("simulated transient storage failure")

        class Result:
            success = True
            key = "book/test/uploads/retry_retry.m4a"
            size = len(payload)
            url = None

        return Result()

    monkeypatch.setattr(files_endpoint.storage_service, "upload_file", fake_upload_file, raising=True)

    # 1차 요청: 500 (일시 오류)
    r1 = client.post(f"/api/v1/files/upload/audio?book_id={book.book_id}", files=files)
    assert r1.status_code == 500

    # 2차 재시도: 200
    r2 = client.post(f"/api/v1/files/upload/audio?book_id={book.book_id}", files=files)
    assert r2.status_code == 200
    data = r2.json()
    assert data.get("success") is True
    assert data.get("chapter_id")


