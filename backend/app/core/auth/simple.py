"""
통합 인증 시스템
- HMAC 토큰: 관리자 웹 (payload_b64.signature, '.' 1개)
- Firebase JWT: 모바일 앱 (header.payload.signature, '.' 2개)
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

# 관리자/앱 계정 (설정에서 읽어옴)
def get_admin_credentials() -> Dict[str, Optional[str]]:
    creds: Dict[str, Optional[str]] = {
        settings.SIMPLE_AUTH_USERNAME: settings.SIMPLE_AUTH_PASSWORD,
    }
    app_user = getattr(settings, "SIMPLE_AUTH_APP_USERNAME", None)
    app_pass = getattr(settings, "SIMPLE_AUTH_APP_PASSWORD", None)
    if app_user:
        creds[str(app_user)] = app_pass
    return creds


security = HTTPBearer(auto_error=False)


def _get_secret_key() -> str:
    return settings.SECRET_KEY


def create_simple_token(username: str) -> str:
    """간단한 HMAC 토큰 생성 (JWT 대체)"""
    payload = {
        "username": username,
        "exp": int(time.time()) + 86400,
        "iat": int(time.time()),
        "sub": f"simple-user-{username}",
        "scope": "admin",
    }

    secret_key = _get_secret_key()
    payload_str = json.dumps(payload, sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_str.encode()).decode()
    signature = hmac.new(
        secret_key.encode(), payload_str.encode(), hashlib.sha256
    ).hexdigest()

    return f"{payload_b64}.{signature}"


def verify_simple_token(token: str) -> Dict[str, Any]:
    """HMAC 토큰 검증"""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            raise ValueError("Invalid token format")

        payload_b64, signature = parts
        secret_key = _get_secret_key()

        payload_bytes = base64.urlsafe_b64decode(payload_b64.encode())
        payload_str = payload_bytes.decode()
        expected_signature = hmac.new(
            secret_key.encode(), payload_str.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid signature")

        payload: Dict[str, Any] = json.loads(payload_str)

        if payload.get("exp", 0) < time.time():
            raise ValueError("Token expired")

        return payload

    except Exception as e:
        raise ValueError(f"Token verification failed: {e}")


def authenticate_user(username: str, password: str) -> bool:
    admin_credentials = get_admin_credentials()
    return admin_credentials.get(username) == password


def _detect_token_type(token: str) -> str:
    """토큰 형식으로 인증 타입을 판별한다. '.' 2개 = Firebase JWT, '.' 1개 = HMAC"""
    dot_count = token.count(".")
    if dot_count == 2:
        return "firebase"
    return "hmac"


async def get_current_user_claims(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Dict[str, Any]:
    """통합 인증: Firebase JWT 또는 HMAC 토큰 모두 처리
    Bearer 헤더가 없을 경우 voj_access_token 쿠키에서 토큰을 읽는다.
    (브라우저 <img> 태그 등 헤더를 직접 설정할 수 없는 요청 지원)
    """

    # 로컬 바이패스
    if settings.ENVIRONMENT == "local" and settings.LOCAL_BYPASS_ENABLED:
        if not credentials:
            return {
                "sub": settings.LOCAL_BYPASS_SUB,
                "username": settings.LOCAL_BYPASS_USERNAME,
                "scope": settings.LOCAL_BYPASS_SCOPE,
                "email": settings.LOCAL_BYPASS_EMAIL,
                "auth_type": "bypass",
            }

    # Bearer 헤더가 없으면 쿠키에서 토큰 읽기 (img/video 태그 등)
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    else:
        token = request.cookies.get("voj_access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token_type = _detect_token_type(token)

    if token_type == "firebase":
        return _verify_firebase_jwt(token)
    else:
        return _verify_hmac_token(token)


def _verify_hmac_token(token: str) -> Dict[str, Any]:
    """HMAC 토큰을 검증하고 claims를 반환한다."""
    try:
        claims = verify_simple_token(token)
        claims["auth_type"] = "hmac"
        return claims
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def _verify_firebase_jwt(token: str) -> Dict[str, Any]:
    """Firebase JWT를 검증하고 UserSQL에서 사용자를 조회한다."""
    from app.core.auth.firebase import is_firebase_initialized, verify_firebase_token
    from app.models.database import SessionLocal
    from app.services.user_service import UserService

    if not is_firebase_initialized():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase authentication is not configured",
        )

    try:
        decoded = verify_firebase_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    firebase_uid = decoded.get("uid", "")
    email = decoded.get("email", "")

    # DB에서 사용자 조회
    db = SessionLocal()
    try:
        user = UserService.get_user_by_firebase_uid(db, firebase_uid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found. Please login via /auth/firebase-login first.",
            )

        return {
            "sub": str(user.id),
            "user_id": user.id,
            "username": user.display_name or email,
            "email": user.email,
            "scope": "admin" if user.role.value == "admin" else "user",
            "status": user.status.value,
            "role": user.role.value,
            "auth_type": "firebase",
        }
    finally:
        db.close()


# 기존 인터페이스 호환
get_current_user_claims_simple = get_current_user_claims


def require_admin_scope() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """관리자 권한 요구 디펜던시"""

    async def _dep(
        claims: Dict[str, Any] = Depends(get_current_user_claims),
    ) -> Dict[str, Any]:
        user_scope = claims.get("scope", "").lower()
        if user_scope != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )
        return claims

    return _dep  # type: ignore[return-value]


def require_any_scope(required_scopes: List[str]) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """기존 스코프 체크 인터페이스 유지"""

    async def _dep(
        claims: Dict[str, Any] = Depends(get_current_user_claims),
    ) -> Dict[str, Any]:
        user_scope = claims.get("scope", "").lower()
        if user_scope not in [s.lower() for s in required_scopes]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient scope"
            )
        return claims

    return _dep  # type: ignore[return-value]


def require_approved_user() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """승인된 사용자만 허용하는 디펜던시. HMAC(관리자)는 항상 통과."""

    async def _dep(
        claims: Dict[str, Any] = Depends(get_current_user_claims),
    ) -> Dict[str, Any]:
        auth_type = claims.get("auth_type", "hmac")

        # HMAC 사용자(관리자 웹)와 로컬 바이패스는 항상 통과
        if auth_type in ("hmac", "bypass"):
            return claims

        # Firebase 사용자는 approved 상태인지 확인
        user_status = claims.get("status", "")
        if user_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account not approved. Current status: {user_status}",
            )
        return claims

    return _dep  # type: ignore[return-value]
