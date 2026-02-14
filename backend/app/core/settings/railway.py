"""
VOJ Audiobooks API - Railway 프로덕션 설정
Railway 환경에서 사용되는 설정들
"""
import os
from typing import Optional

from pydantic import model_validator

from .base import BaseAppSettings


class RailwaySettings(BaseAppSettings):
    """Railway 프로덕션 설정"""

    ENVIRONMENT: str = "railway"

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "RailwaySettings":
        if self.SECRET_KEY == "INSECURE-local-dev-only-change-me":
            raise ValueError(
                "SECRET_KEY must be set to a secure value in railway environment. "
                "Set the SECRET_KEY environment variable."
            )
        if self.SIMPLE_AUTH_PASSWORD == "qwer1234":
            raise ValueError(
                "SIMPLE_AUTH_PASSWORD must be changed from the default value in railway environment."
            )
        if not self.FIREBASE_SERVICE_ACCOUNT_JSON:
            import logging
            logging.getLogger(__name__).warning(
                "FIREBASE_SERVICE_ACCOUNT_JSON is not set. "
                "Firebase auth endpoints will return 503."
            )
        return self

    # PostgreSQL 설정 (Railway에서 자동 제공)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://localhost/voj")

    # Redis 설정 (옵션)
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)

    # Railway Volumes 스토리지 경로
    RAILWAY_VOLUME_MOUNT_PATH: str = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "/data")
    LOCAL_STORAGE_PATH: str = (
        os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "/data") + "/storage"
    )
    LOCAL_UPLOADS_PATH: str = (
        os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "/data") + "/storage/uploads"
    )
    LOCAL_MEDIA_PATH: str = (
        os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "/data") + "/storage/media"
    )
    LOCAL_BOOKS_PATH: str = (
        os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "/data") + "/storage/books"
    )

    # CORS 설정 - Railway 도메인 허용
    CORS_ORIGINS: list = [
        "https://*.railway.app",
        "https://*.up.railway.app",
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
    ]

    # 프로덕션 보안 설정
    SIMPLE_AUTH_ENABLED: bool = True
    LOCAL_BYPASS_ENABLED: bool = False

    # 로깅 레벨
    LOG_LEVEL: str = "INFO"

    # Railway 환경 변수
    RAILWAY_ENVIRONMENT: str = os.getenv("RAILWAY_ENVIRONMENT", "production")
    RAILWAY_PROJECT_ID: Optional[str] = os.getenv("RAILWAY_PROJECT_ID", None)
    RAILWAY_SERVICE_ID: Optional[str] = os.getenv("RAILWAY_SERVICE_ID", None)

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
