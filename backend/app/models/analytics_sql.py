"""
VOJ Audiobooks API - Analytics SQLAlchemy 모델
기기 설치, 재생 진행률, 재생 세션 테이블
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from .database import Base


class DeviceInstallationSQL(Base):
    """기기 설치 기록"""

    __tablename__ = "device_installations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    platform = Column(String(20), nullable=False, default="android")
    os_version = Column(String(50), nullable=True)
    app_version = Column(String(20), nullable=True)
    device_model = Column(String(100), nullable=True)
    first_installed_at = Column(DateTime, default=func.now(), nullable=False)
    last_seen_at = Column(DateTime, default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class PlaybackProgressSQL(Base):
    """재생 진행률 (UPSERT 대상)"""

    __tablename__ = "playback_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "book_id", "chapter_id", name="uq_playback_progress_user_book_chapter"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    book_id = Column(String(255), nullable=False, index=True)
    chapter_id = Column(String(255), nullable=False)
    position_seconds = Column(Integer, default=0, nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    last_played_at = Column(DateTime, default=func.now(), nullable=False)


class PlaybackSessionSQL(Base):
    """재생 세션 (통계용)"""

    __tablename__ = "playback_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(255), nullable=True)
    book_id = Column(String(255), nullable=False, index=True)
    chapter_id = Column(String(255), nullable=False)
    started_at = Column(DateTime, nullable=False, index=True)
    ended_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, default=0, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
