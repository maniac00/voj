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
from app.services.books_sql import BookServiceSQL as BookService  # noqa: E402
from app.models.database import Base, engine, SessionLocal  # noqa: E402


@pytest.fixture(autouse=True)
def _local_setup():
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    Base.metadata.create_all(bind=engine)
    yield


def test_update_book_success():
    client = TestClient(app)
    with SessionLocal() as db:
        created = BookService.create_book(db, user_id=settings.LOCAL_BYPASS_SUB, title="T1", author="A1")
    resp = client.put(
        f"/api/v1/books/{created.book_id}",
        json={"title": "T2"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["title"] == "T2"


def test_update_book_not_owned_returns_404():
    client = TestClient(app)
    with SessionLocal() as db:
        created = BookService.create_book(db, user_id="someone-else", title="T1", author="A1")
    resp = client.put(
        f"/api/v1/books/{created.book_id}",
        json={"title": "T2"},
    )
    assert resp.status_code == 404
