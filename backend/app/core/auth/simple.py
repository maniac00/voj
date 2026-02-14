"""
간단한 하드코딩 인증 시스템
PRD v2.0 요구사항에 따라 admin/admin123 계정만 지원
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
import base64
from typing import Any, Callable, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings


# 관리자/앱 계정 (설정에서 읽어옴)
def get_admin_credentials() -> Dict[str, Optional[str]]:
    # 두 개의 정적 계정을 모두 허용 (어드민/앱 계정)
    creds: Dict[str, Optional[str]] = {
        settings.SIMPLE_AUTH_USERNAME: settings.SIMPLE_AUTH_PASSWORD,
    }
    app_user = getattr(settings, "SIMPLE_AUTH_APP_USERNAME", None)
    app_pass = getattr(settings, "SIMPLE_AUTH_APP_PASSWORD", None)
    if app_user:
        creds[str(app_user)] = app_pass
    return creds


# 간단한 JWT 대체용 토큰 생성/검증

security = HTTPBearer(auto_error=False)


def _get_secret_key() -> str:
    """settings에서 SECRET_KEY를 가져온다."""
    return settings.SECRET_KEY


def create_simple_token(username: str) -> str:
    """간단한 토큰 생성 (JWT 대체)"""
    payload = {
        "username": username,
        "exp": int(time.time()) + 86400,  # 24시간 유효
        "iat": int(time.time()),
        "sub": f"simple-user-{username}",
        "scope": "admin",
    }

    secret_key = _get_secret_key()

    # 간단한 서명 생성
    payload_str = json.dumps(payload, sort_keys=True)
    # URL-safe 인코딩으로 Authorization 헤더 호환성 확보
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode()
    signature = hmac.new(
        secret_key.encode(), payload_str.encode(), hashlib.sha256
    ).hexdigest()

    # base64 인코딩 없이 간단하게
    return f"{payload_b64}.{signature}"


def verify_simple_token(token: str) -> Dict[str, Any]:
    """간단한 토큰 검증"""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            raise ValueError("Invalid token format")

        payload_b64, signature = parts

        secret_key = _get_secret_key()

        # 서명 검증
        # 디코딩 전 원본 payload 문자열로 서명 검증
        payload_bytes = base64.urlsafe_b64decode(payload_b64.encode())
        payload_str = payload_bytes.decode()
        expected_signature = hmac.new(
            secret_key.encode(), payload_str.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid signature")

        payload: Dict[str, Any] = json.loads(payload_str)

        # 만료 시간 확인
        if payload.get("exp", 0) < time.time():
            raise ValueError("Token expired")

        return payload

    except Exception as e:
        raise ValueError(f"Token verification failed: {e}")


def authenticate_user(username: str, password: str) -> bool:
    """사용자 인증"""
    admin_credentials = get_admin_credentials()
    return admin_credentials.get(username) == password


async def get_current_user_claims_simple(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """간단한 인증으로 현재 사용자 클레임 조회"""

    # 로컬 환경에서는 바이패스 허용
    if settings.ENVIRONMENT == "local" and settings.LOCAL_BYPASS_ENABLED:
        if not credentials:
            return {
                "sub": settings.LOCAL_BYPASS_SUB,
                "username": settings.LOCAL_BYPASS_USERNAME,
                "scope": settings.LOCAL_BYPASS_SCOPE,
                "email": settings.LOCAL_BYPASS_EMAIL,
            }

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims_dict: Dict[str, Any] = verify_simple_token(credentials.credentials)
        return claims_dict
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin_scope() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """관리자 권한 요구 디펜던시"""

    async def _dep(
        claims: Dict[str, Any] = Depends(get_current_user_claims_simple),
    ) -> Dict[str, Any]:
        user_scope = claims.get("scope", "").lower()
        if user_scope != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )
        return claims

    return _dep  # type: ignore[return-value]


# 기존 인터페이스와의 호환성을 위한 별칭
get_current_user_claims = get_current_user_claims_simple


def require_any_scope(required_scopes: List[str]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """기존 스코프 체크 인터페이스 유지"""

    async def _dep(
        claims: Dict[str, Any] = Depends(get_current_user_claims_simple),
    ) -> Dict[str, Any]:
        user_scope = claims.get("scope", "").lower()
        if user_scope not in [s.lower() for s in required_scopes]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope"
            )
        return claims

    return _dep  # type: ignore[return-value]
