"""
VOJ Audiobooks API - 헬스 체크 엔드포인트
시스템 상태 및 의존성 상태를 확인하는 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import asyncio
import os

from app.core.config import settings
from app.services.database import db_service
from app.services.storage.factory import storage_service

router = APIRouter()


class HealthResponse(BaseModel):
    """헬스 체크 응답 모델"""
    status: str
    environment: str
    version: str
    dependencies: Dict[str, Any]


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    기본 헬스 체크
    - API 서버 상태 확인
    """
    return HealthResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version="1.0.0",
        dependencies={}
    )


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health_check():
    """
    상세 헬스 체크
    - API 서버 상태
    - DynamoDB 연결 상태 및 테이블 확인
    - 로컬 스토리지 상태 (로컬 환경)
    """
    dependencies = {}
    
    # DynamoDB 연결 및 테이블 상태 확인
    try:
        db_health = await db_service.health_check()
        dependencies["dynamodb"] = db_health
    except Exception as e:
        dependencies["dynamodb"] = {"status": "unhealthy", "error": str(e)}
    
    # 로컬 스토리지 확인 (로컬 환경)
    if settings.ENVIRONMENT == "local":
        try:
            storage_paths = [
                settings.LOCAL_STORAGE_PATH,
                settings.LOCAL_UPLOADS_PATH,
                settings.LOCAL_MEDIA_PATH,
                settings.LOCAL_BOOKS_PATH
            ]
            
            storage_status = {}
            for path in storage_paths:
                if os.path.exists(path):
                    storage_status[path] = "exists"
                else:
                    storage_status[path] = "missing"
            
            all_exist = all(status == "exists" for status in storage_status.values())
            dependencies["local_storage"] = {
                "status": "healthy" if all_exist else "warning",
                "paths": storage_status
            }
        except Exception as e:
            dependencies["local_storage"] = {"status": "unhealthy", "error": str(e)}
    
    # 간단한 인증 설정 확인
    try:
        auth_status = {
            "status": "healthy",
            "auth_type": "simple",
            "username": settings.SIMPLE_AUTH_USERNAME,
            "notes": "하드코딩된 간단한 인증 시스템 사용 중"
        }
        
        if settings.ENVIRONMENT == "production":
            auth_status["notes"] += " (프로덕션에서는 더 강력한 인증 시스템 권장)"
            auth_status["status"] = "warning"
        
        dependencies["auth_config"] = auth_status
    except Exception as e:
        dependencies["auth_config"] = {"status": "unhealthy", "error": str(e)}
    
    # 스토리지 서비스 상태 확인
    try:
        # 스토리지 서비스 타입 확인
        storage_type = type(storage_service).__name__
        dependencies["storage_service"] = {
            "type": storage_type,
            "environment": settings.ENVIRONMENT
        }
        
        # S3 환경인 경우 추가 상태 확인
        if hasattr(storage_service, 'health_check'):
            storage_health = await storage_service.health_check()
            dependencies["storage_service"].update(storage_health)
        else:
            dependencies["storage_service"]["status"] = "healthy"
            
    except Exception as e:
        dependencies["storage_service"] = {"status": "unhealthy", "error": str(e)}
    
    # 전체 상태 결정
    overall_status = "healthy"
    for dep_name, dep_info in dependencies.items():
        if dep_info.get("status") == "unhealthy":
            overall_status = "unhealthy"
            break
        elif dep_info.get("status") in ["warning", "degraded"] and overall_status == "healthy":
            overall_status = "warning"
    
    if overall_status == "unhealthy":
        raise HTTPException(status_code=503, detail="Service dependencies are unhealthy")
    
    return HealthResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        version="1.0.0",
        dependencies=dependencies
    )


@router.post("/init-database")
async def initialize_database():
    """
    데이터베이스 초기화
    - DynamoDB 테이블 생성
    - 개발 환경에서만 사용
    """
    if settings.ENVIRONMENT != "local":
        raise HTTPException(
            status_code=403, 
            detail="Database initialization is only allowed in local environment"
        )
    
    try:
        result = await db_service.initialize()
        return {
            "message": "Database initialized successfully",
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database initialization failed: {str(e)}"
        )
