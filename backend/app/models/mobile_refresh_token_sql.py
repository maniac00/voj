"""
모바일 앱 Refresh Token 저장 모델
- 원문 토큰은 저장하지 않고 SHA-256 해시만 저장
- device_id 단위로 세션을 관리하고 rotation을 지원
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from .database import Base


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class MobileRefreshTokenSQL(Base):
    __tablename__ = "mobile_refresh_tokens"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    device_id = Column(String(255), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)

    issued_at = Column(DateTime, nullable=False, default=_utcnow_naive)
    expires_at = Column(DateTime, nullable=False, index=True)
    last_used_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True, index=True)

    # rotation 체인 추적용 (이전 토큰 -> 신규 토큰)
    replaced_by_token_id = Column(
        Integer,
        ForeignKey("mobile_refresh_tokens.id"),
        nullable=True,
    )
