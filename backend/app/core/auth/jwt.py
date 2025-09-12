"""
JWT verification utilities for AWS Cognito
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional

import httpx
import jwt
from jwt import PyJWKClient

from app.core.config import settings


_JWKS_CACHE: Dict[str, Any] = {}
_JWKS_CACHE_TS: Optional[float] = None
_JWKS_TTL_SECONDS = 60 * 60  # 1 hour


def _get_issuer() -> str:
    return f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"


async def fetch_jwks() -> Dict[str, Any]:
    global _JWKS_CACHE, _JWKS_CACHE_TS
    if _JWKS_CACHE and _JWKS_CACHE_TS and (time.time() - _JWKS_CACHE_TS) < _JWKS_TTL_SECONDS:
        return _JWKS_CACHE

    jwks_url = f"{_get_issuer()}/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(jwks_url)
        resp.raise_for_status()
        _JWKS_CACHE = resp.json()
        _JWKS_CACHE_TS = time.time()
        return _JWKS_CACHE


async def verify_cognito_jwt(token: str) -> Dict[str, Any]:
    """
    Verify a JWT issued by AWS Cognito.

    - Validates signature using JWKS
    - Verifies issuer and expiration
    - For id_token: verifies audience matches client id
    - For access_token: verifies client_id matches client id
    """
    if not token:
        raise ValueError("Empty token")

    jwks = await fetch_jwks()
    issuer = _get_issuer()

    # Use PyJWT's PyJWKClient for key selection by kid
    jwk_client = PyJWKClient(jwks_url=f"{issuer}/.well-known/jwks.json")
    signing_key = jwk_client.get_signing_key_from_jwt(token).key

    # Decode without specifying audience first to inspect claims
    unverified = jwt.decode(
        token,
        signing_key,
        algorithms=["RS256"],
        options={"verify_aud": False},
        issuer=issuer,
    )

    token_use = unverified.get("token_use")
    client_id = settings.COGNITO_CLIENT_ID

    if token_use == "id":
        # Re-decode verifying audience
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=issuer,
        )
    elif token_use == "access":
        # Access token contains client_id claim
        if unverified.get("client_id") != client_id:
            raise jwt.InvalidAudienceError("client_id does not match")
        # Validate again (aud not required)
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
            issuer=issuer,
        )
    else:
        # Unknown token type
        raise jwt.InvalidTokenError("Unsupported token_use")

    return claims


