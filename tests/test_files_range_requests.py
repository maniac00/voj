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
from app.services.storage.local import LocalStorageService  # noqa: E402
from app.api.v1.endpoints import files as files_ep  # noqa: E402


@pytest.fixture(autouse=True)
def _local_setup(tmp_path):
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    settings.PORT = 8000
    # place a file in local storage
    base = tmp_path
    settings.LOCAL_STORAGE_PATH = str(base)
    target_key = "book/x/media/sample.bin"
    full_path = os.path.join(str(base), target_key)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb") as f:
        f.write(b"0123456789")
    # metadata
    with open(full_path + ".metadata", "w") as f:
        f.write("{}")
    # Reinitialize storage service for endpoints with new base path
    files_ep.storage_service = LocalStorageService()
    yield


def test_range_request_partial():
    client = TestClient(app)
    # Range bytes=2-5 → expect '2345' (4 bytes) and 206 with Content-Range
    r = client.get("/api/v1/files/book/x/media/sample.bin", headers={"Range": "bytes=2-5"})
    assert r.status_code == 206, r.text
    assert r.headers.get("Accept-Ranges") == "bytes"
    assert r.headers.get("Content-Range") == "bytes 2-5/10"
    assert r.content == b"2345"


def test_range_invalid_returns_416():
    client = TestClient(app)
    r = client.get("/api/v1/files/book/x/media/sample.bin", headers={"Range": "bytes=20-30"})
    assert r.status_code == 416
    assert r.headers.get("Content-Range") == "bytes */10"

