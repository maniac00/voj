"""
VOJ Audiobooks API - User SQLAlchemy 모델
Firebase 인증 사용자 정보
"""
import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.sql import func

from .database import Base


class UserStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SUSPENDED = "suspended"


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class UserSQL(Base):
    """사용자 모델 - Firebase 인증 연동"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firebase_uid = Column(String(128), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    display_name = Column(String(255), nullable=True)
    photo_url = Column(Text, nullable=True)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING, nullable=False, index=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "firebase_uid": self.firebase_uid,
            "email": self.email,
            "display_name": self.display_name,
            "photo_url": self.photo_url,
            "status": self.status.value if isinstance(self.status, UserStatus) else self.status,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
