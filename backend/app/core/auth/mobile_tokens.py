"""
모바일 앱 토큰 유틸리티
- Access Token: JWT (기본 2시간)
- Refresh Token: Opaque random 문자열 (기본 30일)
"""
from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.mobile_refresh_token_sql import MobileRefreshTokenSQL
from app.models.user_sql import UserSQL

MOBILE_ACCESS_ISSUER = "voj-mobile-auth"
MOBILE_ACCESS_ALGORITHM = "HS256"


class MobileTokenError(Exception):
    """모바일 토큰 처리 공통 에러"""


class NotMobileAccessTokenError(MobileTokenError):
    """모바일 Access JWT가 아닌 토큰"""


class InvalidMobileAccessTokenError(MobileTokenError):
    """모바일 Access JWT가 유효하지 않음"""


class InvalidRefreshTokenError(MobileTokenError):
    """Refresh Token이 유효하지 않음"""


@dataclass
class IssuedTokenBundle:
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


def _utcnow() -> datetime:
    # DB 컬럼(DateTime)이 naive UTC를 사용하므로 tzinfo를 제거해 저장한다.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _access_token_ttl_seconds() -> int:
    return int(getattr(settings, "MOBILE_ACCESS_TOKEN_EXPIRES_SECONDS", 7200))


def _refresh_token_ttl_days() -> int:
    return int(getattr(settings, "MOBILE_REFRESH_TOKEN_EXPIRES_DAYS", 30))


def _refresh_token_random_bytes() -> int:
    return int(getattr(settings, "MOBILE_REFRESH_TOKEN_RANDOM_BYTES", 48))


def _hash_refresh_token(raw_token: str) -> str:
    # SECRET_KEY를 pepper로 섞어 DB 유출 시에도 역추적 난이도를 높인다.
    material = f"{settings.SECRET_KEY}:{raw_token}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def _generate_refresh_token() -> str:
    return secrets.token_urlsafe(_refresh_token_random_bytes())


def _build_access_claims(
    user: UserSQL, device_id: str, now: datetime
) -> Dict[str, Any]:
    expires_in = _access_token_ttl_seconds()
    return {
        "iss": MOBILE_ACCESS_ISSUER,
        "typ": "access",
        "sub": str(user.id),
        "user_id": user.id,
        "device_id": device_id,
        "username": user.display_name or user.email,
        "email": user.email,
        "scope": "admin" if user.role.value == "admin" else "user",
        "status": user.status.value,
        "role": user.role.value,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }


def create_mobile_access_token(user: UserSQL, device_id: str) -> tuple[str, int]:
    now = _utcnow()
    claims = _build_access_claims(user=user, device_id=device_id, now=now)
    token = jwt.encode(
        claims,
        settings.SECRET_KEY,
        algorithm=MOBILE_ACCESS_ALGORITHM,
    )
    return token, _access_token_ttl_seconds()


def _create_refresh_token_record(
    db: Session,
    *,
    user_id: int,
    device_id: str,
    now: datetime,
) -> tuple[str, MobileRefreshTokenSQL]:
    raw_refresh = _generate_refresh_token()
    token_row = MobileRefreshTokenSQL(
        user_id=user_id,
        device_id=device_id,
        token_hash=_hash_refresh_token(raw_refresh),
        issued_at=now,
        expires_at=now + timedelta(days=_refresh_token_ttl_days()),
    )
    db.add(token_row)
    db.flush()
    return raw_refresh, token_row


def revoke_active_refresh_tokens_for_device(
    db: Session,
    *,
    user_id: int,
    device_id: str,
    now: Optional[datetime] = None,
) -> None:
    now_utc = now or _utcnow()
    rows = (
        db.query(MobileRefreshTokenSQL)
        .filter(
            MobileRefreshTokenSQL.user_id == user_id,
            MobileRefreshTokenSQL.device_id == device_id,
            MobileRefreshTokenSQL.revoked_at.is_(None),
        )
        .all()
    )
    for row in rows:
        row.revoked_at = now_utc


def issue_mobile_tokens(
    db: Session,
    *,
    user: UserSQL,
    device_id: str,
) -> IssuedTokenBundle:
    now = _utcnow()
    revoke_active_refresh_tokens_for_device(
        db,
        user_id=user.id,
        device_id=device_id,
        now=now,
    )
    refresh_token, _ = _create_refresh_token_record(
        db,
        user_id=user.id,
        device_id=device_id,
        now=now,
    )
    access_token, expires_in = create_mobile_access_token(
        user=user, device_id=device_id
    )
    db.commit()
    return IssuedTokenBundle(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
    )


def rotate_mobile_tokens(
    db: Session,
    *,
    refresh_token: str,
    device_id: str,
) -> tuple[UserSQL, IssuedTokenBundle]:
    now = _utcnow()
    refresh_hash = _hash_refresh_token(refresh_token)
    stored = (
        db.query(MobileRefreshTokenSQL)
        .filter(MobileRefreshTokenSQL.token_hash == refresh_hash)
        .first()
    )
    if not stored:
        raise InvalidRefreshTokenError("Invalid refresh token")

    if stored.device_id != device_id:
        raise InvalidRefreshTokenError("Refresh token does not match device")

    if stored.revoked_at is not None:
        raise InvalidRefreshTokenError("Refresh token has been revoked")

    if stored.expires_at <= now:
        stored.revoked_at = now
        db.commit()
        raise InvalidRefreshTokenError("Refresh token has expired")

    user = db.query(UserSQL).filter(UserSQL.id == stored.user_id).first()
    if not user:
        stored.revoked_at = now
        db.commit()
        raise InvalidRefreshTokenError("User not found for refresh token")

    new_refresh, new_row = _create_refresh_token_record(
        db,
        user_id=user.id,
        device_id=device_id,
        now=now,
    )
    stored.revoked_at = now
    stored.last_used_at = now
    stored.replaced_by_token_id = new_row.id

    access_token, expires_in = create_mobile_access_token(
        user=user, device_id=device_id
    )
    db.commit()
    return user, IssuedTokenBundle(
        access_token=access_token,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=expires_in,
    )


def revoke_refresh_token(
    db: Session,
    *,
    refresh_token: str,
    device_id: str,
) -> None:
    now = _utcnow()
    refresh_hash = _hash_refresh_token(refresh_token)
    stored = (
        db.query(MobileRefreshTokenSQL)
        .filter(MobileRefreshTokenSQL.token_hash == refresh_hash)
        .first()
    )
    if not stored:
        return
    if stored.device_id != device_id:
        raise InvalidRefreshTokenError("Refresh token does not match device")
    if stored.revoked_at is None:
        stored.revoked_at = now
        db.commit()


def revoke_tokens_by_user_and_device(
    db: Session,
    *,
    user_id: int,
    device_id: str,
) -> None:
    revoke_active_refresh_tokens_for_device(db, user_id=user_id, device_id=device_id)
    db.commit()


def decode_mobile_access_token(token: str) -> Dict[str, Any]:
    try:
        unverified = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False},
            algorithms=[MOBILE_ACCESS_ALGORITHM],
        )
    except Exception as e:
        raise NotMobileAccessTokenError(f"Unrecognized JWT format: {e}") from e

    if (
        unverified.get("iss") != MOBILE_ACCESS_ISSUER
        or unverified.get("typ") != "access"
    ):
        raise NotMobileAccessTokenError("Token issuer/type is not mobile access token")

    try:
        verified = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[MOBILE_ACCESS_ALGORITHM],
        )
    except Exception as e:
        raise InvalidMobileAccessTokenError(str(e)) from e

    verified["auth_type"] = "mobile_jwt"
    return verified
