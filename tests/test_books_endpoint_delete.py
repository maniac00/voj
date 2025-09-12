import sys
import os
import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services.books import BookService  # noqa: E402
from app.models.book import Book  # noqa: E402


@pytest.fixture(autouse=True)
def _local_setup():
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    if not Book.exists():
        Book.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
    yield


def test_delete_book_success():
    client = TestClient(app)
    created = BookService.create_book(user_id=settings.LOCAL_BYPASS_SUB, title="T1", author="A1")
    resp = client.delete(f"/api/v1/books/{created.book_id}")
    assert resp.status_code == 200, resp.text
    assert BookService.get_book(user_id=settings.LOCAL_BYPASS_SUB, book_id=created.book_id) is None


def test_delete_book_not_owned_returns_404():
    client = TestClient(app)
    created = BookService.create_book(user_id="someone-else", title="T1", author="A1")
    resp = client.delete(f"/api/v1/books/{created.book_id}")
    assert resp.status_code == 404

