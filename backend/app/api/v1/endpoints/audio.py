"""
VOJ Audiobooks API - 오디오 관리 엔드포인트
오디오 파일 업로드, 챕터 관리, 스트리밍 URL 생성
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Path, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from app.core.config import settings

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
    status: Optional[str] = Query(None, description="챕터 상태 필터")
):
    """
    책의 오디오 챕터 목록 조회
    - 챕터 번호 순으로 정렬
    - 상태별 필터링 가능
    """
    # TODO: 사용자 인증 확인
    # TODO: 책 소유권 확인
    # TODO: DynamoDB에서 챕터 목록 조회
    
    if settings.ENVIRONMENT == "local":
        # 로컬 개발용 더미 응답
        now = datetime.utcnow()
        dummy_chapters = [
            AudioChapter(
                chapter_id=f"chapter_{i}",
                book_id=book_id,
                chapter_number=i,
                title=f"챕터 {i}",
                description=f"챕터 {i}의 설명",
                file_name=f"chapter_{i}.mp3",
                file_size=1024000,
                duration=1800,  # 30분
                status="ready",
                created_at=now,
                updated_at=now
            )
            for i in range(1, 4)
        ]
        
        return dummy_chapters
    
    raise HTTPException(
        status_code=501,
        detail="Audio chapters listing not implemented yet"
    )


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
        now = datetime.utcnow()
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
    chapter_id: str = Path(..., description="챕터 ID")
):
    """
    오디오 챕터 스트리밍 URL 생성
    - 프로덕션: CloudFront Signed URL
    - 로컬: 직접 파일 URL
    """
    # TODO: 사용자 인증 확인
    # TODO: 책 소유권 확인
    # TODO: 챕터 존재 및 상태 확인
    # TODO: CloudFront Signed URL 생성 (프로덕션)
    # TODO: 로컬 파일 URL 생성 (로컬)
    
    if settings.ENVIRONMENT == "local":
        # 로컬 개발용 더미 응답
        return StreamingUrlResponse(
            streaming_url=f"http://localhost:8000/local-files/books/{book_id}/chapters/{chapter_id}.mp3",
            expires_at=datetime.utcnow().replace(hour=23, minute=59, second=59),
            duration=1800
        )
    elif settings.ENVIRONMENT == "production":
        # TODO: CloudFront Signed URL 생성
        return StreamingUrlResponse(
            streaming_url=f"https://{settings.CLOUDFRONT_DOMAIN}/media/books/{book_id}/chapters/{chapter_id}.mp3",
            expires_at=datetime.utcnow().replace(hour=23, minute=59, second=59),
            duration=1800
        )
    
    raise HTTPException(
        status_code=501,
        detail="Streaming URL generation not implemented yet"
    )


@router.delete("/{book_id}/chapters/{chapter_id}")
async def delete_audio_chapter(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID")
):
    """
    오디오 챕터 삭제
    - 파일과 메타데이터 모두 삭제
    """
    # TODO: 사용자 인증 확인
    # TODO: 책 소유권 확인
    # TODO: S3/로컬 스토리지에서 파일 삭제
    # TODO: DynamoDB에서 챕터 정보 삭제
    
    if settings.ENVIRONMENT == "local":
        return {"message": f"Audio chapter {chapter_id} deleted successfully (local dev mode)"}
    
    raise HTTPException(
        status_code=404,
        detail="Audio chapter not found"
    )

