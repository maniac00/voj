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


@pytest.fixture(autouse=True)
def _local_mode():
    settings.ENVIRONMENT = "local"
    # Force BYPASS mode
    settings.LOCAL_BYPASS_ENABLED = True
    yield


def test_login_local_bypass():
    client = TestClient(app)
    resp = client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "pw"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["access_token"]
    assert data["email"] == "a@b.com"


def test_me_endpoint_works_with_bypass():
    client = TestClient(app)
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["sub"]
    assert data["token_use"] == "access"


def test_logout_local_bypass():
    client = TestClient(app)
    # Missing header triggers LOCAL_DEV_BYPASS in local mode without Cognito
    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 200, resp.text
    assert "Logged out" in resp.json().get("message", "")

