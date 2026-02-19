"""
VOJ Audiobooks API - 기본 설정
모든 환경에서 공통으로 사용되는 설정들
"""
import os
from typing import Any, List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings


class BaseAppSettings(BaseSettings):
    """기본 애플리케이션 설정"""

    # 기본 프로젝트 설정
    PROJECT_NAME: str = "VOJ Audiobooks API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "local"
    ENABLE_API_DOCS: bool = False

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # CORS/Hosts 설정
    ALLOWED_HOSTS: List[str] = ["*"]  # TrustedHostMiddleware 용 (호스트만, 스킴 없음)
    CORS_ORIGINS: List[str] = []  # CORSMiddleware 용 (Origin, 스킴 포함)

    @field_validator("ALLOWED_HOSTS", mode="before")
    def parse_allowed_hosts(cls, v: Any) -> List[str]:
        # 지원 형식: 콤마 구분 문자열, JSON 배열 문자열, 리스트
        if isinstance(v, list):
            return [str(item).strip() for item in v]
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    import json

                    arr = json.loads(s)
                    if isinstance(arr, list):
                        return [str(item).strip() for item in arr]
                except Exception:
                    pass
            return [host.strip() for host in s.split(",") if host.strip()]
        return []

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v: Any) -> List[str]:
        # 지원 형식: 콤마 구분 문자열, JSON 배열 문자열, 리스트
        if isinstance(v, list):
            return [str(item).strip() for item in v]
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("[") and s.endswith("]"):
                try:
                    import json

                    arr = json.loads(s)
                    if isinstance(arr, list):
                        return [str(item).strip() for item in arr]
                except Exception:
                    pass
            return [origin.strip() for origin in s.split(",") if origin.strip()]
        return []

    # AWS 기본 설정
    AWS_REGION: str = "ap-northeast-2"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None

    # DynamoDB 기본 설정
    BOOKS_TABLE_NAME: str = "voj-books"
    AUDIO_CHAPTERS_TABLE_NAME: str = "voj-audio-chapters"

    # S3 기본 설정
    S3_BUCKET_NAME: str = "voj-audiobooks"

    # JWT 시크릿 키 (프로덕션에서 반드시 변경 필요)
    SECRET_KEY: str = "INSECURE-local-dev-only-change-me"

    # 간단한 인증 설정
    SIMPLE_AUTH_ENABLED: bool = True
    SIMPLE_AUTH_USERNAME: str = "admin"
    SIMPLE_AUTH_PASSWORD: str = "qwer1234"
    # 앱용 보조 계정 (이메일 계정)
    SIMPLE_AUTH_APP_USERNAME: str = "dev@example.com"
    SIMPLE_AUTH_APP_PASSWORD: str = "qwer1234"

    # Firebase 인증 설정
    FIREBASE_SERVICE_ACCOUNT_JSON: str = ""
    ADMIN_EMAILS: str = ""

    # Telegram Bot 설정
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ADMIN_CHAT_IDS: str = ""  # 콤마 구분 chat ID (관리자 2명)
    TELEGRAM_WEBHOOK_SECRET: str = ""  # Webhook 보안 시크릿

    @property
    def telegram_admin_chat_ids(self) -> List[str]:
        """TELEGRAM_ADMIN_CHAT_IDS를 리스트로 파싱"""
        s = self.TELEGRAM_ADMIN_CHAT_IDS.strip()
        if not s:
            return []
        return [cid.strip() for cid in s.split(",") if cid.strip()]

    @property
    def admin_emails_list(self) -> List[str]:
        """ADMIN_EMAILS 문자열을 리스트로 파싱 (콤마 구분 또는 JSON 배열)"""
        s = self.ADMIN_EMAILS.strip()
        if not s:
            return []
        if s.startswith("[") and s.endswith("]"):
            try:
                import json
                arr = json.loads(s)
                if isinstance(arr, list):
                    return [str(item).strip() for item in arr]
            except Exception:
                pass
        return [e.strip() for e in s.split(",") if e.strip()]

    # 로컬 인증 바이패스 설정
    LOCAL_BYPASS_ENABLED: bool = False
    LOCAL_BYPASS_SUB: str = "local-dev-user-id"
    LOCAL_BYPASS_EMAIL: str = "dev@example.com"
    LOCAL_BYPASS_USERNAME: str = "local.dev"
    LOCAL_BYPASS_SCOPE: str = "admin"
    LOCAL_BYPASS_GROUPS: List[str] = []

    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # pydantic-settings v2
    model_config = {
        "case_sensitive": True,
    }

    def get_table_name(self, base_name: str) -> str:
        """환경에 따른 테이블 이름 생성"""
        if self.ENVIRONMENT == "local":
            return f"{base_name}-local"
        elif self.ENVIRONMENT == "production":
            return f"{base_name}-prod"
        return base_name
