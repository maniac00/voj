import sys
import os
import pytest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.auth import deps  # noqa: E402


@pytest.mark.asyncio
async def test_extract_user_scopes_from_various_claims():
    claims = {
        "scope": "admin editor",
        "cognito:groups": ["reviewer"],
        "custom:role": "owner",
        "roles": ["Auditor"],
    }
    s = deps._extract_user_scopes(claims)
    assert {"admin", "editor", "reviewer", "owner", "auditor"}.issubset(s)


@pytest.mark.asyncio
async def test_require_any_scope_allows_when_one_matches():
    # Build dep
    dep = deps.require_any_scope(["admin", "editor"])

    # Call through FastAPI Depends signature by invoking the outer callable
    claims = {"cognito:groups": ["editor"]}
    out = await dep(claims)  # type: ignore
    assert out is claims


@pytest.mark.asyncio
async def test_require_any_scope_denies_when_none_match():
    dep = deps.require_any_scope(["admin"])

    claims = {"scope": "viewer"}
    with pytest.raises(Exception):
        await dep(claims)  # type: ignore

