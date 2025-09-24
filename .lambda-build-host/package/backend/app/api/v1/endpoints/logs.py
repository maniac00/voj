"""
VOJ Audiobooks API - 로그 관리 엔드포인트
로그 백업, 조회, 관리 기능
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import json
import os

from app.core.config import settings
from app.core.auth.simple import get_current_user_claims, require_any_scope

router = APIRouter()


class LogBackupRequest(BaseModel):
    """로그 백업 요청 모델"""
    session_id: str
    session_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    chapter_id: Optional[str] = None
    book_id: Optional[str] = None
    tags: List[str] = []
    logs: List[Dict[str, Any]]


class LogBackupResponse(BaseModel):
    """로그 백업 응답 모델"""
    success: bool
    backup_id: str
    message: str
    backup_path: Optional[str] = None


@router.post("/backup", response_model=LogBackupResponse)
async def backup_logs(
    backup_request: LogBackupRequest,
    claims = Depends(require_any_scope(["admin", "editor"]))
):
    """
    로그 세션 서버 백업
    - 로그 데이터를 서버에 JSON 파일로 저장
    - 로컬 환경에서만 지원
    """
    if settings.ENVIRONMENT != "local":
        raise HTTPException(
            status_code=400,
            detail="Log backup is only supported in local environment"
        )

    try:
        user_id = str(claims.get("sub") or claims.get("username") or "")
        
        # 백업 디렉토리 생성
        backup_dir = os.path.join("./storage", "logs", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # 백업 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"log_backup_{backup_request.session_id}_{timestamp}.json"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        # 백업 데이터 구성
        backup_data = {
            "backup_info": {
                "backup_id": backup_request.session_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user_id,
                "session_name": backup_request.session_name,
                "start_time": backup_request.start_time.isoformat(),
                "end_time": backup_request.end_time.isoformat() if backup_request.end_time else None,
                "chapter_id": backup_request.chapter_id,
                "book_id": backup_request.book_id,
                "tags": backup_request.tags,
                "total_logs": len(backup_request.logs)
            },
            "logs": backup_request.logs
        }
        
        # 파일 저장
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        return LogBackupResponse(
            success=True,
            backup_id=backup_request.session_id,
            message=f"Log session backed up successfully: {backup_filename}",
            backup_path=backup_path if settings.ENVIRONMENT == "local" else None
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Log backup failed: {str(e)}"
        )


@router.get("/backups")
async def list_log_backups(
    limit: int = Query(50, ge=1, le=100),
    claims = Depends(require_any_scope(["admin"]))
):
    """
    저장된 로그 백업 목록 조회
    """
    try:
        backup_dir = os.path.join("./storage", "logs", "backups")
        
        if not os.path.exists(backup_dir):
            return {
                "backups": [],
                "total": 0
            }
        
        backups = []
        
        # 백업 파일들 조회
        for filename in sorted(os.listdir(backup_dir), reverse=True)[:limit]:
            if filename.endswith('.json'):
                file_path = os.path.join(backup_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    
                    backup_info = backup_data.get("backup_info", {})
                    file_stats = os.stat(file_path)
                    
                    backups.append({
                        "filename": filename,
                        "backup_id": backup_info.get("backup_id"),
                        "session_name": backup_info.get("session_name"),
                        "created_at": backup_info.get("created_at"),
                        "total_logs": backup_info.get("total_logs", 0),
                        "file_size": file_stats.st_size,
                        "chapter_id": backup_info.get("chapter_id"),
                        "book_id": backup_info.get("book_id"),
                        "tags": backup_info.get("tags", [])
                    })
                    
                except Exception as e:
                    print(f"Failed to read backup file {filename}: {e}")
                    continue
        
        return {
            "backups": backups,
            "total": len(backups)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.delete("/backups/{backup_filename}")
async def delete_log_backup(
    backup_filename: str,
    claims = Depends(require_any_scope(["admin"]))
):
    """
    로그 백업 파일 삭제
    """
    try:
        backup_dir = os.path.join("./storage", "logs", "backups")
        backup_path = os.path.join(backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="Backup file not found")
        
        # 보안 확인 (경로 순회 공격 방지)
        if not backup_path.startswith(backup_dir):
            raise HTTPException(status_code=400, detail="Invalid backup filename")
        
        os.remove(backup_path)
        
        return {
            "success": True,
            "message": f"Backup {backup_filename} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete backup: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_logs(
    max_age_days: int = Query(30, ge=1, le=365, description="삭제할 로그의 최대 나이 (일)"),
    claims = Depends(require_any_scope(["admin"]))
):
    """
    오래된 로그 백업 정리
    """
    try:
        backup_dir = os.path.join("./storage", "logs", "backups")
        
        if not os.path.exists(backup_dir):
            return {
                "success": True,
                "deleted_count": 0,
                "message": "No backup directory found"
            }
        
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        deleted_count = 0
        
        for filename in os.listdir(backup_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(backup_dir, filename)
                
                try:
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete old backup {filename}: {e}")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "max_age_days": max_age_days,
            "message": f"Deleted {deleted_count} old log backups"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Log cleanup failed: {str(e)}"
        )


@router.get("/stats")
async def get_log_stats(claims = Depends(require_any_scope(["admin"]))):
    """
    로그 시스템 통계
    """
    try:
        from app.services.websocket.log_streamer import get_log_streamer_stats
        
        # WebSocket 로그 스트리머 통계
        streamer_stats = get_log_streamer_stats()
        
        # 백업 파일 통계
        backup_dir = os.path.join("./storage", "logs", "backups")
        backup_stats = {
            "total_backups": 0,
            "total_backup_size": 0,
            "oldest_backup": None,
            "newest_backup": None
        }
        
        if os.path.exists(backup_dir):
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
            backup_stats["total_backups"] = len(backup_files)
            
            if backup_files:
                file_times = []
                total_size = 0
                
                for filename in backup_files:
                    file_path = os.path.join(backup_dir, filename)
                    stat = os.stat(file_path)
                    file_times.append(stat.st_mtime)
                    total_size += stat.st_size
                
                backup_stats.update({
                    "total_backup_size": total_size,
                    "oldest_backup": datetime.fromtimestamp(min(file_times)).isoformat(),
                    "newest_backup": datetime.fromtimestamp(max(file_times)).isoformat()
                })
        
        return {
            "websocket_stats": streamer_stats,
            "backup_stats": backup_stats,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get log stats: {str(e)}"
        )
