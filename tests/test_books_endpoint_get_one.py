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
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_get_book_owned_by_user_returns_200():
    client = TestClient(app)
    # create under local bypass user
    with SessionLocal() as db:
        created = BookService.create_book(
            db,
            user_id=settings.LOCAL_BYPASS_SUB,
            title="Owned",
            author="Me",
            narrator="Reader",
        )
    resp = client.get(f"/api/v1/books/{created.book_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["book_id"] == created.book_id
    assert resp.json()["narrator"] == "Reader"


def test_get_book_other_user_still_returns_200_for_global_read():
    client = TestClient(app)
    # create under another user
    with SessionLocal() as db:
        created = BookService.create_book(
            db, user_id="someone-else", title="Other", author="Them"
        )
    resp = client.get(f"/api/v1/books/{created.book_id}")
    assert resp.status_code == 200
    assert resp.json()["book_id"] == created.book_id
