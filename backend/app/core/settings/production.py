"""
VOJ Audiobooks API - 프로덕션 환경 설정
AWS 프로덕션 환경에서 사용되는 설정들
"""
import os
from typing import Optional

from pydantic import ConfigDict, model_validator

from .base import BaseAppSettings


class ProductionSettings(BaseAppSettings):
    """프로덕션 환경 설정"""

    # 환경 구분
    ENVIRONMENT: str = "production"

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "ProductionSettings":
        if self.SECRET_KEY == "INSECURE-local-dev-only-change-me":
            raise ValueError(
                "SECRET_KEY must be set to a secure value in production environment. "
                "Set the SECRET_KEY environment variable."
            )
        if self.SIMPLE_AUTH_PASSWORD == "qwer1234":
            raise ValueError(
                "SIMPLE_AUTH_PASSWORD must be changed from the default value in production environment."
            )
        return self

    # 프로덕션 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # Hosts (TrustedHostMiddleware)
    # 주의: 스킴 없이 호스트명만 지정 (Railway + Vercel)
    ALLOWED_HOSTS: list = [
        "voj-audiobooks.vercel.app",
        "*.railway.app",
        "api.voj-audiobook.com",
    ]

    # CORS Origins (CORSMiddleware)
    # 주의: 스킴 포함 Origin 지정
    CORS_ORIGINS: list = [
        "https://voj-audiobooks.vercel.app",
        "https://api.voj-audiobook.com",
    ]

    # 데이터베이스 (Railway: DATABASE_URL 제공)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # AWS/S3/DynamoDB 미사용
    AWS_REGION: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    DYNAMODB_ENDPOINT_URL: Optional[str] = None
    BOOKS_TABLE_NAME: str = ""
    AUDIO_CHAPTERS_TABLE_NAME: str = ""
    S3_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET_NAME: str = ""

    # Railway 퍼시스턴트 볼륨 경로
    LOCAL_STORAGE_PATH: str = "/data/storage"
    LOCAL_UPLOADS_PATH: str = "/data/uploads"
    LOCAL_MEDIA_PATH: str = "/data/media"
    LOCAL_BOOKS_PATH: str = "/data/books"

    # CloudFront/Cognito 미사용
    CLOUDFRONT_DOMAIN: Optional[str] = None
    CLOUDFRONT_KEY_PAIR_ID: Optional[str] = None
    CLOUDFRONT_PRIVATE_KEY_PATH: Optional[str] = None
    CLOUDFRONT_PRIVATE_KEY_SECRET_ID: Optional[str] = None

    COGNITO_USER_POOL_ID: Optional[str] = None
    COGNITO_CLIENT_ID: Optional[str] = None
    COGNITO_CLIENT_SECRET: Optional[str] = None
    COGNITO_REGION: Optional[str] = None
    COGNITO_DOMAIN: Optional[str] = None

    # 로깅 설정 (프로덕션용)
    LOG_LEVEL: str = "INFO"

    # Pydantic v2
    model_config = ConfigDict(case_sensitive=True)
