"""
VOJ Audiobooks API - 파일 관리 엔드포인트
파일 업로드, 다운로드, 관리 기능
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Path, Query, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import uuid
import io

from app.core.config import settings
from app.services.storage.factory import storage_service
from app.core.auth.deps import get_current_user_claims, require_any_scope

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
    claims = Depends(require_any_scope(["admin", "editor"]))
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
            detail=f"File size exceeds limit. Maximum allowed: {max_size / (1024*1024):.1f}MB"
        )
    
    # 파일 형식 검증
    allowed_audio_types = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/flac", "audio/aac"]
    allowed_image_types = ["image/jpeg", "image/png", "image/webp"]
    allowed_types = allowed_audio_types + allowed_image_types
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed types: {allowed_types}"
        )
    
    try:
        # 파일 키 생성
        file_id = str(uuid.uuid4())
        prefix = {
            "upload": "uploads",
            "media": "media",
            "cover": "covers"
        }.get(file_type, "uploads")
        
        key = storage_service.generate_key(user_id, book_id, f"{file_id}_{file.filename}", prefix)
        
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
            metadata=metadata
        )
        
        if result.success:
            return FileUploadResponse(
                success=True,
                file_id=file_id,
                key=result.key,
                size=result.size,
                content_type=file.content_type,
                url=result.url,
                message="File uploaded successfully"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {result.error}"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/list", response_model=FileListResponse)
async def list_files(
    prefix: str = Query("", description="파일 키 접두사"),
    limit: int = Query(50, ge=1, le=100, description="최대 개수"),
    claims = Depends(get_current_user_claims)
):
    """파일 목록 조회"""
    try:
        files = await storage_service.list_files(prefix=prefix, limit=limit)
        
        file_responses = []
        for file_info in files:
            file_responses.append(FileInfoResponse(
                key=file_info.key,
                size=file_info.size,
                content_type=file_info.content_type,
                last_modified=file_info.last_modified,
                etag=file_info.etag,
                metadata=file_info.metadata
            ))
        
        return FileListResponse(
            files=file_responses,
            total=len(file_responses)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/info/{file_key:path}", response_model=FileInfoResponse)
async def get_file_info(
    file_key: str = Path(..., description="파일 키"),
    claims = Depends(get_current_user_claims)
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
            metadata=file_info.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{file_key:path}", response_class=StreamingResponse)
async def download_file(
    file_key: str = Path(..., description="파일 키"),
    request: Request = None,
    claims = Depends(get_current_user_claims)
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
        
        # 프로덕션 환경에서는 Pre-signed URL로 리다이렉트
        if settings.ENVIRONMENT == "production":
            download_url = await storage_service.get_download_url(file_key, expires_in=3600)
            if download_url:
                from fastapi.responses import RedirectResponse
                return RedirectResponse(url=download_url)
            else:
                raise HTTPException(status_code=500, detail="Failed to generate download URL")
        
        # 로컬 환경에서는 직접 스트리밍 (Range 지원)
        file_data = await storage_service.download_file(file_key)
        if file_data is None:
            raise HTTPException(status_code=404, detail="File not found")

        file_size = len(file_data)
        # 파일 정보 조회
        file_info = await storage_service.get_file_info(file_key)
        content_type = file_info.content_type if file_info else "application/octet-stream"

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
                    "Accept-Ranges": "bytes",
                }
                return StreamingResponse(io.BytesIO(chunk), status_code=206, media_type=content_type, headers=headers)
            except Exception:
                # Fallback to full content on parse error
                pass

        # Full content
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=content_type,
            headers={
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes",
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{file_key:path}")
async def delete_file(
    file_key: str = Path(..., description="파일 키"),
    claims = Depends(require_any_scope(["admin"]))
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
            raise HTTPException(
                status_code=500,
                detail="Failed to delete file"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/presigned-upload-url")
async def get_presigned_upload_url(
    user_id: str = Query(..., description="사용자 ID"),
    book_id: str = Query(..., description="책 ID"),
    filename: str = Query(..., description="파일명"),
    content_type: str = Query(..., description="Content-Type"),
    file_type: str = Query("upload", description="파일 타입"),
    claims = Depends(require_any_scope(["admin", "editor"]))
):
    """
    Pre-signed 업로드 URL 생성
    - 클라이언트에서 직접 S3에 업로드할 수 있는 URL 제공
    - 프로덕션 환경에서만 사용 가능
    """
    if settings.ENVIRONMENT != "production":
        raise HTTPException(
            status_code=400,
            detail="Pre-signed URLs are only available in production environment"
        )
    
    try:
        # 파일 키 생성
        file_id = str(uuid.uuid4())
        prefix = {
            "upload": "uploads",
            "media": "media", 
            "cover": "covers"
        }.get(file_type, "uploads")
        
        key = storage_service.generate_key(user_id, book_id, f"{file_id}_{filename}", prefix)
        
        # Pre-signed URL 생성
        upload_url = await storage_service.get_upload_url(
            key=key,
            content_type=content_type,
            expires_in=3600  # 1시간
        )
        
        if upload_url:
            return {
                "upload_url": upload_url,
                "key": key,
                "file_id": file_id,
                "expires_in": 3600
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate pre-signed upload URL"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
