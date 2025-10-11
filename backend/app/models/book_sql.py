"""
VOJ Audiobooks API - Book SQLAlchemy 모델
PostgreSQL용 책 정보 모델
"""
import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Integer, String, Text
from sqlalchemy.sql import func

from .database import Base


class BookStatus(str, enum.Enum):
    """책 상태 열거형"""

    DRAFT = "draft"
    PROCESSING = "processing"
    PUBLISHED = "published"
    ERROR = "error"


class BookSQL(Base):
    """책 모델 - PostgreSQL"""

    __tablename__ = "books"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # User & Book IDs
    user_id = Column(String(255), nullable=False, index=True)
    book_id = Column(String(255), nullable=False, unique=True, index=True)

    # 책 기본 정보
    title = Column(String(200), nullable=False, index=True)
    author = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    genre = Column(String(50), nullable=True, index=True)
    language = Column(String(10), default="ko")
    isbn = Column(String(20), nullable=True)
    publisher = Column(String(100), nullable=True)
    published_date = Column(DateTime, nullable=True)

    # 책 상태 및 메타데이터
    status = Column(SQLEnum(BookStatus), default=BookStatus.DRAFT, index=True)
    total_chapters = Column(Integer, default=0)
    total_duration = Column(Integer, default=0)  # 초 단위

    # 파일 정보
    cover_image_url = Column(Text, nullable=True)
    cover_image_key = Column(String(500), nullable=True)

    # 타임스탬프
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def to_dict(self) -> dict:
        """모델을 딕셔너리로 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "description": self.description,
            "genre": self.genre,
            "language": self.language,
            "isbn": self.isbn,
            "publisher": self.publisher,
            "published_date": self.published_date.isoformat()
            if self.published_date
            else None,
            "status": self.status.value
            if isinstance(self.status, BookStatus)
            else self.status,
            "total_chapters": self.total_chapters,
            "total_duration": self.total_duration,
            "cover_image_url": self.cover_image_url,
            "cover_image_key": self.cover_image_key,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
