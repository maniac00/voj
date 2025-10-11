"""
두 정적 계정(MVP) 인증 동작 테스트
"""
import sys
import os
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


class TestStaticAccountsLogin:
    def test_login_admin(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "qwer1234"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("username") == "admin"
        assert data.get("access_token")

    def test_login_app_account_with_email(self, client: TestClient):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "dev@example.com", "password": "qwer1234"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("username") == "dev@example.com"
        assert data.get("access_token")

    def test_login_wrong_password(self, client: TestClient):
        for username in ["admin", "dev@example.com"]:
            resp = client.post(
                "/api/v1/auth/login",
                json={"username": username, "password": "wrong"},
            )
            assert resp.status_code in (400, 401, 422)


