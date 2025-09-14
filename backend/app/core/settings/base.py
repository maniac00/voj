"""
VOJ Audiobooks API - 기본 설정
모든 환경에서 공통으로 사용되는 설정들
"""
import os
from typing import List, Optional
from pydantic import field_validator, ConfigDict
from pydantic_settings import BaseSettings


class BaseAppSettings(BaseSettings):
    """기본 애플리케이션 설정"""
    
    # 기본 프로젝트 설정
    PROJECT_NAME: str = "VOJ Audiobooks API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "local"
    
    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS 설정
    ALLOWED_HOSTS: List[str] = ["*"]
    
    @field_validator("ALLOWED_HOSTS", mode="before")
    def assemble_cors_origins(cls, v) -> List[str]:
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    # AWS 기본 설정
    AWS_REGION: str = "ap-northeast-2"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    
    # DynamoDB 기본 설정
    BOOKS_TABLE_NAME: str = "voj-books"
    AUDIO_CHAPTERS_TABLE_NAME: str = "voj-audio-chapters"
    
    # S3 기본 설정
    S3_BUCKET_NAME: str = "voj-audiobooks"
    
    # 간단한 인증 설정
    SIMPLE_AUTH_ENABLED: bool = True
    SIMPLE_AUTH_USERNAME: str = "admin"
    SIMPLE_AUTH_PASSWORD: str = "admin123"
    
    # 로컬 인증 바이패스 설정
    LOCAL_BYPASS_ENABLED: bool = True
    LOCAL_BYPASS_SUB: str = "local-dev-user-id"
    LOCAL_BYPASS_EMAIL: str = "dev@example.com"
    LOCAL_BYPASS_USERNAME: str = "local.dev"
    LOCAL_BYPASS_SCOPE: str = "admin"
    LOCAL_BYPASS_GROUPS: List[str] = []
    
    # FFmpeg 설정
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 인코딩 기능 플래그 (MVP에서는 비활성화)
    ENCODING_ENABLED: bool = False
    
    model_config = ConfigDict(case_sensitive=True)
        
    def get_table_name(self, base_name: str) -> str:
        """환경에 따른 테이블 이름 생성"""
        if self.ENVIRONMENT == "local":
            return f"{base_name}-local"
        elif self.ENVIRONMENT == "production":
            return f"{base_name}-prod"
        return base_name

