"""
간단한 인증 시스템 테스트
"""
import sys
import os
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# 프로젝트 루트를 Python path에 추가
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.core.auth.simple import (
    create_simple_token,
    verify_simple_token,
    authenticate_user,
    get_current_user_claims_simple,
    require_admin_scope,
    get_admin_credentials
)
from app.core.config import settings


class TestSimpleAuth:
    """간단한 인증 시스템 테스트"""

    def test_get_admin_credentials(self):
        """관리자 계정 정보 조회 테스트"""
        credentials = get_admin_credentials()
        
        assert isinstance(credentials, dict)
        assert settings.SIMPLE_AUTH_USERNAME in credentials
        assert credentials[settings.SIMPLE_AUTH_USERNAME] == settings.SIMPLE_AUTH_PASSWORD

    def test_authenticate_user_success(self):
        """사용자 인증 성공 테스트"""
        result = authenticate_user("admin", "admin123")
        assert result is True

    def test_authenticate_user_wrong_password(self):
        """잘못된 비밀번호로 인증 실패 테스트"""
        result = authenticate_user("admin", "wrongpassword")
        assert result is False

    def test_authenticate_user_wrong_username(self):
        """잘못된 사용자명으로 인증 실패 테스트"""
        result = authenticate_user("wronguser", "admin123")
        assert result is False

    def test_create_simple_token(self):
        """토큰 생성 테스트"""
        token = create_simple_token("admin")
        
        assert isinstance(token, str)
        assert "." in token  # payload.signature 형식
        
        # 토큰 구조 확인
        parts = token.split(".")
        assert len(parts) == 2

    def test_verify_simple_token_success(self):
        """토큰 검증 성공 테스트"""
        token = create_simple_token("admin")
        claims = verify_simple_token(token)
        
        assert claims["username"] == "admin"
        assert claims["scope"] == "admin"
        assert "exp" in claims
        assert "iat" in claims
        assert "sub" in claims

    def test_verify_simple_token_invalid_format(self):
        """잘못된 형식의 토큰 검증 테스트"""
        with pytest.raises(ValueError, match="Invalid token format"):
            verify_simple_token("invalid.token.format.extra")

    def test_verify_simple_token_invalid_signature(self):
        """잘못된 서명의 토큰 검증 테스트"""
        token = create_simple_token("admin")
        # 서명 부분을 변조
        payload, _ = token.split(".")
        tampered_token = f"{payload}.tampered_signature"
        
        with pytest.raises(ValueError, match="Invalid signature"):
            verify_simple_token(tampered_token)

    @patch('app.core.auth.simple.time.time')
    def test_verify_simple_token_expired(self, mock_time):
        """만료된 토큰 검증 테스트"""
        # 토큰 생성
        mock_time.return_value = 1000
        token = create_simple_token("admin")
        
        # 시간을 앞으로 이동 (토큰 만료)
        mock_time.return_value = 1000 + 86401  # 24시간 + 1초 후
        
        with pytest.raises(ValueError, match="Token expired"):
            verify_simple_token(token)


class TestGetCurrentUserClaims:
    """현재 사용자 클레임 조회 테스트"""

    @pytest.mark.asyncio
    async def test_get_current_user_claims_with_valid_token(self):
        """유효한 토큰으로 사용자 클레임 조회 테스트"""
        token = create_simple_token("admin")
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        claims = await get_current_user_claims_simple(credentials)
        
        assert claims["username"] == "admin"
        assert claims["scope"] == "admin"

    @pytest.mark.asyncio
    async def test_get_current_user_claims_no_credentials(self):
        """인증 정보 없이 클레임 조회 테스트 (로컬 바이패스)"""
        with patch.object(settings, 'ENVIRONMENT', 'local'), \
             patch.object(settings, 'LOCAL_BYPASS_ENABLED', True):
            
            claims = await get_current_user_claims_simple(None)
            
            assert claims["sub"] == settings.LOCAL_BYPASS_SUB
            assert claims["username"] == settings.LOCAL_BYPASS_USERNAME
            assert claims["scope"] == settings.LOCAL_BYPASS_SCOPE

    @pytest.mark.asyncio
    async def test_get_current_user_claims_invalid_token(self):
        """유효하지 않은 토큰으로 클레임 조회 테스트"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_claims_simple(credentials)
        
        assert exc_info.value.status_code == 401


@pytest.fixture(autouse=True)
def reset_settings():
    """각 테스트 전후로 설정 초기화"""
    original_environment = settings.ENVIRONMENT
    original_bypass_enabled = settings.LOCAL_BYPASS_ENABLED
    
    yield
    
    settings.ENVIRONMENT = original_environment
    settings.LOCAL_BYPASS_ENABLED = original_bypass_enabled
