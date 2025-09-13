"""
환경 자동 감지 테스트
"""
import sys
import os
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.config import settings
from app.core.environment.detector import (
    EnvironmentDetector,
    EnvironmentType,
    get_current_environment,
    validate_current_environment,
    check_environment_readiness
)


@pytest.fixture(autouse=True)
def _local_setup():
    """로컬 환경 설정"""
    settings.ENVIRONMENT = "local"
    yield


class TestEnvironmentDetector:
    """환경 감지기 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.detector = EnvironmentDetector()
    
    def test_detect_local_environment(self):
        """로컬 환경 감지 테스트"""
        # 현재 테스트는 로컬 환경에서 실행
        detected_env = self.detector.detect_environment()
        assert detected_env == EnvironmentType.LOCAL
    
    def test_environment_definitions(self):
        """환경 정의 테스트"""
        # 모든 환경이 정의되어 있는지 확인
        for env_type in EnvironmentType:
            assert env_type in self.detector.environments
            
            env_info = self.detector.environments[env_type]
            assert env_info.name
            assert env_info.description
            assert isinstance(env_info.features, list)
            assert isinstance(env_info.required_vars, list)
            assert isinstance(env_info.optional_vars, list)
    
    def test_validate_local_environment(self):
        """로컬 환경 검증 테스트"""
        validation = self.detector.validate_environment(EnvironmentType.LOCAL)
        
        assert validation["environment"] == "local"
        assert "missing_required" in validation
        assert "missing_optional" in validation
        assert "warnings" in validation
        assert "errors" in validation
        assert "is_valid" in validation
        
        print(f"Local environment validation: {validation}")
    
    def test_get_environment_recommendations(self):
        """환경 권장사항 테스트"""
        recommendations = self.detector.get_environment_recommendations(EnvironmentType.LOCAL)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        print(f"Local environment recommendations: {recommendations}")


class TestEnvironmentAPI:
    """환경 관리 API 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.client = TestClient(app)
    
    def test_health_check_with_environment(self):
        """환경 정보가 포함된 헬스체크 테스트"""
        response = self.client.get("/api/v1/health/detailed")
        assert response.status_code in [200, 503]  # 503은 의존성 문제일 수 있음
        
        data = response.json()
        
        assert "dependencies" in data
        dependencies = data["dependencies"]
        
        # 환경 정보 확인
        if "environment" in dependencies:
            env_info = dependencies["environment"]
            assert "detected_environment" in env_info
            assert env_info["detected_environment"] == "local"
            
            print(f"Environment info from health check: {env_info}")
    
    def test_get_environment_info_api(self):
        """환경 정보 API 테스트"""
        response = self.client.get("/api/v1/health/environment")
        assert response.status_code == 200
        
        data = response.json()
        
        assert "environment" in data
        assert data["environment"] == "local"
        assert "readiness_score" in data
        assert "readiness_level" in data
        assert "validation" in data
        assert "recommendations" in data
        assert "next_steps" in data
        
        print(f"Environment readiness: {data}")
    
    def test_auto_configure_api(self):
        """자동 설정 API 테스트"""
        response = self.client.post("/api/v1/health/environment/auto-configure")
        assert response.status_code == 200
        
        data = response.json()
        
        assert "environment" in data
        assert data["environment"] == "local"
        assert "auto_configured" in data
        assert "success" in data
        
        print(f"Auto-configuration result: {data}")


class TestEnvironmentIntegration:
    """환경 통합 테스트"""
    
    def test_current_environment_functions(self):
        """현재 환경 함수들 테스트"""
        # 현재 환경 조회
        current_env = get_current_environment()
        assert current_env == EnvironmentType.LOCAL
        
        # 현재 환경 검증
        validation = validate_current_environment()
        assert validation["environment"] == "local"
        
        # 환경 준비 상태 확인
        readiness = check_environment_readiness()
        assert readiness["environment"] == "local"
        assert "readiness_score" in readiness
        
        print(f"Current environment: {current_env.value}")
        print(f"Readiness score: {readiness['readiness_score']}")
        print(f"Readiness level: {readiness['readiness_level']}")


@pytest.fixture(autouse=True)
def setup_logging():
    """로깅 설정"""
    import logging
    logging.basicConfig(level=logging.INFO)
    yield
