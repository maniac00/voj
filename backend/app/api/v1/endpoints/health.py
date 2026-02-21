"""
VOJ Audiobooks API - 헬스 체크 엔드포인트
시스템 상태 및 의존성 상태를 확인하는 엔드포인트
"""
import asyncio
import os
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.auth.simple import get_current_user_claims
from app.core.config import settings
from app.core.environment.detector import (
    auto_configure_environment,
    check_environment_readiness,
    get_current_environment,
    validate_current_environment,
)
from app.services.database import db_service
from app.services.storage.factory import storage_service

router = APIRouter()


class HealthResponse(BaseModel):
    """헬스 체크 응답 모델"""

    status: str
    environment: str
    version: str
    dependencies: Dict[str, Any]


@router.get("", response_model=HealthResponse)
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
        dependencies={},
    )


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health_check():
    """
    상세 헬스 체크
    - API 서버 상태
    - 데이터베이스(PostgreSQL/SQLite) 연결 상태 및 테이블 확인
    - 로컬 스토리지 상태 (로컬 환경)
    """
    dependencies = {}

    # 데이터베이스 연결 및 테이블 상태 확인
    try:
        db_health = await db_service.health_check()
        dependencies["database"] = db_health
    except Exception as e:
        dependencies["database"] = {"status": "unhealthy", "error": str(e)}

    # 로컬 스토리지 확인 (로컬 환경)
    if settings.ENVIRONMENT == "local":
        try:
            # 실제 런타임에서 LocalStorageService가 선택한 base_path를 기준으로 체크
            from app.services.storage.factory import storage_service

            base_path = getattr(
                storage_service,
                "base_path",
                getattr(settings, "LOCAL_STORAGE_PATH", "./storage"),
            )
            storage_paths = [
                base_path,
                os.path.join(base_path, "uploads"),
                os.path.join(base_path, "media"),
                os.path.join(base_path, "books"),
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
                "paths": storage_status,
            }
        except Exception as e:
            dependencies["local_storage"] = {"status": "unhealthy", "error": str(e)}

    # 환경 감지 및 검증
    try:
        current_env = get_current_environment()
        env_validation = validate_current_environment()

        env_status = {
            "detected_environment": current_env.value,
            "is_valid": env_validation["is_valid"],
            "missing_required": env_validation.get("missing_required", []),
            "warnings": env_validation.get("warnings", []),
            "features": env_validation.get("features", []),
        }

        if not env_validation["is_valid"]:
            env_status["status"] = "unhealthy"
        elif env_validation.get("warnings"):
            env_status["status"] = "warning"
        else:
            env_status["status"] = "healthy"

        dependencies["environment"] = env_status
    except Exception as e:
        dependencies["environment"] = {"status": "unhealthy", "error": str(e)}

    # 간단한 인증 설정 확인
    try:
        auth_status = {
            "status": "healthy",
            "auth_type": "simple",
            "username": settings.SIMPLE_AUTH_USERNAME,
            "notes": "하드코딩된 간단한 인증 시스템 사용 중",
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
            "environment": settings.ENVIRONMENT,
        }

        # S3 환경인 경우 추가 상태 확인
        if hasattr(storage_service, "health_check"):
            storage_health = await storage_service.health_check()
            dependencies["storage_service"].update(storage_health)
        else:
            dependencies["storage_service"]["status"] = "healthy"

    except Exception as e:
        dependencies["storage_service"] = {"status": "unhealthy", "error": str(e)}

    # 전체 상태 결정 (프로덕션 초기 배포: 실패 시에도 warning으로 다운그레이드하여 200 응답)
    overall_status = "healthy"
    for dep_name, dep_info in dependencies.items():
        if dep_info.get("status") == "unhealthy":
            overall_status = "warning"
            # 기록은 남기되 5xx로 승격하지 않음
        elif (
            dep_info.get("status") in ["warning", "degraded"]
            and overall_status == "healthy"
        ):
            overall_status = "warning"

    return HealthResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        version="1.0.0",
        dependencies=dependencies,
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
            detail="Database initialization is only allowed in local environment",
        )

    try:
        result = await db_service.initialize()
        return {"message": "Database initialized successfully", "result": result}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Database initialization failed: {str(e)}"
        )


@router.get("/environment")
async def get_environment_info():
    """
    환경 정보 조회
    - 현재 감지된 환경
    - 환경 검증 결과
    - 권장사항
    """
    try:
        readiness_info = check_environment_readiness()
        return readiness_info
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get environment info: {str(e)}"
        )


@router.post("/environment/auto-configure")
async def auto_configure():
    """
    환경 자동 설정
    - 필요한 디렉토리 생성
    - 기본 설정 적용
    - 로컬 환경에서만 지원
    """
    if settings.ENVIRONMENT != "local":
        raise HTTPException(
            status_code=400,
            detail="Auto-configuration is only supported in local environment",
        )

    try:
        result = auto_configure_environment()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Auto-configuration failed: {str(e)}"
        )


_MIGRATION_STATUS_FILE = "/tmp/r2_migration_status.json"


def _run_migration_background(audio_keys: list, local_root: str):
    """백그라운드에서 실행되는 마이그레이션 작업."""
    import json
    import boto3
    from botocore.exceptions import ClientError

    ext_to_ct = {
        ".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4",
        ".flac": "audio/flac", ".aac": "audio/aac", ".ogg": "audio/ogg",
    }

    def content_type(path: str) -> str:
        _, ext = os.path.splitext(path.lower())
        return ext_to_ct.get(ext, "application/octet-stream")

    endpoint = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    s3 = boto3.client(
        "s3", endpoint_url=endpoint, region_name="auto",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    )
    bucket = settings.R2_BUCKET_NAME

    status = {"state": "running", "total": len(audio_keys),
              "ok": 0, "skipped": 0, "failed": 0, "current": 0, "errors": []}

    def _save():
        with open(_MIGRATION_STATUS_FILE, "w") as f:
            json.dump(status, f)

    _save()

    for i, key in enumerate(audio_keys, 1):
        status["current"] = i
        local_path = os.path.join(local_root, key)

        if not os.path.exists(local_path):
            status["skipped"] += 1
            _save()
            continue

        try:
            s3.head_object(Bucket=bucket, Key=key)
            status["skipped"] += 1
            _save()
            continue
        except ClientError as e:
            if e.response["Error"]["Code"] not in ("404", "NoSuchKey"):
                status["failed"] += 1
                status["errors"].append({"key": key, "error": str(e)})
                _save()
                continue

        try:
            with open(local_path, "rb") as f:
                s3.put_object(Bucket=bucket, Key=key, Body=f,
                              ContentType=content_type(local_path))
            status["ok"] += 1
        except Exception as exc:
            status["failed"] += 1
            status["errors"].append({"key": key, "error": str(exc)})

        # 10개마다 상태 저장
        if i % 10 == 0:
            _save()

    status["state"] = "done"
    _save()


@router.post("/migrate-audio-to-r2")
async def migrate_audio_to_r2(
    background_tasks: BackgroundTasks,
    dry_run: bool = Query(False, description="True면 업로드 없이 대상 목록만 반환"),
    claims=Depends(get_current_user_claims),
):
    """
    로컬 볼륨의 오디오 파일을 Cloudflare R2로 백그라운드 마이그레이션 (관리자 전용).
    즉시 반환 후 /health/migrate-audio-to-r2/status 로 진행 상황 확인.
    """
    if str(claims.get("scope", "")).lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    if not settings.R2_ACCOUNT_ID:
        raise HTTPException(status_code=400, detail="R2_ACCOUNT_ID not configured")

    import json
    from app.models.database import SessionLocal
    from app.models.audio_chapter_sql import AudioChapterSQL
    from app.services.storage.local import LocalStorageService

    local_svc = LocalStorageService()
    local_root = local_svc.base_path

    db = SessionLocal()
    try:
        rows = db.query(AudioChapterSQL.audio_key).filter(
            AudioChapterSQL.audio_key.isnot(None)
        ).all()
        audio_keys = [r.audio_key.lstrip("/") for r in rows if r.audio_key]
    finally:
        db.close()

    if dry_run:
        return {"dry_run": True, "total": len(audio_keys),
                "local_root": local_root, "files": audio_keys}

    # 이미 실행 중인지 확인
    import os as _os
    if _os.path.exists(_MIGRATION_STATUS_FILE):
        with open(_MIGRATION_STATUS_FILE) as f:
            prev = json.load(f)
        if prev.get("state") == "running":
            return {"message": "이미 마이그레이션이 실행 중입니다.", "status": prev}

    background_tasks.add_task(_run_migration_background, audio_keys, local_root)
    return {"message": f"마이그레이션 시작 ({len(audio_keys)}개 파일). "
                       "GET /api/v1/health/migrate-audio-to-r2/status 로 진행 상황 확인.",
            "total": len(audio_keys)}


@router.get("/migrate-audio-to-r2/status")
async def migrate_audio_to_r2_status(claims=Depends(get_current_user_claims)):
    """R2 마이그레이션 진행 상황 조회."""
    if str(claims.get("scope", "")).lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    import json
    if not os.path.exists(_MIGRATION_STATUS_FILE):
        return {"state": "not_started"}

    with open(_MIGRATION_STATUS_FILE) as f:
        return json.load(f)


_COVER_MIGRATION_STATUS_FILE = "/tmp/r2_cover_migration_status.json"


def _run_cover_migration_background(cover_keys: list, local_root: str):
    """백그라운드에서 실행되는 커버 이미지 마이그레이션 작업."""
    import json
    import boto3
    from botocore.exceptions import ClientError

    ext_to_ct = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
        ".webp": "image/webp", ".gif": "image/gif",
    }

    def content_type(path: str) -> str:
        _, ext = os.path.splitext(path.lower())
        return ext_to_ct.get(ext, "image/jpeg")

    endpoint = f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
    s3 = boto3.client(
        "s3", endpoint_url=endpoint, region_name="auto",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
    )
    bucket = settings.R2_BUCKET_NAME

    status = {"state": "running", "total": len(cover_keys),
              "ok": 0, "skipped": 0, "failed": 0, "current": 0, "errors": []}

    def _save():
        with open(_COVER_MIGRATION_STATUS_FILE, "w") as f:
            json.dump(status, f)

    _save()

    for i, key in enumerate(cover_keys, 1):
        status["current"] = i
        local_path = os.path.join(local_root, key)

        if not os.path.exists(local_path):
            status["skipped"] += 1
            _save()
            continue

        try:
            s3.head_object(Bucket=bucket, Key=key)
            status["skipped"] += 1
            _save()
            continue
        except ClientError as e:
            if e.response["Error"]["Code"] not in ("404", "NoSuchKey"):
                status["failed"] += 1
                status["errors"].append({"key": key, "error": str(e)})
                _save()
                continue

        try:
            with open(local_path, "rb") as f:
                s3.put_object(Bucket=bucket, Key=key, Body=f,
                              ContentType=content_type(local_path))
            status["ok"] += 1
        except Exception as exc:
            status["failed"] += 1
            status["errors"].append({"key": key, "error": str(exc)})

        if i % 10 == 0:
            _save()

    status["state"] = "done"
    _save()


@router.post("/migrate-covers-to-r2")
async def migrate_covers_to_r2(
    background_tasks: BackgroundTasks,
    dry_run: bool = Query(False, description="True면 업로드 없이 대상 목록만 반환"),
    claims=Depends(get_current_user_claims),
):
    """
    로컬 볼륨의 커버 이미지를 Cloudflare R2로 백그라운드 마이그레이션 (관리자 전용).
    즉시 반환 후 /health/migrate-covers-to-r2/status 로 진행 상황 확인.
    """
    if str(claims.get("scope", "")).lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    if not settings.R2_ACCOUNT_ID:
        raise HTTPException(status_code=400, detail="R2_ACCOUNT_ID not configured")

    import json
    from app.models.database import SessionLocal
    from app.models.book_sql import BookSQL
    from app.services.storage.local import LocalStorageService

    local_svc = LocalStorageService()
    local_root = local_svc.base_path

    db = SessionLocal()
    try:
        rows = db.query(BookSQL.cover_image_key).filter(
            BookSQL.cover_image_key.isnot(None)
        ).all()
        cover_keys = [r.cover_image_key.lstrip("/") for r in rows if r.cover_image_key]
    finally:
        db.close()

    if dry_run:
        return {"dry_run": True, "total": len(cover_keys),
                "local_root": local_root, "files": cover_keys}

    if os.path.exists(_COVER_MIGRATION_STATUS_FILE):
        with open(_COVER_MIGRATION_STATUS_FILE) as f:
            prev = json.load(f)
        if prev.get("state") == "running":
            return {"message": "이미 커버 마이그레이션이 실행 중입니다.", "status": prev}

    background_tasks.add_task(_run_cover_migration_background, cover_keys, local_root)
    return {"message": f"커버 마이그레이션 시작 ({len(cover_keys)}개 파일). "
                       "GET /api/v1/health/migrate-covers-to-r2/status 로 진행 상황 확인.",
            "total": len(cover_keys)}


@router.get("/migrate-covers-to-r2/status")
async def migrate_covers_to_r2_status(claims=Depends(get_current_user_claims)):
    """커버 이미지 R2 마이그레이션 진행 상황 조회."""
    if str(claims.get("scope", "")).lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    import json
    if not os.path.exists(_COVER_MIGRATION_STATUS_FILE):
        return {"state": "not_started"}

    with open(_COVER_MIGRATION_STATUS_FILE) as f:
        return json.load(f)
