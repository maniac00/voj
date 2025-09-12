import sys
import os
from datetime import datetime, timedelta, timezone

import pytest
import jwt as pyjwt


# Ensure 'app' package is importable when running tests from repo root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings  # noqa: E402
from app.core.auth import jwt as jwt_mod  # noqa: E402


@pytest.fixture(autouse=True)
def _configure_settings():
    # Configure settings used by verify_cognito_jwt
    settings.COGNITO_REGION = "ap-northeast-2"
    settings.COGNITO_USER_POOL_ID = "local_pool"
    settings.COGNITO_CLIENT_ID = "test_client"
    # Clear JWKS cache before each test
    jwt_mod._JWKS_CACHE = {}
    jwt_mod._JWKS_CACHE_TS = None
    yield


def _generate_rsa_keypair():
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def _make_token(private_pem: bytes, kid: str, token_use: str, extra_claims: dict) -> str:
    now = datetime.now(timezone.utc)
    iss = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
    payload = {
        "iss": iss,
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
        "token_use": token_use,
        **extra_claims,
    }
    headers = {"kid": kid, "alg": "RS256"}
    return pyjwt.encode(payload, private_pem, algorithm="RS256", headers=headers)


def _fake_jwk_client_factory(key_map: dict):
    class _SigningKey:
        def __init__(self, key: bytes):
            self.key = key

    class _FakeJWKClient:
        def __init__(self, jwks_url: str):
            self.jwks_url = jwks_url

        def get_signing_key_from_jwt(self, token: str):
            header = pyjwt.get_unverified_header(token)
            kid = header.get("kid")
            pub = key_map[kid]
            return _SigningKey(pub)

    return _FakeJWKClient


@pytest.mark.asyncio
async def test_verify_cognito_jwt_empty_token_raises():
    with pytest.raises(ValueError):
        await jwt_mod.verify_cognito_jwt("")


@pytest.mark.asyncio
async def test_verify_cognito_jwt_access_success_and_client_id_mismatch(monkeypatch):
    # Generate keypair and patch JWK client to return our public key by kid
    priv, pub = _generate_rsa_keypair()
    key_map = {"k1": pub}
    jwt_mod.PyJWKClient = _fake_jwk_client_factory(key_map)

    # Patch httpx.AsyncClient to avoid real JWKS HTTP call (return 200 with body)
    class _FakeResp:
        def __init__(self):
            self.status_code = 200
        def raise_for_status(self):
            return self
        def json(self):
            return {"keys": []}

    class _FakeAsyncClient:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def get(self, url: str):
            return _FakeResp()

    monkeypatch.setattr(jwt_mod.httpx, "AsyncClient", _FakeAsyncClient)

    # Success: access token with matching client_id
    token_ok = _make_token(priv, kid="k1", token_use="access", extra_claims={"client_id": settings.COGNITO_CLIENT_ID})
    claims = await jwt_mod.verify_cognito_jwt(token_ok)
    assert claims["client_id"] == settings.COGNITO_CLIENT_ID
    assert claims["token_use"] == "access"

    # Failure: client_id mismatch
    token_bad = _make_token(priv, kid="k1", token_use="access", extra_claims={"client_id": "wrong_client"})
    with pytest.raises(pyjwt.InvalidAudienceError):
        await jwt_mod.verify_cognito_jwt(token_bad)


@pytest.mark.asyncio
async def test_verify_cognito_jwt_id_token_success(monkeypatch):
    priv, pub = _generate_rsa_keypair()
    key_map = {"kid-id": pub}
    jwt_mod.PyJWKClient = _fake_jwk_client_factory(key_map)

    class _FakeResp2:
        def __init__(self):
            self.status_code = 200
        def raise_for_status(self):
            return self
        def json(self):
            return {"keys": []}

    class _FakeAsyncClient2:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def get(self, url: str):
            return _FakeResp2()

    monkeypatch.setattr(jwt_mod.httpx, "AsyncClient", _FakeAsyncClient2)

    token = _make_token(priv, kid="kid-id", token_use="id", extra_claims={"aud": settings.COGNITO_CLIENT_ID})
    claims = await jwt_mod.verify_cognito_jwt(token)
    assert claims["token_use"] == "id"
    assert settings.COGNITO_CLIENT_ID in (claims.get("aud") if isinstance(claims.get("aud"), list) else [claims.get("aud")])


@pytest.mark.asyncio
async def test_fetch_jwks_timeout_raises(monkeypatch):
    class _FakeAsyncClient3:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def get(self, url: str):
            raise jwt_mod.httpx.TimeoutException("timeout")

    monkeypatch.setattr(jwt_mod.httpx, "AsyncClient", _FakeAsyncClient3)

    # Provide any non-empty token; we won't reach signature validation due to timeout in JWKS fetch
    with pytest.raises(jwt_mod.httpx.TimeoutException):
        await jwt_mod.verify_cognito_jwt("dummy-token")


@pytest.mark.asyncio
async def test_key_rotation_two_kids_both_verify(monkeypatch):
    # Two separate keys simulating rotation (kid changes)
    priv1, pub1 = _generate_rsa_keypair()
    priv2, pub2 = _generate_rsa_keypair()
    key_map = {"k-old": pub1, "k-new": pub2}
    jwt_mod.PyJWKClient = _fake_jwk_client_factory(key_map)

    class _FakeResp4:
        def __init__(self):
            self.status_code = 200
        def raise_for_status(self):
            return self
        def json(self):
            return {"keys": []}

    class _FakeAsyncClient4:
        def __init__(self, *args, **kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def get(self, url: str):
            return _FakeResp4()

    monkeypatch.setattr(jwt_mod.httpx, "AsyncClient", _FakeAsyncClient4)

    token_old = _make_token(priv1, kid="k-old", token_use="access", extra_claims={"client_id": settings.COGNITO_CLIENT_ID})
    token_new = _make_token(priv2, kid="k-new", token_use="access", extra_claims={"client_id": settings.COGNITO_CLIENT_ID})

    claims1 = await jwt_mod.verify_cognito_jwt(token_old)
    claims2 = await jwt_mod.verify_cognito_jwt(token_new)

    assert claims1["token_use"] == "access"
    assert claims2["token_use"] == "access"

