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
from app.models.book import Book  # noqa: E402


@pytest.fixture(autouse=True)
def _local_setup():
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    if not Book.exists():
        Book.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
    yield


def test_books_e2e_flow():
    client = TestClient(app)

    # 1) Create
    r = client.post("/api/v1/books/", json={"title": "Flow", "author": "Tester"})
    assert r.status_code == 201, r.text
    created = r.json()

    # 2) List
    r = client.get("/api/v1/books/?size=10")
    assert r.status_code == 200
    assert any(it["book_id"] == created["book_id"] for it in r.json()["books"])

    # 3) Get
    r = client.get(f"/api/v1/books/{created['book_id']}")
    assert r.status_code == 200
    assert r.json()["title"] == "Flow"

    # 4) Update
    r = client.put(f"/api/v1/books/{created['book_id']}", json={"title": "Flow2"})
    assert r.status_code == 200
    assert r.json()["title"] == "Flow2"

    # 5) Delete
    r = client.delete(f"/api/v1/books/{created['book_id']}")
    assert r.status_code == 200
    # confirm 404 afterwards
    r = client.get(f"/api/v1/books/{created['book_id']}")
    assert r.status_code == 404
