"""
VOJ Audiobooks API - 로컬 개발 환경 설정
로컬 개발 환경에서 사용되는 설정들
"""
from typing import Optional
from pydantic import ConfigDict
from .base import BaseAppSettings


class LocalSettings(BaseAppSettings):
    """로컬 개발 환경 설정"""
    
    # 환경 구분
    ENVIRONMENT: str = "local"
    
    # 개발 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS 설정 (로컬 개발용 - 더 관대한 설정)
    ALLOWED_HOSTS: list = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]
    
    # AWS 설정 (로컬)
    AWS_REGION: str = "ap-northeast-2"
    AWS_ACCESS_KEY_ID: str = "local"
    AWS_SECRET_ACCESS_KEY: str = "local"
    
    # DynamoDB 설정 (로컬)
    DYNAMODB_ENDPOINT_URL: str = "http://localhost:8001"
    BOOKS_TABLE_NAME: str = "voj-books-local"
    AUDIO_CHAPTERS_TABLE_NAME: str = "voj-audio-chapters-local"
    
    # S3 설정 (로컬에서는 사용하지 않음)
    S3_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET_NAME: str = "local-bucket"  # 실제로는 사용하지 않음
    
    # 로컬 스토리지 설정
    LOCAL_STORAGE_PATH: str = "./storage"
    LOCAL_UPLOADS_PATH: str = "./storage/uploads"
    LOCAL_MEDIA_PATH: str = "./storage/media"
    LOCAL_BOOKS_PATH: str = "./storage/books"
    
    # CloudFront 설정 (로컬에서는 사용하지 않음)
    CLOUDFRONT_DOMAIN: Optional[str] = None
    CLOUDFRONT_KEY_PAIR_ID: Optional[str] = None
    CLOUDFRONT_PRIVATE_KEY_PATH: Optional[str] = None
    
    # Cognito 설정 (환경 변수에서 로드)
    # 주의: 로컬 환경에서는 설정이 없을 경우 인증 디펜던시가 BYPASS 모드로 동작합니다.
    # 필요한 경우 .env.local에 COGNITO_* 값을 설정하세요.
    
    # FFmpeg 설정 (macOS Homebrew 기본 경로)
    FFMPEG_PATH: str = "/opt/homebrew/bin/ffmpeg"
    FFPROBE_PATH: str = "/opt/homebrew/bin/ffprobe"
    
    # 로깅 설정 (개발용 - 더 상세한 로그)
    LOG_LEVEL: str = "DEBUG"
    
    # Pydantic v2
    model_config = ConfigDict(case_sensitive=True)
