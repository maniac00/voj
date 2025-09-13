"""
환경별 인코딩 설정 관리
로컬 개발 환경과 AWS 프로덕션 환경에 최적화된 설정 제공
"""
from __future__ import annotations

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings
from app.services.encoding.ffmpeg_service import EncodingConfig


class Environment(Enum):
    """환경 타입"""
    LOCAL = "local"
    PRODUCTION = "production"
    STAGING = "staging"


@dataclass
class EnvironmentEncodingConfig:
    """환경별 인코딩 설정"""
    # FFmpeg 설정
    encoding_config: EncodingConfig
    
    # 큐 설정
    max_workers: int
    max_queue_size: int
    
    # 재시도 설정
    max_retries: int
    base_delay: float
    max_delay: float
    
    # 파일 관리 설정
    cleanup_temp_files_hours: int
    archive_original_files: bool
    
    # 성능 설정
    encoding_timeout: int  # 초
    concurrent_jobs_per_book: int
    
    # 모니터링 설정
    enable_detailed_logging: bool
    enable_metrics: bool


class EnvironmentConfigManager:
    """환경별 설정 관리자"""
    
    def __init__(self):
        self._configs = self._initialize_configs()
        self.current_environment = self._detect_environment()
    
    def _detect_environment(self) -> Environment:
        """현재 환경 감지"""
        env_name = settings.ENVIRONMENT.lower()
        
        if env_name == "production":
            return Environment.PRODUCTION
        elif env_name == "staging":
            return Environment.STAGING
        else:
            return Environment.LOCAL
    
    def _initialize_configs(self) -> Dict[Environment, EnvironmentEncodingConfig]:
        """환경별 설정 초기화"""
        return {
            Environment.LOCAL: self._create_local_config(),
            Environment.PRODUCTION: self._create_production_config(),
            Environment.STAGING: self._create_staging_config()
        }
    
    def _create_local_config(self) -> EnvironmentEncodingConfig:
        """로컬 개발 환경 설정"""
        return EnvironmentEncodingConfig(
            # 개발 편의를 위한 빠른 인코딩 (품질보다 속도 우선)
            encoding_config=EncodingConfig(
                output_format="m4a",
                codec="aac",
                bitrate="64k",  # 로컬에서는 약간 높은 품질
                sample_rate=44100,
                channels=1,
                additional_options=["-movflags", "+faststart", "-preset", "fast"]
            ),
            
            # 로컬 리소스에 맞는 큐 설정
            max_workers=2,  # CPU 코어 수 고려
            max_queue_size=10,
            
            # 빠른 재시도 (개발 중 빠른 피드백)
            max_retries=2,
            base_delay=1.0,
            max_delay=30.0,
            
            # 로컬 스토리지 관리
            cleanup_temp_files_hours=1,  # 1시간 후 정리
            archive_original_files=False,  # 로컬에서는 원본 보관
            
            # 개발 환경 성능 설정
            encoding_timeout=300,  # 5분
            concurrent_jobs_per_book=1,  # 동시 작업 제한
            
            # 개발 중 상세 모니터링
            enable_detailed_logging=True,
            enable_metrics=True
        )
    
    def _create_production_config(self) -> EnvironmentEncodingConfig:
        """AWS 프로덕션 환경 설정"""
        return EnvironmentEncodingConfig(
            # 프로덕션 최적화 인코딩 (대역폭 최적화)
            encoding_config=EncodingConfig(
                output_format="m4a",
                codec="aac",
                bitrate="56k",  # PRD 명세에 따른 최적화
                sample_rate=44100,
                channels=1,
                additional_options=[
                    "-movflags", "+faststart",
                    "-preset", "medium",  # 품질과 속도 균형
                    "-profile:a", "aac_low"
                ]
            ),
            
            # AWS Lambda/ECS 환경에 맞는 큐 설정
            max_workers=4,  # 더 많은 동시 처리
            max_queue_size=100,
            
            # 프로덕션 안정성을 위한 재시도
            max_retries=5,
            base_delay=2.0,
            max_delay=300.0,  # 5분
            
            # 프로덕션 스토리지 관리
            cleanup_temp_files_hours=24,  # 24시간 후 정리
            archive_original_files=True,  # 원본 파일 아카이브
            
            # 프로덕션 성능 설정
            encoding_timeout=1800,  # 30분 (긴 오디오 대응)
            concurrent_jobs_per_book=2,
            
            # 프로덕션 모니터링
            enable_detailed_logging=False,  # 로그 최소화
            enable_metrics=True
        )
    
    def _create_staging_config(self) -> EnvironmentEncodingConfig:
        """스테이징 환경 설정 (프로덕션과 유사하지만 더 관대)"""
        prod_config = self._create_production_config()
        
        # 스테이징에서는 더 상세한 로깅
        prod_config.enable_detailed_logging = True
        prod_config.max_retries = 3
        prod_config.encoding_timeout = 900  # 15분
        
        return prod_config
    
    def get_current_config(self) -> EnvironmentEncodingConfig:
        """현재 환경 설정 조회"""
        return self._configs[self.current_environment]
    
    def get_config_for_environment(self, env: Environment) -> EnvironmentEncodingConfig:
        """특정 환경 설정 조회"""
        return self._configs[env]
    
    def update_config(self, env: Environment, **kwargs) -> None:
        """환경 설정 업데이트"""
        config = self._configs[env]
        
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    def get_encoding_command_preview(self, input_file: str = "input.mp3") -> str:
        """현재 환경의 FFmpeg 명령어 미리보기"""
        config = self.get_current_config()
        
        cmd_parts = [
            settings.FFMPEG_PATH,
            "-y",
            "-i", input_file,
            "-ac", str(config.encoding_config.channels),
            "-ar", str(config.encoding_config.sample_rate),
            "-c:a", config.encoding_config.codec,
            "-b:a", config.encoding_config.bitrate
        ]
        
        if config.encoding_config.additional_options:
            cmd_parts.extend(config.encoding_config.additional_options)
        
        cmd_parts.append(f"output.{config.encoding_config.output_format}")
        
        return " ".join(cmd_parts)
    
    def validate_environment_config(self) -> Dict[str, Any]:
        """현재 환경 설정 검증"""
        config = self.get_current_config()
        issues = []
        warnings = []
        
        # FFmpeg 경로 확인
        import subprocess
        try:
            subprocess.run([settings.FFMPEG_PATH, "-version"], 
                         capture_output=True, check=True, timeout=5)
        except Exception:
            issues.append(f"FFmpeg not found or not working: {settings.FFMPEG_PATH}")
        
        # 워커 수 검증
        if config.max_workers > 8:
            warnings.append(f"High worker count ({config.max_workers}) may cause resource issues")
        
        # 타임아웃 검증
        if config.encoding_timeout < 60:
            warnings.append(f"Short timeout ({config.encoding_timeout}s) may cause failures for long audio")
        
        # 환경별 특정 검증
        if self.current_environment == Environment.LOCAL:
            # 로컬 스토리지 경로 확인
            if not hasattr(settings, 'LOCAL_STORAGE_PATH'):
                issues.append("LOCAL_STORAGE_PATH not configured")
        
        elif self.current_environment == Environment.PRODUCTION:
            # AWS 설정 확인
            aws_configs = ['AWS_REGION', 'S3_BUCKET_NAME']
            for config_name in aws_configs:
                if not getattr(settings, config_name, None):
                    warnings.append(f"{config_name} not configured for production")
        
        return {
            "environment": self.current_environment.value,
            "config": config,
            "issues": issues,
            "warnings": warnings,
            "is_valid": len(issues) == 0
        }
    
    def get_performance_recommendations(self) -> Dict[str, str]:
        """성능 최적화 권장사항"""
        config = self.get_current_config()
        recommendations = {}
        
        if self.current_environment == Environment.LOCAL:
            recommendations.update({
                "workers": f"현재 {config.max_workers}개 워커. CPU 코어 수에 맞게 조정 권장.",
                "bitrate": f"현재 {config.encoding_config.bitrate}. 개발용으로는 적절함.",
                "timeout": f"현재 {config.encoding_timeout}초. 긴 오디오 테스트 시 늘려주세요."
            })
        
        elif self.current_environment == Environment.PRODUCTION:
            recommendations.update({
                "workers": f"현재 {config.max_workers}개 워커. AWS 인스턴스 크기에 맞게 조정.",
                "bitrate": f"현재 {config.encoding_config.bitrate}. 대역폭 최적화됨.",
                "storage": "원본 파일 아카이브 활성화됨. 비용 최적화를 위해 S3 Glacier 고려."
            })
        
        return recommendations


# 전역 환경 설정 관리자
env_config_manager = EnvironmentConfigManager()


def get_current_encoding_config() -> EncodingConfig:
    """현재 환경의 인코딩 설정 조회 (편의 함수)"""
    return env_config_manager.get_current_config().encoding_config


def get_current_environment_config() -> EnvironmentEncodingConfig:
    """현재 환경 설정 조회 (편의 함수)"""
    return env_config_manager.get_current_config()


def validate_current_environment() -> Dict[str, Any]:
    """현재 환경 설정 검증 (편의 함수)"""
    return env_config_manager.validate_environment_config()


def get_ffmpeg_command_preview(input_file: str = "example.mp3") -> str:
    """FFmpeg 명령어 미리보기 (편의 함수)"""
    return env_config_manager.get_encoding_command_preview(input_file)


def get_performance_tips() -> Dict[str, str]:
    """성능 최적화 팁 (편의 함수)"""
    return env_config_manager.get_performance_recommendations()


# 환경별 특수 설정
class EnvironmentSpecificSettings:
    """환경별 특수 설정"""
    
    @staticmethod
    def get_local_settings() -> Dict[str, Any]:
        """로컬 환경 특수 설정"""
        return {
            "storage_type": "local",
            "immediate_processing": True,  # 즉시 처리
            "debug_output": True,
            "preserve_temp_files": True,  # 디버깅용 임시 파일 보관
            "ffmpeg_loglevel": "info"
        }
    
    @staticmethod 
    def get_production_settings() -> Dict[str, Any]:
        """프로덕션 환경 특수 설정"""
        return {
            "storage_type": "s3",
            "immediate_processing": False,  # 큐 기반 처리
            "debug_output": False,
            "preserve_temp_files": False,
            "ffmpeg_loglevel": "error",
            "enable_cloudwatch_metrics": True,
            "s3_storage_class": "STANDARD",
            "cloudfront_invalidation": True
        }
    
    @staticmethod
    def get_staging_settings() -> Dict[str, Any]:
        """스테이징 환경 특수 설정"""
        prod_settings = EnvironmentSpecificSettings.get_production_settings()
        
        # 스테이징에서는 더 관대한 설정
        prod_settings.update({
            "debug_output": True,
            "ffmpeg_loglevel": "info",
            "preserve_temp_files": True
        })
        
        return prod_settings


def get_environment_settings() -> Dict[str, Any]:
    """현재 환경의 특수 설정 조회"""
    env = env_config_manager.current_environment
    
    if env == Environment.LOCAL:
        return EnvironmentSpecificSettings.get_local_settings()
    elif env == Environment.PRODUCTION:
        return EnvironmentSpecificSettings.get_production_settings()
    elif env == Environment.STAGING:
        return EnvironmentSpecificSettings.get_staging_settings()
    else:
        return EnvironmentSpecificSettings.get_local_settings()


# 환경별 최적화 함수
def optimize_for_environment() -> Dict[str, Any]:
    """현재 환경에 맞는 최적화 적용"""
    env = env_config_manager.current_environment
    config = env_config_manager.get_current_config()
    results = {"environment": env.value, "optimizations": []}
    
    try:
        if env == Environment.LOCAL:
            # 로컬 환경 최적화
            results["optimizations"].extend([
                "빠른 인코딩을 위해 'fast' 프리셋 사용",
                "개발 편의를 위해 상세 로깅 활성화",
                "임시 파일 1시간 후 정리",
                "원본 파일 보관 (디버깅용)"
            ])
        
        elif env == Environment.PRODUCTION:
            # 프로덕션 환경 최적화
            results["optimizations"].extend([
                "대역폭 최적화를 위해 56kbps 사용",
                "안정성을 위해 재시도 5회",
                "비용 절약을 위해 원본 파일 아카이브",
                "CloudWatch 메트릭 활성화"
            ])
            
            # AWS 특화 설정
            aws_settings = get_environment_settings()
            if aws_settings.get("enable_cloudwatch_metrics"):
                results["optimizations"].append("CloudWatch 메트릭 수집 활성화")
        
        elif env == Environment.STAGING:
            # 스테이징 환경 최적화
            results["optimizations"].extend([
                "프로덕션과 유사한 설정",
                "테스트를 위한 상세 로깅",
                "중간 수준의 재시도 정책"
            ])
        
        results["success"] = True
        
    except Exception as e:
        results["success"] = False
        results["error"] = str(e)
    
    return results


# 환경 전환 함수 (테스트용)
def switch_environment(target_env: Environment) -> bool:
    """환경 전환 (테스트 및 개발용)"""
    try:
        env_config_manager.current_environment = target_env
        
        # 인코딩 서비스 재설정
        from app.services.encoding.ffmpeg_service import encoding_service
        new_config = env_config_manager.get_current_config().encoding_config
        encoding_service.config = new_config
        
        # 큐 설정 재적용
        from app.services.encoding.encoding_queue import encoding_queue
        new_env_config = env_config_manager.get_current_config()
        encoding_queue.max_workers = new_env_config.max_workers
        
        return True
        
    except Exception as e:
        print(f"Failed to switch environment: {e}")
        return False


# 설정 비교 함수
def compare_environment_configs() -> Dict[str, Any]:
    """환경별 설정 비교"""
    comparison = {}
    
    for env in Environment:
        config = env_config_manager.get_config_for_environment(env)
        comparison[env.value] = {
            "encoding": {
                "bitrate": config.encoding_config.bitrate,
                "channels": config.encoding_config.channels,
                "sample_rate": config.encoding_config.sample_rate,
                "codec": config.encoding_config.codec
            },
            "queue": {
                "max_workers": config.max_workers,
                "max_queue_size": config.max_queue_size
            },
            "retry": {
                "max_retries": config.max_retries,
                "base_delay": config.base_delay
            },
            "performance": {
                "encoding_timeout": config.encoding_timeout,
                "concurrent_jobs_per_book": config.concurrent_jobs_per_book
            }
        }
    
    return comparison
