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
from app.models.database import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def _local_setup():
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    Base.metadata.drop_all(bind=engine)
    # Ensure SQL tables exist
    Base.metadata.create_all(bind=engine)
    yield


def test_create_book_endpoint_works_in_local_with_bypass():
    client = TestClient(app)
    resp = client.post(
        "/api/v1/books/",
        json={
            "title": "My Book",
            "author": "Author",
            "narrator": "Narrator",
            "description": "d",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "My Book"
    assert data["author"] == "Author"
    assert data["narrator"] == "Narrator"
    assert data["user_id"]
