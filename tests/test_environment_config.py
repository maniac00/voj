"""
환경별 인코딩 설정 테스트
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
from app.services.encoding.environment_config import (
    EnvironmentConfigManager,
    Environment,
    get_current_encoding_config,
    validate_current_environment,
    get_ffmpeg_command_preview
)
from app.core.config import settings as app_settings


@pytest.fixture(autouse=True)
def _local_setup():
    """로컬 환경 설정"""
    settings.ENVIRONMENT = "local"
    settings.LOCAL_BYPASS_ENABLED = True
    yield


class TestEnvironmentConfigManager:
    """환경별 설정 관리자 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.config_manager = EnvironmentConfigManager()
    
    def test_detect_environment(self):
        """환경 감지 테스트"""
        # 현재는 로컬로 설정됨
        assert self.config_manager.current_environment == Environment.LOCAL
    
    def test_get_local_config(self):
        """로컬 환경 설정 테스트"""
        local_config = self.config_manager.get_config_for_environment(Environment.LOCAL)
        
        assert local_config.encoding_config.bitrate == "64k"  # 로컬은 약간 높은 품질
        assert local_config.max_workers == 2
        assert local_config.cleanup_temp_files_hours == 1
        assert local_config.enable_detailed_logging is True
        assert local_config.archive_original_files is False
    
    def test_get_production_config(self):
        """프로덕션 환경 설정 테스트"""
        prod_config = self.config_manager.get_config_for_environment(Environment.PRODUCTION)
        
        assert prod_config.encoding_config.bitrate == "56k"  # 프로덕션 최적화
        assert prod_config.max_workers == 4
        assert prod_config.cleanup_temp_files_hours == 24
        assert prod_config.enable_detailed_logging is False
        assert prod_config.archive_original_files is True
        assert prod_config.max_retries == 5
    
    def test_get_current_config(self):
        """현재 환경 설정 조회 테스트"""
        current_config = self.config_manager.get_current_config()
        
        # 로컬 환경이므로 로컬 설정이어야 함
        assert current_config.encoding_config.bitrate == "64k"
        assert current_config.enable_detailed_logging is True
    
    def test_ffmpeg_command_preview(self):
        """FFmpeg 명령어 미리보기 테스트"""
        command = self.config_manager.get_encoding_command_preview("test.mp3")
        
        assert "ffmpeg" in command
        assert "-i test.mp3" in command
        assert "-ac 1" in command  # 모노
        assert "-ar 44100" in command  # 샘플레이트
        assert "-c:a aac" in command  # AAC 코덱
        assert "-b:a 64k" in command  # 로컬 환경 비트레이트
        assert "output.m4a" in command
    
    def test_validate_environment_config(self):
        """환경 설정 검증 테스트"""
        validation = self.config_manager.validate_environment_config()
        
        assert "environment" in validation
        assert validation["environment"] == "local"
        assert "config" in validation
        assert "issues" in validation
        assert "warnings" in validation
        assert "is_valid" in validation
        
        print(f"Validation result: {validation}")


@pytest.mark.skipif(getattr(app_settings, 'ENCODING_ENABLED', False) is False, reason="Encoding disabled in MVP")
class TestEnvironmentConfigAPI:
    """환경별 설정 API 테스트"""
    
    def setup_method(self):
        """각 테스트 전 설정"""
        self.client = TestClient(app)
    
    def test_get_current_config_api(self):
        """현재 환경 설정 API 테스트"""
        response = self.client.get("/api/v1/encoding/config/current")
        assert response.status_code == 200
        
        data = response.json()
        
        assert "environment_validation" in data
        assert "ffmpeg_command_preview" in data
        assert "performance_recommendations" in data
        
        print(f"Current config: {data}")
    
    def test_compare_configs_api(self):
        """환경별 설정 비교 API 테스트"""
        response = self.client.get("/api/v1/encoding/config/compare")
        assert response.status_code == 200
        
        data = response.json()
        
        assert "environment_configs" in data
        configs = data["environment_configs"]
        
        assert "local" in configs
        assert "production" in configs
        assert "staging" in configs
        
        # 로컬과 프로덕션 설정 차이 확인
        local_bitrate = configs["local"]["encoding"]["bitrate"]
        prod_bitrate = configs["production"]["encoding"]["bitrate"]
        
        assert local_bitrate == "64k"
        assert prod_bitrate == "56k"
        
        print(f"Config comparison: {configs}")
    
    def test_optimize_environment_api(self):
        """환경 최적화 API 테스트"""
        response = self.client.post("/api/v1/encoding/config/optimize")
        assert response.status_code == 200
        
        data = response.json()
        
        assert "environment" in data
        assert data["environment"] == "local"
        assert "optimizations" in data
        assert "success" in data
        
        print(f"Optimization result: {data}")
    
    def test_preview_encoding_command_api(self):
        """FFmpeg 명령어 미리보기 API 테스트"""
        response = self.client.get("/api/v1/encoding/config/preview?input_file=sample.mp3")
        assert response.status_code == 200
        
        data = response.json()
        
        assert data["input_file"] == "sample.mp3"
        assert "ffmpeg_command" in data
        assert data["environment"] == "local"
        
        # 로컬 환경 명령어 확인
        command = data["ffmpeg_command"]
        assert "-b:a 64k" in command  # 로컬 환경 비트레이트
        assert "-preset fast" in command  # 로컬 환경 빠른 프리셋
        
        print(f"FFmpeg command preview: {command}")


class TestEnvironmentSpecificBehavior:
    """환경별 특수 동작 테스트"""
    
    def test_local_environment_settings(self):
        """로컬 환경 특수 설정 테스트"""
        from app.services.encoding.environment_config import get_environment_settings
        
        settings_dict = get_environment_settings()
        
        assert settings_dict["storage_type"] == "local"
        assert settings_dict["immediate_processing"] is True
        assert settings_dict["debug_output"] is True
        assert settings_dict["preserve_temp_files"] is True
    
    def test_encoding_config_application(self):
        """인코딩 설정 적용 테스트"""
        encoding_config = get_current_encoding_config()
        
        # 로컬 환경 설정 확인
        assert encoding_config.bitrate == "64k"
        assert encoding_config.channels == 1
        assert encoding_config.sample_rate == 44100
        assert encoding_config.codec == "aac"
        assert encoding_config.output_format == "m4a"
        
        # 로컬 환경 추가 옵션 확인
        assert "-preset" in encoding_config.additional_options
        assert "fast" in encoding_config.additional_options
    
    def test_environment_validation(self):
        """환경 검증 테스트"""
        validation_result = validate_current_environment()
        
        assert validation_result["environment"] == "local"
        assert isinstance(validation_result["is_valid"], bool)
        assert isinstance(validation_result["issues"], list)
        assert isinstance(validation_result["warnings"], list)
        
        # FFmpeg 설치되어 있으면 유효해야 함
        if validation_result["is_valid"]:
            assert len(validation_result["issues"]) == 0
        
        print(f"Environment validation: {validation_result}")
    
    def test_ffmpeg_command_generation(self):
        """FFmpeg 명령어 생성 테스트"""
        command = get_ffmpeg_command_preview("test_audio.mp3")
        
        # 기본 구조 확인
        assert command.startswith(settings.FFMPEG_PATH)
        assert "-i test_audio.mp3" in command
        assert "output.m4a" in command
        
        # 로컬 환경 특정 설정 확인
        assert "-b:a 64k" in command
        assert "-preset fast" in command
        
        print(f"Generated command: {command}")


@pytest.fixture(autouse=True)
def setup_logging():
    """로깅 설정"""
    import logging
    logging.basicConfig(level=logging.INFO)
    yield
