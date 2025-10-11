"""
VOJ Audiobooks API - Database 설정
SQLAlchemy 데이터베이스 연결 및 세션 관리
"""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 환경에 따른 데이터베이스 URL 설정
_default_sqlite_path = Path(__file__).resolve().parents[3] / "voj_dev.db"  # repo root/voj_dev.db
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:////{_default_sqlite_path}"

# PostgreSQL URL 형식 수정 (Railway는 postgres:// 형식으로 제공)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLAlchemy 엔진 생성
if DATABASE_URL.startswith("sqlite"):
    # SQLite용 설정 (로컬 개발)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL용 설정 (Railway 프로덕션)
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # 연결 상태 자동 체크
        pool_recycle=300,  # 5분마다 연결 재활용
    )

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 베이스 클래스
Base = declarative_base()


# Dependency
def get_db():
    """데이터베이스 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
