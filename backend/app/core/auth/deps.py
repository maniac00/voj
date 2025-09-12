"""
FastAPI dependencies for authentication with AWS Cognito JWTs.
"""
from __future__ import annotations

from typing import Annotated, Dict, Optional, Callable, List, Set
import re

from fastapi import Depends, Header, HTTPException, status

from app.core.auth.jwt import verify_cognito_jwt
from app.core.config import settings


async def get_bearer_token(authorization: Optional[str] = Header(default=None)) -> str:
    if not authorization:
        # Local dev bypass for convenience
        if settings.ENVIRONMENT == "local" and settings.LOCAL_BYPASS_ENABLED:
            return "LOCAL_DEV_BYPASS"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header format")
    return parts[1]


async def get_current_user_claims(token: Annotated[str, Depends(get_bearer_token)]) -> Dict:
    # Bypass in local dev when no token provided
    if settings.ENVIRONMENT == "local" and token == "LOCAL_DEV_BYPASS":
        claims: Dict[str, str] = {
            "sub": settings.LOCAL_BYPASS_SUB,
            "email": settings.LOCAL_BYPASS_EMAIL,
            "cognito:username": settings.LOCAL_BYPASS_USERNAME,
            "token_use": "access",
            "scope": settings.LOCAL_BYPASS_SCOPE,
        }
        if settings.LOCAL_BYPASS_GROUPS:
            claims["cognito:groups"] = list(settings.LOCAL_BYPASS_GROUPS)
        return claims

    try:
        claims = await verify_cognito_jwt(token)
        return claims
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}")


def require_any_scope(required_scopes: List[str]) -> Callable[[Dict], Dict]:
    """Dependency factory to ensure the user has at least one of the required scopes.
    Cognito access token typically includes a space-separated 'scope' claim.
    """

    async def _dep(claims: Annotated[Dict, Depends(get_current_user_claims)]) -> Dict:
        user_scopes = _extract_user_scopes(claims)
        reqs = {s.lower() for s in required_scopes}
        if not any(req in user_scopes for req in reqs):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope")
        return claims

    return _dep


def _extract_user_scopes(claims: Dict) -> Set[str]:
    """Extract normalized scopes/roles from various Cognito/custom claims.

    - scope/s: space or comma separated string
    - cognito:groups: list[str]
    - custom:role: single string
    - roles: list[str]
    """
    scopes: Set[str] = set()

    # scope(s) string: split by space or comma
    raw_scopes = str(claims.get("scope") or claims.get("scopes") or "").strip()
    if raw_scopes:
        for token in re.split(r"[\s,]+", raw_scopes):
            if token:
                scopes.add(token.lower())

    # groups
    groups = claims.get("cognito:groups")
    if isinstance(groups, list):
        for g in groups:
            if isinstance(g, str) and g:
                scopes.add(g.lower())

    # custom:role
    custom_role = claims.get("custom:role")
    if isinstance(custom_role, str) and custom_role:
        scopes.add(custom_role.lower())

    # roles list
    roles = claims.get("roles")
    if isinstance(roles, list):
        for r in roles:
            if isinstance(r, str) and r:
                scopes.add(r.lower())

    return scopes

