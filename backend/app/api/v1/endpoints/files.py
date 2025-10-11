"""
VOJ Audiobooks API - 파일 관리 엔드포인트
파일 업로드, 다운로드, 관리 기능
"""
import hashlib
import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException
from fastapi import Path as PathParam
from fastapi import Query, Request, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth.simple import get_current_user_claims, require_any_scope
from app.core.config import settings
from app.models.audio_chapter_sql import AudioChapterSQL
from app.models.database import get_db
from app.services.books_sql import BookServiceSQL as BookService
from app.services.storage.factory import storage_service
from app.utils.audio_validation import extract_chapter_info
from app.utils.ffprobe import extract_audio_metadata

router = APIRouter()


class FileUploadResponse(BaseModel):
    """파일 업로드 응답 모델"""

    success: bool
    file_id: str
    key: str
    size: int
    content_type: str
    url: Optional[str] = None
    message: str


class AudioUploadResponseDto(BaseModel):
    """오디오 업로드 응답 모델"""

    success: bool
    chapter_id: str
    file_id: str
    chapter_number: int
    title: str
    status: str
    message: str
    warnings: Optional[List[str]] = None
    processing_info: Optional[Dict[str, Any]] = None


class FileInfoResponse(BaseModel):
    """파일 정보 응답 모델"""

    key: str
    size: int
    content_type: str
    last_modified: Optional[str]
    etag: Optional[str]
    metadata: Optional[dict]


class FileListResponse(BaseModel):
    """파일 목록 응답 모델"""

    files: List[FileInfoResponse]
    total: int


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Query(..., description="사용자 ID"),
    book_id: str = Query(..., description="책 ID"),
    file_type: str = Query("upload", description="파일 타입 (upload, media, cover)"),
    claims=Depends(require_any_scope(["admin", "editor"])),
    db: Session = Depends(get_db),
):
    """
    파일 업로드
    - 지원 형식: 오디오 파일 (MP3, WAV, M4A, FLAC), 이미지 파일 (JPG, PNG)
    - 파일 크기 제한: 100MB
    """
    # 파일 크기 제한 확인 (100MB)
    max_size = 100 * 1024 * 1024  # 100MB
    file_content = await file.read()

    if len(file_content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds limit. Maximum allowed: {max_size / (1024*1024):.1f}MB",
        )

    # 파일 형식 검증
    # MVP: mp4 컨테이너만 허용 (audio/mp4, audio/x-m4a)
    allowed_audio_types = ["audio/mp4", "audio/x-m4a"]
    allowed_image_types = ["image/jpeg", "image/png", "image/webp"]
    allowed_types = allowed_audio_types + allowed_image_types

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed types: {allowed_types}",
        )

    try:
        # 파일 키 생성
        file_id = str(uuid.uuid4())
        prefix = {"upload": "uploads", "media": "media", "cover": "covers"}.get(
            file_type, "uploads"
        )

        key = storage_service.generate_key(
            user_id, book_id, f"{file_id}_{file.filename}", prefix
        )

        # 메타데이터 준비
        metadata = {
            "original_filename": file.filename,
            "file_id": file_id,
            "user_id": user_id,
            "book_id": book_id,
            "file_type": file_type,
        }

        # 파일 업로드
        result = await storage_service.upload_file(
            file_data=io.BytesIO(file_content),
            key=key,
            content_type=file.content_type,
            metadata=metadata,
        )

        if not result.success:
            raise HTTPException(
                status_code=500, detail=f"File upload failed: {result.error}"
            )

        return FileUploadResponse(
            success=True,
            file_id=file_id,
            key=result.key,
            size=result.size,
            content_type=file.content_type,
            url=result.url,
            message="File uploaded successfully",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/upload/audio", response_model=AudioUploadResponseDto)
async def upload_audio_file(
    file: UploadFile = File(...),
    book_id: str = Query(..., description="책 ID"),
    chapter_title: Optional[str] = Query(None, description="챕터 제목"),
    claims=Depends(require_any_scope(["admin", "editor"])),
    db: "Session" = Depends(get_db) if "get_db" in globals() else None,
):
    """
    오디오 파일 업로드 (AudioChapter 자동 생성)
    - 지원 형식: WAV, MP3, M4A, FLAC
    - 파일 크기 제한: 100MB
    - 자동 메타데이터 추출 (로컬 환경)
    """
    # 파일 크기 제한 확인
    max_size = 100 * 1024 * 1024  # 100MB
    file_content = await file.read()

    if len(file_content) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds limit. Maximum allowed: {max_size / (1024*1024):.1f}MB",
        )

    # MVP: mp4/m4a만 허용 (간단 검증)
    filename = (file.filename or "").lower()
    if not (filename.endswith(".mp4") or filename.endswith(".m4a")):
        raise HTTPException(
            status_code=400, detail="Only .mp4/.m4a files are allowed in MVP"
        )

    try:
        # 사용자 권한 확인 (책 소유권) - 관리자(admin)일 때는 우회 허용
        user_id = str(claims.get("sub") or claims.get("username") or "")
        if db is None:
            raise HTTPException(status_code=500, detail="Database session unavailable")
        is_admin = str(claims.get("scope", "")).lower() == "admin"
        book = (
            BookService.get_book_any_user(db, book_id=book_id)
            if is_admin
            else BookService.get_book(db, user_id=user_id, book_id=book_id)
        )
        if not book:
            raise HTTPException(
                status_code=404, detail="Book not found or access denied"
            )

        # 파일 ID 및 키 생성
        file_id = str(uuid.uuid4())
        key = storage_service.generate_key(
            user_id, book_id, f"{file_id}_{file.filename}", "uploads"
        )

        # 메타데이터 준비
        metadata = {
            "original_filename": file.filename,
            "file_id": file_id,
            "user_id": user_id,
            "book_id": book_id,
            "file_type": "upload",
            "content_type": file.content_type,
        }

        # 파일 업로드
        upload_result = await storage_service.upload_file(
            file_data=io.BytesIO(file_content),
            key=key,
            content_type=file.content_type,
            metadata=metadata,
        )

        if not upload_result.success:
            raise HTTPException(
                status_code=500, detail=f"File upload failed: {upload_result.error}"
            )

        # 파일명에서 챕터 정보 추출
        chapter_info = extract_chapter_info(file.filename or "unknown.mp3")

        # SQL: 현재 최대 chapter_number + 1
        max_num = (
            db.query(func.max(AudioChapterSQL.chapter_number))
            .filter(AudioChapterSQL.book_id == book_id)
            .scalar()
        )
        next_chapter_number = (max_num or 0) + 1
        final_title = (
            chapter_title
            or chapter_info.get("suggested_title")
            or f"Chapter {next_chapter_number}"
        )

        chapter_sql = AudioChapterSQL(
            book_id=book_id,
            user_id=user_id,
            chapter_id=file_id,
            chapter_number=next_chapter_number,
            chapter_title=final_title,
            audio_key=key,
            audio_url=None,
            duration=0,
            file_size=len(file_content),
            content_type=file.content_type,
            bitrate=None,
            sample_rate=44100,
            channels=1,
        )
        db.add(chapter_sql)
        db.commit()

        # 동기화: 책의 총 챕터 수를 실제 개수로 업데이트
        try:
            chapter_count = (
                db.query(func.count(AudioChapterSQL.id))
                .filter(AudioChapterSQL.book_id == book_id)
                .scalar()
            ) or 0
            BookService.update_book_any_user(
                db,
                book_id=book_id,
                total_chapters=int(chapter_count),
            )
        except Exception:
            # 카운트 동기화 실패는 업로드 성공과 분리
            pass

        processing_info: Dict[str, Any] = {
            "encoding_skipped": True,
            "skip_reason": "encoding disabled in MVP",
        }
        return AudioUploadResponseDto(
            success=True,
            chapter_id=file_id,
            file_id=file_id,
            chapter_number=next_chapter_number,
            title=final_title,
            status="ready",
            message=f"Audio file '{file.filename}' uploaded successfully",
            warnings=None,
            processing_info=processing_info,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio upload failed: {str(e)}")


@router.post("/retry-processing/{chapter_id}")
async def retry_audio_processing(
    chapter_id: str = PathParam(..., description="챕터 ID"),
    claims=Depends(require_any_scope(["admin", "editor"])),
    db: Session = Depends(get_db),
):
    """
    오디오 파일 재처리
    - 메타데이터 추출 실패 시 재시도
    - 로컬 환경에서만 지원
    """
    if settings.ENVIRONMENT != "local":
        raise HTTPException(
            status_code=400,
            detail="Audio reprocessing is only supported in local environment",
        )

    try:
        user_id = str(claims.get("sub") or claims.get("username") or "")

        chapter = (
            db.query(AudioChapterSQL)
            .filter(AudioChapterSQL.chapter_id == chapter_id)
            .first()
        )
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")

        is_admin = str(claims.get("scope", "")).lower() == "admin"
        book = (
            BookService.get_book_any_user(db, book_id=chapter.book_id)
            if is_admin
            else BookService.get_book(db, user_id=user_id, book_id=chapter.book_id)
        )
        if not book:
            raise HTTPException(
                status_code=404, detail="Book not found or access denied"
            )

        if not chapter.audio_key:
            raise HTTPException(
                status_code=400, detail="No storage key found for chapter"
            )

        storage_base = getattr(
            storage_service,
            "base_path",
            getattr(settings, "LOCAL_STORAGE_PATH", "./storage"),
        )
        file_path = Path(storage_base) / chapter.audio_key.lstrip("/")
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found on disk")

        try:
            metadata_result = extract_audio_metadata(str(file_path))
        except Exception as meta_error:
            raise HTTPException(
                status_code=500, detail=f"Reprocessing failed: {meta_error}"
            )

        chapter.duration = int(metadata_result.get("duration") or chapter.duration or 0)
        chapter.bitrate = metadata_result.get("bitrate")
        chapter.sample_rate = metadata_result.get("sample_rate")
        chapter.channels = metadata_result.get("channels")
        db.commit()
        db.refresh(chapter)

        return {
            "success": True,
            "chapter_id": chapter_id,
            "status": "ready",
            "message": "Audio reprocessing completed successfully",
            "metadata": metadata_result,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reprocessing failed: {str(e)}")


@router.get("/list", response_model=FileListResponse)
async def list_files(
    prefix: str = Query("", description="파일 키 접두사"),
    limit: int = Query(50, ge=1, le=100, description="최대 개수"),
    claims=Depends(get_current_user_claims),
):
    """파일 목록 조회"""
    try:
        files = await storage_service.list_files(prefix=prefix, limit=limit)

        file_responses = []
        for file_info in files:
            file_responses.append(
                FileInfoResponse(
                    key=file_info.key,
                    size=file_info.size,
                    content_type=file_info.content_type,
                    last_modified=file_info.last_modified,
                    etag=file_info.etag,
                    metadata=file_info.metadata,
                )
            )

        return FileListResponse(files=file_responses, total=len(file_responses))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/info/{file_key:path}", response_model=FileInfoResponse)
async def get_file_info(
    file_key: str = PathParam(..., description="파일 키"),
    claims=Depends(get_current_user_claims),
):
    """파일 정보 조회"""
    try:
        file_info = await storage_service.get_file_info(file_key)

        if file_info is None:
            raise HTTPException(status_code=404, detail="File not found")

        return FileInfoResponse(
            key=file_info.key,
            size=file_info.size,
            content_type=file_info.content_type,
            last_modified=file_info.last_modified,
            etag=file_info.etag,
            metadata=file_info.metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{file_key:path}", response_class=StreamingResponse)
async def download_file(
    file_key: str = PathParam(..., description="파일 키"),
    request: Request = None,
):
    """
    파일 다운로드
    - 로컬 환경: 직접 파일 스트리밍
    - 프로덕션 환경: Pre-signed URL로 리다이렉트
    """
    try:
        # 파일 존재 확인
        if not await storage_service.file_exists(file_key):
            raise HTTPException(status_code=404, detail="File not found")

        # 프로덕션 환경에서도 직접 스트리밍 (CDN 프록시 전제)

        # 로컬 환경에서는 직접 스트리밍 (Range 지원)
        file_data = await storage_service.download_file(file_key)
        if file_data is None:
            raise HTTPException(status_code=404, detail="File not found")

        file_size = len(file_data)
        # 파일 정보 조회
        file_info = await storage_service.get_file_info(file_key)
        content_type = (
            file_info.content_type if file_info else "application/octet-stream"
        )

        # 캐시 헤더 준비
        etag = 'W/"' + hashlib.md5(file_data).hexdigest() + '"'
        last_modified = None
        try:
            if file_info and file_info.last_modified:
                # 기대 포맷: RFC 1123
                last_modified = file_info.last_modified
        except Exception:
            last_modified = None
        if not last_modified:
            last_modified = datetime.now(timezone.utc).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            )
        cache_headers = {
            "ETag": etag,
            "Last-Modified": last_modified,
            "Cache-Control": "public, max-age=0, s-maxage=86400, stale-while-revalidate=600",
            "Accept-Ranges": "bytes",
        }

        range_header = request.headers.get("range") if request else None
        if range_header and range_header.lower().startswith("bytes="):
            # Parse Range: bytes=start-end
            try:
                range_spec = range_header.split("=", 1)[1]
                start_str, end_str = (range_spec.split("-", 1) + [""])[:2]
                start = int(start_str) if start_str else 0
                end = int(end_str) if end_str else file_size - 1
                start = max(0, start)
                end = min(file_size - 1, end)
                if start > end or start >= file_size:
                    # Invalid range
                    return StreamingResponse(
                        io.BytesIO(b""),
                        status_code=416,
                        media_type=content_type,
                        headers={
                            "Content-Range": f"bytes */{file_size}",
                            "Accept-Ranges": "bytes",
                        },
                    )
                chunk = file_data[start : end + 1]
                headers = {
                    "Content-Range": f"bytes {start}-{end}/{file_size}",
                    "Content-Length": str(len(chunk)),
                }
                headers.update(cache_headers)
                return StreamingResponse(
                    io.BytesIO(chunk),
                    status_code=206,
                    media_type=content_type,
                    headers=headers,
                )
            except Exception:
                # Fallback to full content on parse error
                pass

        # Full content
        base_headers = {
            "Content-Length": str(file_size),
        }
        base_headers.update(cache_headers)
        return StreamingResponse(
            io.BytesIO(file_data), media_type=content_type, headers=base_headers
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/{file_key:path}")
async def delete_file(
    file_key: str = PathParam(..., description="파일 키"),
    claims=Depends(require_any_scope(["admin"])),
):
    """파일 삭제"""
    try:
        # 파일 존재 확인
        if not await storage_service.file_exists(file_key):
            raise HTTPException(status_code=404, detail="File not found")

        # 파일 삭제
        success = await storage_service.delete_file(file_key)

        if success:
            return {"message": f"File {file_key} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/presigned-upload-url")
async def get_presigned_upload_url(
    user_id: str = Query(..., description="사용자 ID"),
    book_id: str = Query(..., description="책 ID"),
    filename: str = Query(..., description="파일명"),
    content_type: str = Query(..., description="Content-Type"),
    file_type: str = Query("upload", description="파일 타입"),
    claims=Depends(require_any_scope(["admin", "editor"])),
):
    """
    Pre-signed 업로드 URL 생성
    - 클라이언트에서 직접 S3에 업로드할 수 있는 URL 제공
    - 프로덕션 환경에서만 사용 가능
    """
    if settings.ENVIRONMENT != "production":
        raise HTTPException(
            status_code=400,
            detail="Pre-signed URLs are only available in production environment",
        )

    try:
        # 파일 키 생성
        file_id = str(uuid.uuid4())
        prefix = {"upload": "uploads", "media": "media", "cover": "covers"}.get(
            file_type, "uploads"
        )

        key = storage_service.generate_key(
            user_id, book_id, f"{file_id}_{filename}", prefix
        )

        # Pre-signed URL 생성
        upload_url = await storage_service.get_upload_url(
            key=key, content_type=content_type, expires_in=3600  # 1시간
        )

        if upload_url:
            return {
                "upload_url": upload_url,
                "key": key,
                "file_id": file_id,
                "expires_in": 3600,
            }
        else:
            raise HTTPException(
                status_code=500, detail="Failed to generate pre-signed upload URL"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
