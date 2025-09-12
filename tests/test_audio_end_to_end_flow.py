import sys
import os
import uuid
import io
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


def test_audio_upload_list_reorder_delete_flow():
    _ensure_tables()
    client = TestClient(app)

    # 1) Book 생성 (로컬 바이패스 사용자)
    book = BookService.create_book(user_id=settings.LOCAL_BYPASS_SUB, title="B", author="A")

    # 2) 파일 업로드 (uploads)
    content = b"\x00" * 2048
    files = {"file": ("001 Intro.wav", content, "audio/wav")}
    params = {"user_id": settings.LOCAL_BYPASS_SUB, "book_id": book.book_id, "file_type": "uploads"}
    r = client.post("/api/v1/files/upload", files=files, params=params)
    assert r.status_code == 200, r.text
    upload_res = r.json()
    key = upload_res["key"]

    # 3) 오디오 챕터 레코드 생성 (업로드 결과 연결)
    chap = AudioChapter(
        chapter_id=str(uuid.uuid4()),
        book_id=book.book_id,
        chapter_number=1,
        title="Intro",
        status="ready",
        file_info=FileInfo(original_name="001 Intro.wav", file_size=len(content), mime_type="audio/wav", s3_key=key),
        audio_metadata=AudioMetadata(duration=60),
    )
    chap.save()

    # 4) 목록 조회
    r = client.get(f"/api/v1/audio/{book.book_id}/chapters")
    assert r.status_code == 200, r.text
    data = r.json()
    assert any(it["title"] == "Intro" for it in data)

    # 5) 순서 변경
    r = client.put(f"/api/v1/audio/{book.book_id}/chapters/{chap.chapter_id}?new_number=3")
    assert r.status_code == 200, r.text
    assert r.json()["chapter_number"] == 3

    # 6) 삭제
    r = client.delete(f"/api/v1/audio/{book.book_id}/chapters/{chap.chapter_id}")
    assert r.status_code == 200, r.text

    # 7) 목록 재확인 (삭제됨)
    r = client.get(f"/api/v1/audio/{book.book_id}/chapters")
    assert r.status_code == 200
    titles = [it["title"] for it in r.json()]
    assert "Intro" not in titles


