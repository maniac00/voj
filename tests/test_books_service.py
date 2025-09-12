import sys
import os
import uuid as _uuid
from datetime import datetime

import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings  # noqa: E402
from app.services.books import BookService  # noqa: E402
from app.models.book import Book  # noqa: E402


@pytest.fixture(autouse=True)
def _configure_local_dynamodb(tmp_path):
    # Ensure local mode for tests (DynamoDB Local)
    settings.ENVIRONMENT = "local"
    settings.DYNAMODB_ENDPOINT_URL = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:8001")
    # Create tables if not exists
    if not Book.exists():
        Book.create_table(read_capacity_units=5, write_capacity_units=5, wait=True)
    yield


def test_create_get_update_delete_book():
    user_id = "u-" + _uuid.uuid4().hex[:8]
    # create
    b = BookService.create_book(user_id=user_id, title="t1", author="a1")
    assert b.user_id == user_id
    # get
    g = BookService.get_book(user_id=user_id, book_id=b.book_id)
    assert g is not None and g.book_id == b.book_id
    # update
    u = BookService.update_book(user_id=user_id, book_id=b.book_id, title="t2")
    assert u is not None and u.title == "t2"
    # list
    page = BookService.list_books(user_id=user_id, limit=5)
    assert any(it.book_id == b.book_id for it in page.items)
    # delete
    ok = BookService.delete_book(user_id=user_id, book_id=b.book_id)
    assert ok is True
    assert BookService.get_book(user_id=user_id, book_id=b.book_id) is None


