"""
VOJ Audiobooks API - AudioChapter SQLAlchemy 모델
PostgreSQL용 오디오 챕터 모델
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class AudioChapterSQL(Base):
    """오디오 챕터 모델 - PostgreSQL"""

    __tablename__ = "audio_chapters"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign Keys
    book_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)

    # Chapter 정보
    chapter_id = Column(String(255), nullable=False, unique=True, index=True)
    chapter_number = Column(Integer, nullable=False)
    chapter_title = Column(String(200), nullable=True)

    # 오디오 파일 정보
    audio_key = Column(String(500), nullable=False)  # 스토리지 키
    audio_url = Column(Text, nullable=True)  # 접근 URL
    duration = Column(Integer, default=0)  # 초 단위
    file_size = Column(Integer, default=0)  # 바이트 단위
    content_type = Column(String(50), default="audio/mpeg")

    # 메타데이터
    bitrate = Column(Integer, nullable=True)  # kbps
    sample_rate = Column(Integer, nullable=True)  # Hz
    channels = Column(Integer, nullable=True)  # 1=mono, 2=stereo

    # 타임스탬프
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def to_dict(self) -> dict:
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "book_id": self.book_id,
            "user_id": self.user_id,
            "chapter_id": self.chapter_id,
            "chapter_number": self.chapter_number,
            "chapter_title": self.chapter_title,
            "audio_key": self.audio_key,
            "audio_url": self.audio_url,
            "duration": self.duration,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "bitrate": self.bitrate,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
