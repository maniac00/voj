"""
환경 자동 감지 및 설정 관리
"""
from __future__ import annotations

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from app.core.config import settings


class EnvironmentType(Enum):
    """환경 타입"""
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EnvironmentInfo:
    """환경 정보"""
    type: EnvironmentType
    name: str
    description: str
    features: List[str]
    required_vars: List[str]
    optional_vars: List[str]


class EnvironmentDetector:
    """환경 자동 감지기"""
    
    def __init__(self):
        self.environments = self._define_environments()
    
    def _define_environments(self) -> Dict[EnvironmentType, EnvironmentInfo]:
        """환경 정의"""
        return {
            EnvironmentType.LOCAL: EnvironmentInfo(
                type=EnvironmentType.LOCAL,
                name="로컬 개발",
                description="개발자 로컬 머신에서 실행",
                features=[
                    "DynamoDB Local",
                    "로컬 파일 시스템 스토리지",
                    "즉시 메타데이터 처리",
                    "상세 디버깅 로그",
                    "개발용 빠른 인코딩"
                ],
                required_vars=[
                    "FFMPEG_PATH",
                    "FFPROBE_PATH"
                ],
                optional_vars=[
                    "DYNAMODB_ENDPOINT",
                    "LOCAL_STORAGE_PATH",
                    "LOCAL_BYPASS_ENABLED"
                ]
            ),
            
            EnvironmentType.DEVELOPMENT: EnvironmentInfo(
                type=EnvironmentType.DEVELOPMENT,
                name="개발 서버",
                description="개발팀 공유 개발 서버",
                features=[
                    "실제 DynamoDB",
                    "S3 개발 버킷",
                    "CloudFront 개발 배포",
                    "상세 로깅",
                    "테스트 데이터 허용"
                ],
                required_vars=[
                    "AWS_REGION",
                    "S3_BUCKET_NAME",
                    "DYNAMODB_BOOKS_TABLE",
                    "DYNAMODB_AUDIO_TABLE"
                ],
                optional_vars=[
                    "CLOUDFRONT_DISTRIBUTION_ID",
                    "CLOUDFRONT_DOMAIN"
                ]
            ),
            
            EnvironmentType.STAGING: EnvironmentInfo(
                type=EnvironmentType.STAGING,
                name="스테이징",
                description="프로덕션과 유사한 테스트 환경",
                features=[
                    "프로덕션 유사 설정",
                    "실제 AWS 서비스",
                    "성능 테스트",
                    "보안 테스트",
                    "통합 테스트"
                ],
                required_vars=[
                    "AWS_REGION",
                    "S3_BUCKET_NAME",
                    "DYNAMODB_BOOKS_TABLE",
                    "DYNAMODB_AUDIO_TABLE",
                    "CLOUDFRONT_DISTRIBUTION_ID"
                ],
                optional_vars=[
                    "CLOUDFRONT_KEY_PAIR_ID",
                    "CLOUDFRONT_PRIVATE_KEY_PATH"
                ]
            ),
            
            EnvironmentType.PRODUCTION: EnvironmentInfo(
                type=EnvironmentType.PRODUCTION,
                name="프로덕션",
                description="실제 서비스 운영 환경",
                features=[
                    "고가용성 설정",
                    "보안 강화",
                    "모니터링 활성화",
                    "자동 스케일링",
                    "백업 및 복구"
                ],
                required_vars=[
                    "AWS_REGION",
                    "S3_BUCKET_NAME",
                    "DYNAMODB_BOOKS_TABLE",
                    "DYNAMODB_AUDIO_TABLE",
                    "CLOUDFRONT_DISTRIBUTION_ID",
                    "CLOUDFRONT_KEY_PAIR_ID"
                ],
                optional_vars=[
                    "CLOUDFRONT_PRIVATE_KEY_PATH",
                    "CLOUDWATCH_LOG_GROUP"
                ]
            )
        }
    
    def detect_environment(self) -> EnvironmentType:
        """현재 환경 자동 감지"""
        # 1. 명시적 환경 변수 확인
        env_var = getattr(settings, 'ENVIRONMENT', '').lower()
        
        if env_var == 'production':
            return EnvironmentType.PRODUCTION
        elif env_var == 'staging':
            return EnvironmentType.STAGING
        elif env_var == 'development':
            return EnvironmentType.DEVELOPMENT
        elif env_var == 'local':
            return EnvironmentType.LOCAL
        
        # 2. 환경 변수 존재 여부로 추론
        if self._has_production_indicators():
            return EnvironmentType.PRODUCTION
        elif self._has_staging_indicators():
            return EnvironmentType.STAGING
        elif self._has_development_indicators():
            return EnvironmentType.DEVELOPMENT
        else:
            return EnvironmentType.LOCAL
    
    def _has_production_indicators(self) -> bool:
        """프로덕션 환경 지표 확인"""
        indicators = [
            getattr(settings, 'CLOUDFRONT_KEY_PAIR_ID', None),
            getattr(settings, 'CLOUDFRONT_PRIVATE_KEY_PATH', None),
            os.environ.get('AWS_LAMBDA_FUNCTION_NAME'),  # Lambda 환경
            os.environ.get('ECS_CONTAINER_METADATA_URI')  # ECS 환경
        ]
        
        return any(indicators)
    
    def _has_staging_indicators(self) -> bool:
        """스테이징 환경 지표 확인"""
        staging_patterns = [
            'staging',
            'stage',
            'test',
            'qa'
        ]
        
        # 버킷명이나 테이블명에 스테이징 패턴이 있는지 확인
        bucket_name = getattr(settings, 'S3_BUCKET_NAME', '').lower()
        table_name = getattr(settings, 'DYNAMODB_BOOKS_TABLE', '').lower()
        
        return any(
            pattern in bucket_name or pattern in table_name
            for pattern in staging_patterns
        )
    
    def _has_development_indicators(self) -> bool:
        """개발 환경 지표 확인"""
        return bool(
            getattr(settings, 'AWS_REGION', None) and
            getattr(settings, 'S3_BUCKET_NAME', None) and
            not self._has_production_indicators() and
            not self._has_staging_indicators()
        )
    
    def validate_environment(self, env_type: EnvironmentType) -> Dict[str, Any]:
        """환경 설정 검증"""
        env_info = self.environments[env_type]
        validation_result = {
            "environment": env_type.value,
            "name": env_info.name,
            "description": env_info.description,
            "features": env_info.features,
            "missing_required": [],
            "missing_optional": [],
            "warnings": [],
            "errors": [],
            "is_valid": True
        }
        
        # 필수 환경 변수 확인
        for var_name in env_info.required_vars:
            if not getattr(settings, var_name, None):
                validation_result["missing_required"].append(var_name)
                validation_result["errors"].append(f"Required variable {var_name} is not set")
        
        # 선택적 환경 변수 확인
        for var_name in env_info.optional_vars:
            if not getattr(settings, var_name, None):
                validation_result["missing_optional"].append(var_name)
                validation_result["warnings"].append(f"Optional variable {var_name} is not set")
        
        # 환경별 특수 검증
        if env_type == EnvironmentType.LOCAL:
            validation_result.update(self._validate_local_environment())
        elif env_type == EnvironmentType.PRODUCTION:
            validation_result.update(self._validate_production_environment())
        
        # 전체 유효성 결정
        validation_result["is_valid"] = len(validation_result["missing_required"]) == 0
        
        return validation_result
    
    def _validate_local_environment(self) -> Dict[str, Any]:
        """로컬 환경 특수 검증"""
        local_validation = {"errors": [], "warnings": []}
        
        # FFmpeg 설치 확인
        ffmpeg_path = getattr(settings, 'FFMPEG_PATH', 'ffmpeg')
        try:
            import subprocess
            subprocess.run([ffmpeg_path, '-version'], 
                         capture_output=True, check=True, timeout=5)
        except Exception:
            local_validation["errors"].append(f"FFmpeg not found at {ffmpeg_path}")
        
        # 로컬 스토리지 디렉토리 확인
        storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', './storage')
        if not os.path.exists(storage_path):
            local_validation["warnings"].append(f"Storage directory {storage_path} does not exist")
        
        # DynamoDB Local 확인
        dynamodb_endpoint = getattr(settings, 'DYNAMODB_ENDPOINT', None)
        if dynamodb_endpoint:
            try:
                import requests
                response = requests.get(f"{dynamodb_endpoint}/", timeout=5)
                if response.status_code != 400:  # DynamoDB Local returns 400 for root path
                    local_validation["warnings"].append("DynamoDB Local may not be running")
            except Exception:
                local_validation["warnings"].append("Cannot connect to DynamoDB Local")
        
        return local_validation
    
    def _validate_production_environment(self) -> Dict[str, Any]:
        """프로덕션 환경 특수 검증"""
        prod_validation = {"errors": [], "warnings": []}
        
        # AWS 자격증명 확인
        if not (os.environ.get('AWS_ACCESS_KEY_ID') or os.environ.get('AWS_PROFILE')):
            prod_validation["errors"].append("AWS credentials not configured")
        
        # CloudFront 키 파일 확인
        key_path = getattr(settings, 'CLOUDFRONT_PRIVATE_KEY_PATH', None)
        if key_path and not os.path.exists(key_path):
            prod_validation["errors"].append(f"CloudFront private key not found: {key_path}")
        
        # 보안 설정 확인
        if getattr(settings, 'LOCAL_BYPASS_ENABLED', False):
            prod_validation["warnings"].append("Local bypass is enabled in production")
        
        return prod_validation
    
    def get_environment_recommendations(self, env_type: EnvironmentType) -> List[str]:
        """환경별 권장사항"""
        recommendations = []
        
        if env_type == EnvironmentType.LOCAL:
            recommendations.extend([
                "개발 편의를 위해 상세 로깅을 활성화하세요",
                "DynamoDB Local을 사용하여 AWS 비용을 절약하세요",
                "FFmpeg를 최신 버전으로 유지하세요",
                "로컬 스토리지 디렉토리를 정기적으로 정리하세요"
            ])
        
        elif env_type == EnvironmentType.PRODUCTION:
            recommendations.extend([
                "CloudWatch 모니터링을 설정하세요",
                "S3 버킷에 적절한 라이프사이클 정책을 설정하세요",
                "CloudFront 캐시 정책을 최적화하세요",
                "정기적인 백업 및 복구 테스트를 수행하세요",
                "보안 감사를 정기적으로 실시하세요"
            ])
        
        elif env_type == EnvironmentType.STAGING:
            recommendations.extend([
                "프로덕션과 동일한 설정을 사용하세요",
                "성능 테스트를 정기적으로 수행하세요",
                "보안 스캔을 자동화하세요"
            ])
        
        return recommendations


# 전역 환경 감지기
environment_detector = EnvironmentDetector()


def get_current_environment() -> EnvironmentType:
    """현재 환경 조회 (편의 함수)"""
    return environment_detector.detect_environment()


def validate_current_environment() -> Dict[str, Any]:
    """현재 환경 검증 (편의 함수)"""
    env_type = get_current_environment()
    return environment_detector.validate_environment(env_type)


def get_environment_info(env_type: Optional[EnvironmentType] = None) -> EnvironmentInfo:
    """환경 정보 조회 (편의 함수)"""
    if env_type is None:
        env_type = get_current_environment()
    return environment_detector.environments[env_type]


def get_environment_recommendations(env_type: Optional[EnvironmentType] = None) -> List[str]:
    """환경 권장사항 조회 (편의 함수)"""
    if env_type is None:
        env_type = get_current_environment()
    return environment_detector.get_environment_recommendations(env_type)


def check_environment_readiness() -> Dict[str, Any]:
    """환경 준비 상태 확인"""
    current_env = get_current_environment()
    validation = validate_current_environment()
    recommendations = get_environment_recommendations(current_env)
    
    # 준비 상태 점수 계산
    total_checks = len(validation["missing_required"]) + len(validation["missing_optional"])
    failed_checks = len(validation["missing_required"])
    
    if total_checks == 0:
        readiness_score = 100
    else:
        readiness_score = max(0, 100 - (failed_checks * 50) - (len(validation["missing_optional"]) * 10))
    
    readiness_level = "ready" if readiness_score >= 90 else "warning" if readiness_score >= 70 else "not_ready"
    
    return {
        "environment": current_env.value,
        "readiness_score": readiness_score,
        "readiness_level": readiness_level,
        "validation": validation,
        "recommendations": recommendations,
        "next_steps": _get_next_steps(validation, current_env)
    }


def _get_next_steps(validation: Dict[str, Any], env_type: EnvironmentType) -> List[str]:
    """다음 단계 권장사항"""
    steps = []
    
    if validation["missing_required"]:
        steps.append(f"필수 환경 변수 설정: {', '.join(validation['missing_required'])}")
    
    if env_type == EnvironmentType.LOCAL:
        if "FFMPEG_PATH" in validation["missing_required"]:
            steps.append("FFmpeg 설치: brew install ffmpeg")
        if "DynamoDB Local" in str(validation.get("warnings", [])):
            steps.append("DynamoDB Local 시작: docker-compose up -d dynamodb-local")
    
    elif env_type == EnvironmentType.PRODUCTION:
        if "AWS credentials" in str(validation.get("errors", [])):
            steps.append("AWS 자격증명 설정: aws configure")
        if validation["missing_required"]:
            steps.append("AWS 리소스 생성: CDK 또는 Terraform 배포")
    
    if not steps:
        steps.append("환경 설정이 완료되었습니다. 서비스를 시작할 수 있습니다.")
    
    return steps


# 환경별 기본 설정 생성
def generate_environment_config(env_type: EnvironmentType) -> Dict[str, str]:
    """환경별 기본 설정 생성"""
    base_config = {
        "NODE_ENV": "development" if env_type == EnvironmentType.LOCAL else "production",
        "ENVIRONMENT": env_type.value,
        "AWS_REGION": "ap-northeast-2",
    }
    
    if env_type == EnvironmentType.LOCAL:
        base_config.update({
            "NEXT_PUBLIC_API_URL": "http://localhost:8000",
            "API_PORT": "8000",
            "DYNAMODB_ENDPOINT": "http://localhost:8001",
            "STORAGE_TYPE": "local",
            "LOCAL_STORAGE_PATH": "./storage",
            "FFMPEG_PATH": "/opt/homebrew/bin/ffmpeg",
            "FFPROBE_PATH": "/opt/homebrew/bin/ffprobe",
            "LOCAL_BYPASS_ENABLED": "true",
            "DYNAMODB_BOOKS_TABLE": "voj-books-local",
            "DYNAMODB_AUDIO_TABLE": "voj-audio-chapters-local"
        })
    
    elif env_type == EnvironmentType.PRODUCTION:
        base_config.update({
            "STORAGE_TYPE": "s3",
            "S3_BUCKET_NAME": "voj-audiobooks-prod",
            "CLOUDFRONT_DISTRIBUTION_ID": "E1234567890ABC",
            "DYNAMODB_BOOKS_TABLE": "voj-books-prod",
            "DYNAMODB_AUDIO_TABLE": "voj-audio-chapters-prod",
            "LOCAL_BYPASS_ENABLED": "false"
        })
    
    return base_config


def auto_configure_environment() -> Dict[str, Any]:
    """환경 자동 설정"""
    current_env = get_current_environment()
    validation = validate_current_environment()
    
    auto_config_result = {
        "environment": current_env.value,
        "auto_configured": [],
        "manual_required": [],
        "success": True
    }
    
    try:
        # 환경별 자동 설정 적용
        if current_env == EnvironmentType.LOCAL:
            # 로컬 스토리지 디렉토리 생성
            storage_path = getattr(settings, 'LOCAL_STORAGE_PATH', './storage')
            os.makedirs(storage_path, exist_ok=True)
            os.makedirs(os.path.join(storage_path, 'book'), exist_ok=True)
            auto_config_result["auto_configured"].append(f"Created storage directory: {storage_path}")
            
            # 로그 디렉토리 생성
            log_path = os.path.join(storage_path, 'logs')
            os.makedirs(log_path, exist_ok=True)
            os.makedirs(os.path.join(log_path, 'backups'), exist_ok=True)
            auto_config_result["auto_configured"].append(f"Created log directory: {log_path}")
        
        # 수동 설정이 필요한 항목
        if validation["missing_required"]:
            auto_config_result["manual_required"].extend(validation["missing_required"])
            auto_config_result["success"] = False
        
    except Exception as e:
        auto_config_result["success"] = False
        auto_config_result["error"] = str(e)
    
    return auto_config_result
