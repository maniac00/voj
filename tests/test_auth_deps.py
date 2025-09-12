import sys
import os
import types
import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings  # noqa: E402
from app.core.auth import deps  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_local_bypass():
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    settings.LOCAL_BYPASS_SUB = "local-sub"
    settings.LOCAL_BYPASS_EMAIL = "local@example.com"
    settings.LOCAL_BYPASS_USERNAME = "local.user"
    settings.LOCAL_BYPASS_SCOPE = "admin editor"
    settings.LOCAL_BYPASS_GROUPS = ["editor"]
    yield


@pytest.mark.asyncio
async def test_get_bearer_token_local_bypass_when_missing_auth_header():
    token = await deps.get_bearer_token(authorization=None)
    assert token == "LOCAL_DEV_BYPASS"


@pytest.mark.asyncio
async def test_get_current_user_claims_uses_bypass_settings():
    claims = await deps.get_current_user_claims(token="LOCAL_DEV_BYPASS")
    assert claims["sub"] == settings.LOCAL_BYPASS_SUB
    assert claims["email"] == settings.LOCAL_BYPASS_EMAIL
    assert claims["cognito:username"] == settings.LOCAL_BYPASS_USERNAME
    # scope string split → includes both
    assert "admin" in claims["scope"] and "editor" in claims["scope"]
    assert "editor" in claims.get("cognito:groups", [])


@pytest.mark.asyncio
async def test_get_bearer_token_requires_header_when_bypass_disabled():
    settings.LOCAL_BYPASS_ENABLED = False
    with pytest.raises(Exception):
        await deps.get_bearer_token(authorization=None)

