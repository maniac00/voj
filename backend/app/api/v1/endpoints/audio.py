"""
VOJ Audiobooks API - 오디오 관리 엔드포인트
오디오 파일 업로드, 챕터 관리, 스트리밍 URL 생성
"""
import asyncio
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger(__name__)

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Path,
    Request,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.auth.simple import get_current_user_claims, require_any_scope, require_approved_user
from app.core.config import settings
from app.models.analytics_sql import PlaybackProgressSQL
from app.models.audio_chapter_sql import AudioChapterSQL
from app.models.database import get_db
from app.models.user_sql import UserSQL
from app.services.books_sql import BookServiceSQL as BookService
from app.core.audit import log_audio_deleted
from app.services.storage.factory import storage_service
from app.utils.audio_convert import get_audio_duration


def _extract_file_name(audio_key: Optional[str]) -> str:
    if not audio_key:
        return ""
    name = audio_key.split("/")[-1]
    parts = name.split("_", 1)
    return parts[1] if len(parts) > 1 else name


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
    status: str = Field(
        default="processing", description="상태: uploading, processing, ready, error"
    )
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class AudioChapterUpdate(BaseModel):
    """오디오 챕터 수정 요청 모델"""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="챕터 제목")


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
        json_encoders = {datetime: lambda v: v.isoformat()}


@router.post("/{book_id}/chapters/upload", response_model=AudioUploadResponse)
async def upload_audio_chapter(
    book_id: str = Path(..., description="책 ID"),
    chapter_data: AudioChapterCreate = None,
    audio_file: UploadFile = File(..., description="오디오 파일"),
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
            detail=f"Unsupported file type. Allowed types: {allowed_types}",
        )

    if settings.ENVIRONMENT == "local":
        # 로컬 개발용 더미 응답
        chapter_id = str(uuid.uuid4())
        return AudioUploadResponse(
            chapter_id=chapter_id,
            upload_status="uploaded",
            message=f"Audio file {audio_file.filename} uploaded successfully (local dev mode)",
        )

    raise HTTPException(status_code=501, detail="Audio upload not implemented yet")


@router.get("/{book_id}/chapters", response_model=List[AudioChapter])
async def get_audio_chapters(
    book_id: str = Path(..., description="책 ID"),
    status: Optional[str] = Query(None, description="챕터 상태 필터"),
    claims=Depends(require_approved_user()),
    db: Session = Depends(get_db),
):
    """
    책의 오디오 챕터 목록 조회
    - 챕터 번호 순으로 정렬
    - 승인된 사용자만 접근 가능 (공개 라이브러리 — 소유권 제한 없음)
    """
    # 승인된 사용자는 모든 책의 챕터에 접근 가능
    book = BookService.get_book_any_user(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    try:
        query = (
            db.query(AudioChapterSQL)
            .filter(AudioChapterSQL.book_id == book_id)
            .order_by(
                AudioChapterSQL.chapter_number.asc(), AudioChapterSQL.created_at.asc()
            )
        )
        rows = query.all()

        results: List[AudioChapter] = []
        for row in rows:
            results.append(
                AudioChapter(
                    chapter_id=row.chapter_id,
                    book_id=row.book_id,
                    chapter_number=int(row.chapter_number),
                    title=row.chapter_title or "",
                    description="",
                    file_name=_extract_file_name(row.audio_key),
                    file_size=int(row.file_size or 0),
                    duration=int(row.duration or 0),
                    status="ready",
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                )
            )

        return results
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list chapters: {str(e)}"
        )


@router.patch("/{book_id}/chapters/{chapter_id}", response_model=AudioChapter)
async def update_chapter_metadata(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID"),
    payload: AudioChapterUpdate = None,
    claims=Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """
    오디오 챕터 메타데이터 수정 (제목 등)
    - 사용자 인증 및 소유권 검증
    """
    user_id = str(claims.get("sub") or claims.get("username") or "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user claims"
        )

    is_admin = str(claims.get("scope", "")).lower() == "admin"
    book = (
        BookService.get_book_any_user(db, book_id=book_id)
        if is_admin
        else BookService.get_book(db, user_id=user_id, book_id=book_id)
    )
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    chapter = (
        db.query(AudioChapterSQL)
        .filter(
            and_(
                AudioChapterSQL.chapter_id == chapter_id,
                AudioChapterSQL.book_id == book_id,
            )
        )
        .first()
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if not payload:
        raise HTTPException(status_code=400, detail="No update data provided")

    try:
        if payload.title is not None:
            chapter.chapter_title = payload.title
        db.commit()
        db.refresh(chapter)

        return AudioChapter(
            chapter_id=chapter.chapter_id,
            book_id=chapter.book_id,
            chapter_number=int(chapter.chapter_number),
            title=chapter.chapter_title or "",
            description="",
            file_name=_extract_file_name(chapter.audio_key),
            file_size=int(chapter.file_size or 0),
            duration=int(chapter.duration or 0),
            status="ready",
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update chapter: {str(e)}"
        )


@router.put("/{book_id}/chapters/{chapter_id}", response_model=AudioChapter)
async def update_chapter_order(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID"),
    new_number: int = Query(..., ge=1, description="새로운 챕터 번호"),
    claims=Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """
    오디오 챕터 순서 변경 (chapter_number 업데이트)
    - 사용자 인증 및 소유권 검증
    - 동일 책 내에서 번호만 변경 (충돌 케이스는 단순 교체/중복 허용 없이 overwrite)
    """
    user_id = str(claims.get("sub") or claims.get("username") or "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user claims"
        )

    # 책 소유권 확인 (관리자 우회 허용)
    is_admin = str(claims.get("scope", "")).lower() == "admin"
    book = (
        BookService.get_book_any_user(db, book_id=book_id)
        if is_admin
        else BookService.get_book(db, user_id=user_id, book_id=book_id)
    )
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 챕터 조회
    chapter = (
        db.query(AudioChapterSQL)
        .filter(
            and_(
                AudioChapterSQL.chapter_id == chapter_id,
                AudioChapterSQL.book_id == book_id,
            )
        )
        .first()
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    old_number = chapter.chapter_number
    if old_number == new_number:
        file_name = _extract_file_name(chapter.audio_key)
        return AudioChapter(
            chapter_id=chapter.chapter_id,
            book_id=chapter.book_id,
            chapter_number=int(chapter.chapter_number),
            title=chapter.chapter_title or "",
            description="",
            file_name=file_name,
            file_size=int(chapter.file_size or 0),
            duration=int(chapter.duration or 0),
            status="ready",
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
        )

    try:
        # 충돌하는 챕터가 있는지 확인
        conflicting = (
            db.query(AudioChapterSQL)
            .filter(
                and_(
                    AudioChapterSQL.book_id == book_id,
                    AudioChapterSQL.chapter_number == new_number,
                )
            )
            .first()
        )

        if conflicting:
            # 임시 번호로 충돌 회피 후 스왑
            conflicting.chapter_number = -1
            db.flush()
            chapter.chapter_number = new_number
            db.flush()
            conflicting.chapter_number = old_number
            db.commit()
        else:
            chapter.chapter_number = new_number
            db.commit()

        db.refresh(chapter)
        file_name = _extract_file_name(chapter.audio_key)

        return AudioChapter(
            chapter_id=chapter.chapter_id,
            book_id=chapter.book_id,
            chapter_number=int(chapter.chapter_number),
            title=chapter.chapter_title or "",
            description="",
            file_name=file_name,
            file_size=int(chapter.file_size or 0),
            duration=int(chapter.duration or 0),
            status="ready",
            created_at=chapter.created_at,
            updated_at=chapter.updated_at,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to update chapter order: {str(e)}"
        )


@router.get("/{book_id}/chapters/{chapter_id}", response_model=AudioChapter)
async def get_audio_chapter(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID"),
    claims=Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """
    특정 오디오 챕터 상세 조회 (DB 기반)
    - 인증된 사용자는 모든 책의 챕터에 접근 가능
    """
    book = BookService.get_book_any_user(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 챕터 조회 및 검증
    chapter = (
        db.query(AudioChapterSQL)
        .filter(
            and_(
                AudioChapterSQL.chapter_id == chapter_id,
                AudioChapterSQL.book_id == book_id,
            )
        )
        .first()
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Audio chapter not found")

    file_name = _extract_file_name(chapter.audio_key)

    return AudioChapter(
        chapter_id=chapter.chapter_id,
        book_id=chapter.book_id,
        chapter_number=int(chapter.chapter_number),
        title=chapter.chapter_title or "",
        description="",
        file_name=file_name,
        file_size=int(chapter.file_size or 0),
        duration=int(chapter.duration or 0),
        status="ready",
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
    )


@router.get(
    "/{book_id}/chapters/{chapter_id}/stream", response_model=StreamingUrlResponse
)
async def get_streaming_url(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID"),
    claims=Depends(require_approved_user()),
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    오디오 챕터 스트리밍 URL 생성
    - 승인된 사용자만 접근 가능 (공개 라이브러리 — 소유권 제한 없음)
    """
    book = BookService.get_book_any_user(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 챕터 조회 및 상태 확인
    chapter = (
        db.query(AudioChapterSQL)
        .filter(
            and_(
                AudioChapterSQL.chapter_id == chapter_id,
                AudioChapterSQL.book_id == book_id,
            )
        )
        .first()
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Audio chapter not found")

    storage_file_key = (
        chapter.audio_key or f"book/{book_id}/media/{chapter.chapter_id}.m4a"
    )
    storage_file_key = storage_file_key.lstrip("/")

    expires = datetime.now(timezone.utc).replace(
        hour=23, minute=59, second=59, microsecond=0
    )
    duration = int(chapter.duration or 0)

    if settings.ENVIRONMENT == "production":
        # R2 Worker HMAC 서명 URL 반환 (이그레스 무료)
        if settings.R2_WORKER_URL and settings.R2_AUTH_SECRET:
            import hashlib
            import hmac
            import time as _time
            from urllib.parse import quote

            exp = int(_time.time()) + 3600
            # HMAC 서명은 raw key (한국어 포함)로 계산
            message = f"{storage_file_key}:{exp}".encode()
            secret = settings.R2_AUTH_SECRET.encode()
            token = hmac.new(secret, message, hashlib.sha256).hexdigest()
            worker_url = settings.R2_WORKER_URL.rstrip("/")
            # URL 경로는 percent-encode (비ASCII 문자를 Flutter/ExoPlayer가 올바르게 처리하도록)
            encoded_key = quote(storage_file_key, safe="/")
            signed_url = f"{worker_url}/{encoded_key}?token={token}&exp={exp}"
            logger.info("R2 Worker URL 반환: %s", storage_file_key)
            return StreamingUrlResponse(streaming_url=signed_url, expires_at=expires, duration=duration)

        # R2 미설정 시 Railway 직접 스트리밍 fallback
        base = os.getenv("BACKEND_ORIGIN") or os.getenv("RAILWAY_PUBLIC_DOMAIN")
        if not base and request is not None:
            base = str(request.base_url)
        if base:
            base = base.strip()
            if not (base.startswith("http://") or base.startswith("https://")):
                base = f"https://{base}"
            absolute_url = f"{base.rstrip('/')}{settings.API_V1_STR}/files/{storage_file_key}"
            return StreamingUrlResponse(streaming_url=absolute_url, expires_at=expires, duration=duration)

    streaming_path = f"{settings.API_V1_STR}/files/{storage_file_key}"
    if not streaming_path.startswith("/"):
        streaming_path = f"/{streaming_path.lstrip('/')}"
    return StreamingUrlResponse(streaming_url=streaming_path, expires_at=expires, duration=duration)


@router.post("/{book_id}/chapters/{chapter_id}/progress")
async def update_playback_progress(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID"),
    payload: dict = None,
    claims=Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """
    재생 진행률 업데이트 — playback_progress 테이블에 UPSERT
    """
    book = BookService.get_book_any_user(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    chapter = (
        db.query(AudioChapterSQL)
        .filter(
            and_(
                AudioChapterSQL.chapter_id == chapter_id,
                AudioChapterSQL.book_id == book_id,
            )
        )
        .first()
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    position = 0
    duration = 0
    try:
        position = int((payload or {}).get("position", 0))
        duration = int((payload or {}).get("duration", 0))
    except Exception:
        pass

    user_id = _resolve_user_id_from_claims(claims, db)
    if not user_id:
        return {"ok": True}

    try:
        progress = db.query(PlaybackProgressSQL).filter(
            and_(
                PlaybackProgressSQL.user_id == user_id,
                PlaybackProgressSQL.book_id == book_id,
                PlaybackProgressSQL.chapter_id == chapter_id,
            )
        ).first()

        if progress:
            progress.position_seconds = position
            progress.duration_seconds = duration
            progress.last_played_at = func.now()
        else:
            progress = PlaybackProgressSQL(
                user_id=user_id,
                book_id=book_id,
                chapter_id=chapter_id,
                position_seconds=position,
                duration_seconds=duration,
            )
            db.add(progress)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.warning("Failed to save playback progress: %s", e)

    return {"ok": True}


@router.get("/{book_id}/chapters/{chapter_id}/position")
async def get_playback_position(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID"),
    claims=Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """
    마지막 재생 위치 조회 — playback_progress 테이블에서 조회
    """
    book = BookService.get_book_any_user(db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    chapter_exists = (
        db.query(AudioChapterSQL)
        .filter(
            and_(
                AudioChapterSQL.chapter_id == chapter_id,
                AudioChapterSQL.book_id == book_id,
            )
        )
        .first()
        is not None
    )
    if not chapter_exists:
        raise HTTPException(status_code=404, detail="Chapter not found")

    user_id = _resolve_user_id_from_claims(claims, db)
    if not user_id:
        return {}

    progress = db.query(PlaybackProgressSQL).filter(
        and_(
            PlaybackProgressSQL.user_id == user_id,
            PlaybackProgressSQL.book_id == book_id,
            PlaybackProgressSQL.chapter_id == chapter_id,
        )
    ).first()

    if not progress:
        return {}

    return {
        "position": progress.position_seconds,
        "duration": progress.duration_seconds,
        "last_played_at": progress.last_played_at.isoformat() if progress.last_played_at else None,
    }

@router.delete("/{book_id}/chapters/{chapter_id}")
async def delete_audio_chapter(
    book_id: str = Path(..., description="책 ID"),
    chapter_id: str = Path(..., description="챕터 ID"),
    claims=Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """
    오디오 챕터 삭제
    - 파일과 메타데이터 모두 삭제
    """
    user_id = str(claims.get("sub") or claims.get("username") or "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user claims"
        )

    # 책 소유권 확인 (관리자 우회 허용)
    is_admin = str(claims.get("scope", "")).lower() == "admin"
    book = (
        BookService.get_book_any_user(db, book_id=book_id)
        if is_admin
        else BookService.get_book(db, user_id=user_id, book_id=book_id)
    )
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    chapter = (
        db.query(AudioChapterSQL)
        .filter(
            and_(
                AudioChapterSQL.chapter_id == chapter_id,
                AudioChapterSQL.book_id == book_id,
            )
        )
        .first()
    )
    if not chapter:
        raise HTTPException(status_code=404, detail="Audio chapter not found")

    # 스토리지 파일 삭제 시도
    try:
        if chapter.audio_key:
            await storage_service.delete_file(chapter.audio_key)
    except Exception as e:
        logger.warning("Failed to delete storage file %s: %s", chapter.audio_key, e)

    # 챕터 삭제
    try:
        db.delete(chapter)
        db.commit()
        log_audio_deleted(user_id, book_id, chapter_id)
        return {"message": f"Audio chapter {chapter_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete chapter: {str(e)}"
        )


def _resolve_user_id_from_claims(claims: dict, db: Session):
    """claims에서 DB user.id를 찾는다."""
    firebase_uid = claims.get("uid") or claims.get("sub") or ""
    if firebase_uid:
        user = db.query(UserSQL).filter(UserSQL.firebase_uid == str(firebase_uid)).first()
        if user:
            return user.id
    username = claims.get("username") or ""
    if username:
        user = db.query(UserSQL).filter(UserSQL.email == username).first()
        if user:
            return user.id
    return None


@router.post("/backfill-durations")
async def backfill_durations(
    dry_run: bool = Query(True, description="True면 대상만 조회, False면 실제 업데이트"),
    claims=Depends(require_any_scope(["admin"])),
    db: Session = Depends(get_db),
):
    """
    duration이 0이거나 NULL인 챕터들의 duration을 재계산 (admin 전용).

    각 챕터의 오디오 파일을 스토리지에서 다운로드하여 ffprobe + mutagen으로 duration을 추출한 뒤
    DB를 업데이트한다.
    """
    chapters = (
        db.query(AudioChapterSQL)
        .filter(
            AudioChapterSQL.audio_key.isnot(None),
            or_(
                AudioChapterSQL.duration.is_(None),
                AudioChapterSQL.duration <= 0,
            ),
        )
        .all()
    )

    total = len(chapters)

    if not chapters:
        return {
            "success": True,
            "message": "No chapters with missing duration",
            "total": 0,
            "updated": 0,
            "failed": 0,
            "skipped": 0,
        }

    if dry_run:
        files = [
            {
                "chapter_id": ch.chapter_id,
                "book_id": ch.book_id,
                "audio_key": ch.audio_key,
                "current_duration": ch.duration,
            }
            for ch in chapters
        ]
        return {
            "success": True,
            "dry_run": True,
            "total": total,
            "files": files,
        }

    updated = 0
    failed = 0
    skipped = 0
    results = []

    for ch in chapters:
        audio_key = ch.audio_key
        try:
            file_data = await storage_service.download_file(audio_key)
            if file_data is None:
                logger.warning("backfill: file not found in storage: %s", audio_key)
                results.append({"chapter_id": ch.chapter_id, "audio_key": audio_key, "status": "not_found"})
                skipped += 1
                continue

            # 확장자 결정
            ext = os.path.splitext(audio_key)[1] or ".m4a"

            # 임시 파일에 저장 → get_audio_duration (ffprobe + mutagen fallback)
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                tmp.write(file_data)
                tmp_path = tmp.name

            try:
                duration = await asyncio.to_thread(get_audio_duration, tmp_path)
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

            if duration > 0:
                ch.duration = duration
                db.commit()
                updated += 1
                results.append({"chapter_id": ch.chapter_id, "audio_key": audio_key, "status": "ok", "duration": duration})
                logger.info("backfill: %s → %d s", audio_key, duration)
            else:
                skipped += 1
                results.append({"chapter_id": ch.chapter_id, "audio_key": audio_key, "status": "duration_zero"})
                logger.warning("backfill: could not extract duration for %s", audio_key)

        except Exception as e:
            db.rollback()
            logger.error("backfill error for %s: %s", audio_key, e)
            results.append({"chapter_id": ch.chapter_id, "audio_key": audio_key, "status": "error", "detail": str(e)})
            failed += 1

    return {
        "success": True,
        "message": f"Backfill complete: {updated} updated, {failed} failed, {skipped} skipped",
        "total": total,
        "updated": updated,
        "failed": failed,
        "skipped": skipped,
        "results": results,
    }
