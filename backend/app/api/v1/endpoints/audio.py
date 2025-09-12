"""
VOJ Audiobooks API - 오디오 관리 엔드포인트
오디오 파일 업로드, 챕터 관리, 스트리밍 URL 생성
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Path, Query, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid

from app.core.config import settings
from app.core.auth.deps import get_current_user_claims
from app.services.books import BookService
from app.models.audio_chapter import AudioChapter as AudioChapterModel
from app.services.storage.factory import storage_service
import os

router = APIRouter()


class AudioChapterBase(BaseModel):
    """오디오 챕터 기본 정보 모델"""
    chapter_number: int = Field(..., ge=1, description="챕터 번호")
    title: str = Field(..., min_length=1, max_length=200, description="챕터 제목")
    description: Optional[str] = Field(None, max_length=500, description="챕터 설명")


class AudioChapterCreate(AudioChapterBase):
    """오디오 챕터 생성 요청 모델"""
    pass


class AudioChapter(AudioChapterBase):
    """오디오 챕터 응답 모델"""
    chapter_id: str
    book_id: str
    file_name: str
    file_size: int = Field(description="파일 크기(바이트)")
    duration: int = Field(description="재생 시간(초)")
    status: str = Field(default="processing", description="상태: uploading, processing, ready, error")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AudioUploadResponse(BaseModel):
    """오디오 업로드 응답 모델"""
    chapter_id: str
    upload_status: str
    message: str


class StreamingUrlResponse(BaseModel):
    """스트리밍 URL 응답 모델"""
    streaming_url: str
    expires_at: datetime
    duration: int
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


@router.post("/{book_id}/chapters/upload", response_model=AudioUploadResponse)
async def upload_audio_chapter(
    book_id: str = Path(..., description="책 ID"),
    chapter_data: AudioChapterCreate = None,
    audio_file: UploadFile = File(..., description="오디오 파일")
):
    """
    오디오 챕터 파일 업로드
    - 지원 형식: MP3, WAV, M4A, FLAC
    - 파일 크기 제한: 100MB
    - 업로드 후 자동으로 인코딩 처리
    """
    # TODO: 사용자 인증 확인
    # TODO: 책 소유권 확인
    # TODO: 파일 형식 및 크기 검증
    # TODO: S3/로컬 스토리지에 파일 업로드
    # TODO: DynamoDB에 챕터 정보 저장
    # TODO: 인코딩 작업 큐에 추가
    
    # 파일 형식 검증
    allowed_types = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/flac"]
    if audio_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {allowed_types}"
        )
    
    if settings.ENVIRONMENT == "local":
        # 로컬 개발용 더미 응답
        chapter_id = str(uuid.uuid4())
        return AudioUploadResponse(
            chapter_id=chapter_id,
            upload_status="uploaded",
            message=f"Audio file {audio_file.filename} uploaded successfully (local dev mode)"
        )
    
    raise HTTPException(
        status_code=501,
        detail="Audio upload not implemented yet"
    )


@router.get("/{book_id}/chapters", response_model=List[AudioChapter])
async def get_audio_chapters(
    book_id: str = Path(..., description="책 ID"),
    status: Optional[str] = Query(None, description="챕터 상태 필터"),
    claims = Depends(get_current_user_claims)
):
    """
    책의 오디오 챕터 목록 조회
    - 챕터 번호 순으로 정렬
    - 상태별 필터링 가능
    """
    user_id = str(claims.get("sub") or claims.get("cognito:username") or "")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user claims")

    # 책 소유권 확인
    if not BookService.get_book(user_id=user_id, book_id=book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    try:
        # DynamoDB에서 책의 챕터 목록 조회 (챕터 번호 오름차순)
        chapters = list(AudioChapterModel.list_by_book(book_id=book_id, limit=100))
        if status:
            chapters = [c for c in chapters if (c.status or "").lower() == status.lower()]

        # 모델을 응답 모델로 매핑
        results: List[AudioChapter] = []
        for c in chapters:
            file_name = None
            file_size = 0
            duration = 0
            if getattr(c, "file_info", None):
                file_name = c.file_info.original_name if hasattr(c.file_info, "original_name") else None
                file_size = int(c.file_info.file_size) if hasattr(c.file_info, "file_size") and c.file_info.file_size is not None else 0
            if getattr(c, "audio_metadata", None) and hasattr(c.audio_metadata, "duration") and c.audio_metadata.duration is not None:
                duration = int(c.audio_metadata.duration)

            results.append(
                AudioChapter(
                    chapter_id=c.chapter_id,
                    book_id=c.book_id,
                    chapter_number=int(c.chapter_number),
                    title=c.title,
                    description=c.description,
                    file_name=file_name or "",
                    file_size=file_size,
                    duration=duration,
                    status=c.status,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                )
            )

        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list chapters: {str(e)}")


@router.put("/{book_id}/chapters/{chapter_id}", response_model=AudioChapter)
async def update_chapter_order(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID"),
    new_number: int = Query(..., ge=1, description="새로운 챕터 번호"),
    claims = Depends(get_current_user_claims)
):
    """
    오디오 챕터 순서 변경 (chapter_number 업데이트)
    - 사용자 인증 및 소유권 검증
    - 동일 책 내에서 번호만 변경 (충돌 케이스는 단순 교체/중복 허용 없이 overwrite)
    """
    user_id = str(claims.get("sub") or claims.get("cognito:username") or "")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user claims")

    # 책 소유권 확인
    if not BookService.get_book(user_id=user_id, book_id=book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    # 챕터 조회
    chapter = AudioChapterModel.get_by_id(chapter_id)
    if not chapter or chapter.book_id != book_id:
        raise HTTPException(status_code=404, detail="Chapter not found")

    try:
        chapter.chapter_number = new_number
        chapter.save()
        file_name = None
        file_size = 0
        duration = 0
        if getattr(chapter, "file_info", None):
            file_name = chapter.file_info.original_name if hasattr(chapter.file_info, "original_name") else None
            file_size = int(chapter.file_info.file_size) if hasattr(chapter.file_info, "file_size") and chapter.file_info.file_size is not None else 0
        if getattr(chapter, "audio_metadata", None) and hasattr(chapter.audio_metadata, "duration") and chapter.audio_metadata.duration is not None:
            duration = int(chapter.audio_metadata.duration)

        return AudioChapter(
            chapter_id=chapter.chapter_id,
            book_id=chapter.book_id,
            chapter_number=int(chapter.chapter_number),
            title=chapter.title,
            description=chapter.description,
            file_name=file_name or "",
            file_size=file_size,
            duration=duration,
            status=chapter.status,
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update chapter order: {str(e)}")


@router.get("/{book_id}/chapters/{chapter_id}", response_model=AudioChapter)
async def get_audio_chapter(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID")
):
    """
    특정 오디오 챕터 상세 조회
    """
    # TODO: 사용자 인증 확인
    # TODO: 책 소유권 확인
    # TODO: DynamoDB에서 챕터 정보 조회
    
    if settings.ENVIRONMENT == "local":
        # 로컬 개발용 더미 응답
        now = datetime.now(timezone.utc)
        return AudioChapter(
            chapter_id=chapter_id,
            book_id=book_id,
            chapter_number=1,
            title="테스트 챕터",
            description="테스트 챕터의 설명",
            file_name="test_chapter.mp3",
            file_size=1024000,
            duration=1800,
            status="ready",
            created_at=now,
            updated_at=now
        )
    
    raise HTTPException(
        status_code=404,
        detail="Audio chapter not found"
    )


@router.get("/{book_id}/chapters/{chapter_id}/stream", response_model=StreamingUrlResponse)
async def get_streaming_url(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID"),
    claims = Depends(get_current_user_claims)
):
    """
    오디오 챕터 스트리밍 URL 생성
    - 프로덕션: CloudFront Signed URL
    - 로컬: 직접 파일 URL
    """
    # 사용자 인증 및 소유권 확인
    user_id = str(claims.get("sub") or claims.get("cognito:username") or "")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user claims")
    if not BookService.get_book(user_id=user_id, book_id=book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    # 챕터 조회 및 상태 확인
    chapter = AudioChapterModel.get_by_id(chapter_id)
    if not chapter or chapter.book_id != book_id:
        raise HTTPException(status_code=404, detail="Audio chapter not found")

    # 키 결정: s3_key 우선, 없으면 표준 경로 추정(book/<book_id>/media/<filename>)
    key = None
    if getattr(chapter, "file_info", None) and getattr(chapter.file_info, "s3_key", None):
        key = chapter.file_info.s3_key
    elif getattr(chapter, "file_info", None) and getattr(chapter.file_info, "original_name", None):
        key = f"book/{book_id}/media/{chapter.file_info.original_name.replace(' ', '_')}"
    else:
        # 최후의 수단: 챕터 ID 기반 기본 파일명
        key = f"book/{book_id}/media/{chapter.chapter_id}.m4a"

    expires = datetime.now(timezone.utc).replace(hour=23, minute=59, second=59, microsecond=0)

    if settings.ENVIRONMENT == "production":
        # CloudFront Signed URL 우선, 실패 시 S3 Presigned URL
        url = None
        if hasattr(storage_service, "get_cloudfront_signed_url"):
            try:
                url = await storage_service.get_cloudfront_signed_url(key, expires_in=3600)
            except Exception:
                url = None
        if not url:
            url = await storage_service.get_download_url(key, expires_in=3600)
        if not url:
            raise HTTPException(status_code=500, detail="Failed to generate streaming URL")
        return StreamingUrlResponse(streaming_url=url, expires_at=expires, duration=chapter.audio_metadata.duration if getattr(chapter, "audio_metadata", None) else 0)

    # 로컬: Files 다운로드 엔드포인트를 통한 스트리밍 일원화
    local_url = f"http://localhost:{settings.PORT}{settings.API_V1_STR}/files/{key}"
    duration = chapter.audio_metadata.duration if getattr(chapter, "audio_metadata", None) else 0
    return StreamingUrlResponse(streaming_url=local_url, expires_at=expires, duration=duration)


@router.delete("/{book_id}/chapters/{chapter_id}")
async def delete_audio_chapter(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID"),
    claims = Depends(get_current_user_claims)
):
    """
    오디오 챕터 삭제
    - 파일과 메타데이터 모두 삭제
    """
    user_id = str(claims.get("sub") or claims.get("cognito:username") or "")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user claims")

    # 책 소유권 확인
    if not BookService.get_book(user_id=user_id, book_id=book_id):
        raise HTTPException(status_code=404, detail="Book not found")

    chapter = AudioChapterModel.get_by_id(chapter_id)
    if not chapter or chapter.book_id != book_id:
        raise HTTPException(status_code=404, detail="Audio chapter not found")

    # 스토리지 파일 삭제 시도
    try:
        if getattr(chapter, "file_info", None):
            s3_key = getattr(chapter.file_info, "s3_key", None)
            local_path = getattr(chapter.file_info, "local_path", None)
            if s3_key:
                try:
                    await storage_service.delete_file(s3_key)
                except Exception:
                    pass
            if local_path:
                try:
                    if os.path.exists(local_path):
                        os.remove(local_path)
                except Exception:
                    pass
        # 메타데이터/원본 등 추가 키가 있다면 여기서 추가 삭제 가능
    except Exception:
        pass

    # DynamoDB에서 챕터 삭제
    try:
        chapter.delete()
        return {"message": f"Audio chapter {chapter_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete chapter: {str(e)}")

