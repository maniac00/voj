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
from app.services.books_sql import BookServiceSQL as BookService  # noqa: E402
from app.models.database import Base, engine, SessionLocal  # noqa: E402


@pytest.fixture(autouse=True)
def _setup_sqlite_db(tmp_path):
    # 로컬 모드 + 간단 인증 바이패스
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    # SQL 테이블 생성 (SQLite 파일 기반)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_create_get_update_delete_book(db_session):
    user_id = "u-" + _uuid.uuid4().hex[:8]
    # create
    b = BookService.create_book(db_session, user_id=user_id, title="t1", author="a1")
    assert b.user_id == user_id
    # get
    g = BookService.get_book(db_session, user_id=user_id, book_id=b.book_id)
    assert g is not None and g.book_id == b.book_id
    # update
    u = BookService.update_book(db_session, user_id=user_id, book_id=b.book_id, title="t2")
    assert u is not None and u.title == "t2"
    # list
    items = BookService.list_all_books(db_session, user_id=user_id)
    assert any(it.book_id == b.book_id for it in items)
    # delete
    ok = BookService.delete_book(db_session, user_id=user_id, book_id=b.book_id)
    assert ok is True
    assert BookService.get_book(db_session, user_id=user_id, book_id=b.book_id) is None


