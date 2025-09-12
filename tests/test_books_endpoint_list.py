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


def test_list_books_basic():
    client = TestClient(app)
    # Seed a book for the local bypass user
    b = BookService.create_book(user_id=settings.LOCAL_BYPASS_SUB, title="Alpha", author="Author A")
    resp = client.get("/api/v1/books/?size=5")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] >= 1
    assert any(it["book_id"] == b.book_id for it in data["books"])


def test_list_books_search_filters():
    client = TestClient(app)
    # Add another book
    _ = BookService.create_book(user_id=settings.LOCAL_BYPASS_SUB, title="Beta", author="Alice")
    resp = client.get("/api/v1/books/?size=10&search=beta")
    assert resp.status_code == 200
    data = resp.json()
    assert any("Beta" == it["title"] for it in data["books"])  # search by title

