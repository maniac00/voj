"""
모바일 JWT + Refresh Token 인증 플로우 테스트
"""
import os
import sys
import types

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.models.database import Base, SessionLocal, engine
from app.models.mobile_refresh_token_sql import MobileRefreshTokenSQL


@pytest.fixture(autouse=True)
def _prepare_tables(monkeypatch):
    import app.core.telegram as telegram

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.query(MobileRefreshTokenSQL).delete()
        db.commit()

    def _fake_verify(id_token: str):
        suffix = id_token.replace("token-", "")
        return {
            "uid": f"uid-{suffix}",
            "email": f"mobile-{suffix}@example.com",
            "name": f"Mobile {suffix}",
            "picture": "",
        }

    fake_firebase_module = types.ModuleType("app.core.auth.firebase")
    fake_firebase_module.is_firebase_initialized = lambda: True
    fake_firebase_module.verify_firebase_token = _fake_verify
    monkeypatch.setitem(sys.modules, "app.core.auth.firebase", fake_firebase_module)
    monkeypatch.setattr(telegram, "send_new_user_notification", lambda **kwargs: None)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_mobile_login_issues_access_and_refresh_tokens(client: TestClient):
    response = client.post(
        "/api/v1/auth/mobile/login",
        json={"id_token": "token-login", "device_id": "device-a"},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 7200
    assert data["email"] == "mobile-login@example.com"

    with SessionLocal() as db:
        rows = (
            db.query(MobileRefreshTokenSQL)
            .filter(MobileRefreshTokenSQL.device_id == "device-a")
            .all()
        )
        assert len(rows) == 1
        assert rows[0].token_hash != data["refresh_token"]
        assert rows[0].revoked_at is None


def test_mobile_refresh_rotates_token_and_rejects_old_token(client: TestClient):
    login_resp = client.post(
        "/api/v1/auth/mobile/login",
        json={"id_token": "token-rotate", "device_id": "device-rotate"},
    )
    assert login_resp.status_code == 200, login_resp.text
    refresh_token_1 = login_resp.json()["refresh_token"]

    refresh_resp_1 = client.post(
        "/api/v1/auth/mobile/refresh",
        json={"refresh_token": refresh_token_1, "device_id": "device-rotate"},
    )
    assert refresh_resp_1.status_code == 200, refresh_resp_1.text
    refresh_token_2 = refresh_resp_1.json()["refresh_token"]
    assert refresh_token_2 != refresh_token_1

    old_reuse_resp = client.post(
        "/api/v1/auth/mobile/refresh",
        json={"refresh_token": refresh_token_1, "device_id": "device-rotate"},
    )
    assert old_reuse_resp.status_code == 401

    refresh_resp_2 = client.post(
        "/api/v1/auth/mobile/refresh",
        json={"refresh_token": refresh_token_2, "device_id": "device-rotate"},
    )
    assert refresh_resp_2.status_code == 200, refresh_resp_2.text

    with SessionLocal() as db:
        rows = (
            db.query(MobileRefreshTokenSQL)
            .filter(MobileRefreshTokenSQL.device_id == "device-rotate")
            .all()
        )
        assert len(rows) == 3
        revoked_count = sum(1 for row in rows if row.revoked_at is not None)
        assert revoked_count == 2


def test_mobile_refresh_requires_matching_device_id(client: TestClient):
    login_resp = client.post(
        "/api/v1/auth/mobile/login",
        json={"id_token": "token-device", "device_id": "device-origin"},
    )
    assert login_resp.status_code == 200, login_resp.text
    refresh_token = login_resp.json()["refresh_token"]

    mismatch_resp = client.post(
        "/api/v1/auth/mobile/refresh",
        json={"refresh_token": refresh_token, "device_id": "device-other"},
    )
    assert mismatch_resp.status_code == 401
