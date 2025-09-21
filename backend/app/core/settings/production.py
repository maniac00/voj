"""
VOJ Audiobooks API - 프로덕션 환경 설정
AWS 프로덕션 환경에서 사용되는 설정들
"""
import os
from typing import Optional
from pydantic import ConfigDict
from .base import BaseAppSettings


class ProductionSettings(BaseAppSettings):
    """프로덕션 환경 설정"""
    
    # 환경 구분
    ENVIRONMENT: str = "production"
    
    # 프로덕션 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Hosts (TrustedHostMiddleware)
    # 주의: 스킴 없이 호스트명만 지정
    ALLOWED_HOSTS: list = [
        "voj-audiobooks.vercel.app",            # 프론트엔드 도메인
        "d3o89byostp1xs.cloudfront.net",       # CloudFront 도메인
        "*.execute-api.ap-northeast-2.amazonaws.com",  # API Gateway 기본 도메인
        "*.lambda-url.ap-northeast-2.on.aws",  # Lambda Function URL 도메인 (테스트/우회)
        "api.voj-audiobook.com",               # 커스텀 API 도메인(있을 경우)
    ]

    # CORS Origins (CORSMiddleware)
    # 주의: 스킴 포함 Origin 지정
    CORS_ORIGINS: list = [
        "https://voj-audiobooks.vercel.app",
        "https://d3o89byostp1xs.cloudfront.net",
        "https://api.voj-audiobook.com",
    ]
    
    # AWS 설정 (프로덕션 - 환경 변수에서 읽기)
    AWS_REGION: str = "ap-northeast-2"
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    # DynamoDB 설정 (프로덕션)
    DYNAMODB_ENDPOINT_URL: Optional[str] = None  # AWS DynamoDB 사용
    BOOKS_TABLE_NAME: str = "voj-books-prod"
    AUDIO_CHAPTERS_TABLE_NAME: str = "voj-audio-chapters-prod"
    
    # S3 설정 (프로덕션)
    S3_ENDPOINT_URL: Optional[str] = None  # AWS S3 사용
    S3_BUCKET_NAME: str = "voj-audiobooks-prod"
    
    # 로컬 스토리지 설정 (프로덕션에서는 사용하지 않음)
    LOCAL_STORAGE_PATH: str = "/tmp/storage"  # Lambda 임시 디렉토리
    LOCAL_UPLOADS_PATH: str = "/tmp/uploads"
    LOCAL_MEDIA_PATH: str = "/tmp/media"
    LOCAL_BOOKS_PATH: str = "/tmp/books"
    
    # CloudFront 설정 (프로덕션)
    CLOUDFRONT_DOMAIN: str = "d3o89byostp1xs.cloudfront.net"
    CLOUDFRONT_KEY_PAIR_ID: str = "K1MOHSPPL0L417"
    CLOUDFRONT_PRIVATE_KEY_PATH: str = "/opt/keys/voj-private-key.pem"
    CLOUDFRONT_PRIVATE_KEY_SECRET_ID: Optional[str] = os.getenv("CLOUDFRONT_PRIVATE_KEY_SECRET_ID", "voj/prod/cloudfront/privateKey")
    
    # Cognito 설정 (프로덕션 - 환경 변수에서 읽기)
    COGNITO_USER_POOL_ID: Optional[str] = os.getenv("COGNITO_USER_POOL_ID")
    COGNITO_CLIENT_ID: Optional[str] = os.getenv("COGNITO_CLIENT_ID")
    COGNITO_CLIENT_SECRET: Optional[str] = os.getenv("COGNITO_CLIENT_SECRET")
    COGNITO_REGION: str = "ap-northeast-2"
    COGNITO_DOMAIN: Optional[str] = os.getenv("COGNITO_DOMAIN")
    
    # 로깅 설정 (프로덕션용)
    LOG_LEVEL: str = "INFO"
    
    # Pydantic v2
    model_config = ConfigDict(case_sensitive=True)
