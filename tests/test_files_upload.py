import sys
import os
import io
import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app  # noqa: E402
from app.core.config import settings  # noqa: E402


@pytest.fixture(autouse=True)
def _local_setup(tmp_path):
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    settings.LOCAL_BYPASS_GROUPS = []
    # Ensure local storage directories exist
    settings.LOCAL_STORAGE_PATH = str(tmp_path)
    settings.LOCAL_UPLOADS_PATH = os.path.join(str(tmp_path), "uploads")
    settings.LOCAL_MEDIA_PATH = os.path.join(str(tmp_path), "media")
    settings.LOCAL_BOOKS_PATH = os.path.join(str(tmp_path), "books")
    yield


def test_upload_audio_success_and_key_format():
    client = TestClient(app)
    file_content = b"\x00" * 1024  # 1KB
    files = {
        "file": ("001 Intro.m4a", file_content, "audio/mp4"),
    }
    params = {
        "user_id": "user-1",
        "book_id": "book-1",
        "file_type": "uploads",
    }
    resp = client.post("/api/v1/files/upload", files=files, params=params)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    # key should follow: book/<book_id>/<prefix>/<uuid>_<filename>
    assert data["key"].startswith("book/book-1/uploads/")
    assert data["size"] == len(file_content)


def test_upload_rejects_unsupported_type():
    client = TestClient(app)
    files = {
        "file": ("note.txt", b"hello", "text/plain"),
    }
    params = {
        "user_id": "user-1",
        "book_id": "book-1",
        "file_type": "uploads",
    }
    resp = client.post("/api/v1/files/upload", files=files, params=params)
    assert resp.status_code == 400


def test_upload_forbidden_without_required_scope():
    client = TestClient(app)
    # Drop admin/editor scope
    settings.LOCAL_BYPASS_SCOPE = "viewer"
    files = {
        "file": ("001.m4a", b"\x00" * 100, "audio/mp4"),
    }
    params = {
        "user_id": "user-1",
        "book_id": "book-1",
        "file_type": "uploads",
    }
    resp = client.post("/api/v1/files/upload", files=files, params=params)
    assert resp.status_code == 403

