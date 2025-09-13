"""
VOJ Audiobooks API - 인코딩 관리 엔드포인트
인코딩 작업 상태 조회, 관리 기능
"""
from fastapi import APIRouter, HTTPException, Path as PathParam, Query, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import os
from pathlib import Path

from app.core.config import settings
from app.core.auth.simple import get_current_user_claims, require_any_scope
from app.services.encoding.encoding_queue import (
    encoding_queue,
    get_encoding_job_status,
    get_encoding_queue_stats,
    submit_encoding_job,
    EncodingStatus
)
from app.models.audio_chapter import AudioChapter
from app.services.books import BookService
from app.services.encoding.file_manager import file_manager, get_storage_usage
from app.services.encoding.retry_manager import get_retry_stats, clear_failure_history, get_retry_health
from app.services.encoding.environment_config import (
    validate_current_environment,
    get_ffmpeg_command_preview,
    get_performance_tips,
    compare_environment_configs,
    optimize_for_environment
)

router = APIRouter()


class EncodingJobResponse(BaseModel):
    """인코딩 작업 응답 모델"""
    job_id: str
    chapter_id: str
    book_id: str
    status: str
    progress: float = Field(ge=0.0, le=1.0, description="진행률 (0.0 ~ 1.0)")
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Optional[Dict[str, Any]] = None


class EncodingQueueStatsResponse(BaseModel):
    """인코딩 큐 통계 응답 모델"""
    total_jobs: int
    status_counts: Dict[str, int]
    queue_size: int
    workers: int
    avg_processing_time: float
    running: bool


class StartEncodingRequest(BaseModel):
    """인코딩 시작 요청 모델"""
    force_encoding: bool = Field(default=False, description="강제 인코딩 여부")


@router.get("/queue/stats", response_model=EncodingQueueStatsResponse)
async def get_queue_stats(claims = Depends(require_any_scope(["admin"]))):
    """
    인코딩 큐 통계 조회
    - 전체 작업 수, 상태별 개수, 평균 처리 시간 등
    """
    try:
        stats = get_encoding_queue_stats()
        return EncodingQueueStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get queue stats: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=EncodingJobResponse)
async def get_encoding_job(
    job_id: str = PathParam(..., description="작업 ID"),
    claims = Depends(get_current_user_claims)
):
    """
    특정 인코딩 작업 상태 조회
    """
    try:
        job_status = get_encoding_job_status(job_id)
        
        if not job_status:
            raise HTTPException(status_code=404, detail="Encoding job not found")
        
        return EncodingJobResponse(**job_status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.get("/chapters/{chapter_id}/jobs", response_model=List[EncodingJobResponse])
async def get_chapter_encoding_jobs(
    chapter_id: str = PathParam(..., description="챕터 ID"),
    claims = Depends(get_current_user_claims)
):
    """
    특정 챕터의 인코딩 작업 목록 조회
    """
    try:
        jobs = encoding_queue.get_jobs_by_chapter(chapter_id)
        
        return [
            EncodingJobResponse(
                job_id=job.job_id,
                chapter_id=job.chapter_id,
                book_id=job.book_id,
                status=job.status.value,
                progress=job.progress,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
                error_message=job.error_message,
                retry_count=job.retry_count,
                metadata=job.metadata
            )
            for job in jobs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chapter jobs: {str(e)}"
        )


@router.post("/chapters/{chapter_id}/encode")
async def start_chapter_encoding(
    chapter_id: str = PathParam(..., description="챕터 ID"),
    request: StartEncodingRequest = StartEncodingRequest(),
    claims = Depends(require_any_scope(["admin", "editor"]))
):
    """
    챕터 인코딩 시작
    - 기존 인코딩 작업이 있으면 중복 방지
    - 인코딩 필요성 자동 판단 (force_encoding=False인 경우)
    """
    try:
        # 챕터 조회
        chapter = AudioChapter.get_by_id(chapter_id)
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        # 책 소유권 확인
        user_id = str(claims.get("sub") or claims.get("username") or "")
        book = BookService.get_book(user_id=user_id, book_id=chapter.book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found or access denied")
        
        # 파일 경로 확인
        if not chapter.file_info or not chapter.file_info.local_path:
            raise HTTPException(status_code=400, detail="No input file found for encoding")
        
        input_path = chapter.file_info.local_path
        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail="Input file not found on disk")
        
        # 기존 진행 중인 작업 확인
        existing_jobs = encoding_queue.get_jobs_by_chapter(chapter_id)
        active_jobs = [j for j in existing_jobs if j.status in [EncodingStatus.PENDING, EncodingStatus.PROCESSING]]
        
        if active_jobs and not request.force_encoding:
            return {
                "message": "Encoding already in progress",
                "job_id": active_jobs[0].job_id,
                "status": active_jobs[0].status.value
            }
        
        # 인코딩 필요성 확인
        from app.services.encoding.ffmpeg_service import should_encode_file
        should_encode, reason = should_encode_file(input_path, request.force_encoding)
        
        if not should_encode and not request.force_encoding:
            return {
                "message": f"Encoding not required: {reason}",
                "chapter_id": chapter_id,
                "status": "skipped"
            }
        
        # 출력 경로 생성
        import os
        from pathlib import Path
        
        input_file = Path(input_path)
        output_path = str(input_file.parent.parent / "media" / f"{input_file.stem}.m4a")
        
        # 출력 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 인코딩 작업 제출
        job_id = submit_encoding_job(chapter_id, chapter.book_id, input_path, output_path)
        
        # 챕터 상태 업데이트
        chapter.status = "processing"
        chapter.save()
        
        return {
            "success": True,
            "job_id": job_id,
            "chapter_id": chapter_id,
            "message": f"Encoding job started: {reason}",
            "input_path": input_path,
            "output_path": output_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start encoding: {str(e)}"
        )


@router.post("/jobs/{job_id}/retry")
async def retry_encoding_job(
    job_id: str = PathParam(..., description="작업 ID"),
    claims = Depends(require_any_scope(["admin", "editor"]))
):
    """
    인코딩 작업 재시도
    """
    try:
        success = encoding_queue.retry_job(job_id)
        
        if success:
            return {
                "success": True,
                "job_id": job_id,
                "message": "Encoding job retried successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Job cannot be retried (not failed or retry limit exceeded)"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retry job: {str(e)}"
        )


@router.post("/jobs/{job_id}/cancel")
async def cancel_encoding_job(
    job_id: str = PathParam(..., description="작업 ID"),
    claims = Depends(require_any_scope(["admin", "editor"]))
):
    """
    인코딩 작업 취소
    """
    try:
        success = encoding_queue.cancel_job(job_id)
        
        if success:
            return {
                "success": True,
                "job_id": job_id,
                "message": "Encoding job cancelled successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Job cannot be cancelled (not pending)"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/health")
async def get_encoding_health(claims = Depends(require_any_scope(["admin"]))):
    """
    인코딩 시스템 헬스체크
    """
    try:
        from app.services.encoding.encoding_queue import get_encoding_health
        return get_encoding_health()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/storage/stats")
async def get_storage_stats(claims = Depends(require_any_scope(["admin"]))):
    """
    스토리지 사용량 통계 조회
    """
    try:
        usage_stats = get_storage_usage()
        file_stats = file_manager.get_storage_stats()
        
        return {
            "disk_usage": usage_stats,
            "file_stats": file_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get storage stats: {str(e)}"
        )


@router.post("/storage/cleanup")
async def cleanup_storage(
    max_age_hours: int = Query(24, ge=1, le=168, description="정리할 파일의 최대 나이 (시간)"),
    claims = Depends(require_any_scope(["admin"]))
):
    """
    스토리지 정리
    - 오래된 임시 파일 삭제
    - 중복 파일 정리
    """
    try:
        # 오래된 임시 파일 정리
        temp_removed = file_manager.cleanup_old_temp_files(max_age_hours)
        
        # 오래된 인코딩 작업 정리
        jobs_removed = encoding_queue.cleanup_old_jobs(max_age_hours)
        
        return {
            "success": True,
            "temp_files_removed": temp_removed,
            "old_jobs_removed": jobs_removed,
            "max_age_hours": max_age_hours,
            "message": f"Storage cleanup completed"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Storage cleanup failed: {str(e)}"
        )


@router.post("/storage/optimize/{book_id}")
async def optimize_book_storage(
    book_id: str = PathParam(..., description="책 ID"),
    claims = Depends(require_any_scope(["admin"]))
):
    """
    특정 책의 스토리지 최적화
    - 인코딩 완료된 원본 파일 아카이브
    - 불필요한 임시 파일 정리
    """
    try:
        # 책 존재 확인
        user_id = str(claims.get("sub") or claims.get("username") or "")
        book = BookService.get_book(user_id=user_id, book_id=book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found or access denied")
        
        # 스토리지 최적화 실행
        results = file_manager.optimize_storage(book_id)
        
        return {
            "success": True,
            "book_id": book_id,
            "optimization_results": results,
            "message": f"Storage optimization completed for book '{book.title}'"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Storage optimization failed: {str(e)}"
        )


@router.get("/retry/stats")
async def get_retry_statistics(claims = Depends(require_any_scope(["admin"]))):
    """
    재시도 통계 조회
    """
    try:
        retry_stats = get_retry_stats()
        retry_health = get_retry_health()
        
        return {
            "retry_stats": retry_stats,
            "retry_health": retry_health,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get retry stats: {str(e)}"
        )


@router.post("/retry/clear-history")
async def clear_retry_history(
    chapter_id: Optional[str] = Query(None, description="특정 챕터 ID (없으면 전체 정리)"),
    claims = Depends(require_any_scope(["admin"]))
):
    """
    재시도 실패 기록 정리
    """
    try:
        removed_count = clear_failure_history(chapter_id)
        
        return {
            "success": True,
            "removed_count": removed_count,
            "chapter_id": chapter_id,
            "message": f"Cleared {removed_count} failure records"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear retry history: {str(e)}"
        )


@router.post("/jobs/{job_id}/force-retry")
async def force_retry_job(
    job_id: str = PathParam(..., description="작업 ID"),
    ignore_limits: bool = Query(False, description="재시도 제한 무시"),
    claims = Depends(require_any_scope(["admin"]))
):
    """
    강제 재시도 (관리자 전용)
    - 재시도 횟수 제한 무시 가능
    - 실패 기록 초기화
    """
    try:
        job = encoding_queue.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if ignore_limits:
            # 재시도 횟수 초기화
            job.retry_count = 0
            job.error_message = None
            
            # 실패 기록 정리
            clear_failure_history(job.chapter_id)
        
        # 재시도 실행
        success = encoding_queue.retry_job(job_id)
        
        if success:
            return {
                "success": True,
                "job_id": job_id,
                "message": "Job force-retried successfully",
                "ignore_limits": ignore_limits
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Job cannot be retried"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to force retry job: {str(e)}"
        )


@router.get("/config/current")
async def get_current_config(claims = Depends(require_any_scope(["admin"]))):
    """
    현재 환경 설정 조회
    """
    try:
        validation = validate_current_environment()
        ffmpeg_preview = get_ffmpeg_command_preview()
        performance_tips = get_performance_tips()
        
        return {
            "environment_validation": validation,
            "ffmpeg_command_preview": ffmpeg_preview,
            "performance_recommendations": performance_tips,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get current config: {str(e)}"
        )


@router.get("/config/compare")
async def compare_configs(claims = Depends(require_any_scope(["admin"]))):
    """
    환경별 설정 비교
    """
    try:
        comparison = compare_environment_configs()
        return {
            "environment_configs": comparison,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare configs: {str(e)}"
        )


@router.post("/config/optimize")
async def optimize_environment(claims = Depends(require_any_scope(["admin"]))):
    """
    현재 환경에 맞는 최적화 적용
    """
    try:
        optimization_result = optimize_for_environment()
        return optimization_result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to optimize environment: {str(e)}"
        )


@router.get("/config/preview")
async def preview_encoding_command(
    input_file: str = Query("example.mp3", description="예시 입력 파일명"),
    claims = Depends(require_any_scope(["admin"]))
):
    """
    현재 환경의 FFmpeg 명령어 미리보기
    """
    try:
        command = get_ffmpeg_command_preview(input_file)
        
        return {
            "input_file": input_file,
            "ffmpeg_command": command,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to preview command: {str(e)}"
        )
