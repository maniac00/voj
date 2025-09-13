"""
간단한 인증 엔드포인트 테스트
"""
import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.config import settings
from app.core.auth.simple import create_simple_token


class TestAuthEndpoints:
    """인증 엔드포인트 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.client = TestClient(app)
    
    def test_login_success(self):
        """로그인 성공 테스트"""
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 86400
        assert data["username"] == "admin"
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0

    def test_login_invalid_credentials(self):
        """잘못된 인증 정보로 로그인 테스트"""
        test_cases = [
            ("wronguser", "admin123"),
            ("admin", "wrongpassword"),
            ("", "admin123"),
            ("admin", ""),
        ]
        
        for username, password in test_cases:
            response = self.client.post(
                "/api/v1/auth/login",
                json={
                    "username": username,
                    "password": password
                }
            )
            
            assert response.status_code in [401, 422]  # 401 for auth, 422 for validation

    def test_logout_success(self):
        """로그아웃 성공 테스트"""
        response = self.client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    def test_get_current_user_with_valid_token(self):
        """유효한 토큰으로 현재 사용자 정보 조회 테스트"""
        token = create_simple_token("admin")
        
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sub" in data
        assert data["username"] == "admin"
        assert data["scope"] == "admin"

    def test_get_current_user_with_invalid_token(self):
        """유효하지 않은 토큰으로 현재 사용자 정보 조회 테스트"""
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        
        assert response.status_code == 401

    def test_get_current_user_without_token_local_bypass(self):
        """토큰 없이 현재 사용자 정보 조회 테스트 (로컬 바이패스)"""
        with patch.object(settings, 'ENVIRONMENT', 'local'), \
             patch.object(settings, 'LOCAL_BYPASS_ENABLED', True):
            
            response = self.client.get("/api/v1/auth/me")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["sub"] == settings.LOCAL_BYPASS_SUB
            assert data["username"] == settings.LOCAL_BYPASS_USERNAME
            assert data["scope"] == settings.LOCAL_BYPASS_SCOPE


class TestAuthIntegration:
    """인증 통합 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.client = TestClient(app)
    
    def test_full_auth_flow(self):
        """전체 인증 플로우 테스트"""
        # 1. 로그인
        login_response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin",
                "password": "admin123"
            }
        )
        
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 2. 토큰으로 사용자 정보 조회
        user_response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["username"] == "admin"
        
        # 3. 로그아웃
        logout_response = self.client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200

    def test_protected_endpoint_access(self):
        """보호된 엔드포인트 접근 테스트"""
        # 유효한 토큰으로 접근
        token = create_simple_token("admin")
        
        response = self.client.get(
            "/api/v1/books/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 인증은 성공하고, 다른 오류(DB 등)가 있을 수 있음
        assert response.status_code != 401  # 인증 오류가 아님


@pytest.fixture(autouse=True)
def reset_settings():
    """각 테스트 전후로 설정 초기화"""
    original_username = settings.SIMPLE_AUTH_USERNAME
    original_password = settings.SIMPLE_AUTH_PASSWORD
    original_environment = settings.ENVIRONMENT
    original_bypass_enabled = settings.LOCAL_BYPASS_ENABLED
    
    yield
    
    settings.SIMPLE_AUTH_USERNAME = original_username
    settings.SIMPLE_AUTH_PASSWORD = original_password
    settings.ENVIRONMENT = original_environment
    settings.LOCAL_BYPASS_ENABLED = original_bypass_enabled
