"""
VOJ Audiobooks API - 책 관리 엔드포인트
책 생성, 조회, 수정, 삭제 기능
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth.simple import (
    get_current_user_claims,
    require_admin_scope,
    require_approved_user,
)
from app.models.database import get_db
from app.services.books_sql import BookServiceSQL as BookService
from app.models.book_sql import BookSQL
from app.models.audio_chapter_sql import AudioChapterSQL
from app.core.audit import log_book_created, log_book_deleted
from app.services.storage.factory import storage_service
from sqlalchemy import func

logger = logging.getLogger(__name__)

router = APIRouter()


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


class BookBase(BaseModel):
    """책 기본 정보 모델"""

    title: str = Field(..., min_length=1, max_length=200, description="책 제목")
    author: str = Field(..., min_length=1, max_length=100, description="저자")
    narrator: Optional[str] = Field(None, max_length=50, description="낭독자")
    description: Optional[str] = Field(None, max_length=1000, description="책 설명")
    genre: Optional[str] = Field(None, max_length=50, description="장르")
    language: str = Field(default="ko", description="언어 코드")
    isbn: Optional[str] = Field(None, description="ISBN")
    publisher: Optional[str] = Field(None, max_length=100, description="출판사")
    published_date: Optional[datetime] = Field(None, description="출간일")


class BookCreate(BookBase):
    """책 생성 요청 모델"""

    pass


class BookUpdate(BaseModel):
    """책 수정 요청 모델"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    narrator: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)
    genre: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = Field(None, max_length=100)
    published_date: Optional[datetime] = None
    cover_image_url: Optional[str] = Field(None, description="커버 이미지 URL")
    cover_image_key: Optional[str] = Field(None, description="커버 이미지 스토리지 키")
    is_copyrighted: Optional[bool] = Field(None, description="저작권 보호 콘텐츠 여부 (관리자 전용)")


class Book(BookBase):
    """책 응답 모델"""

    book_id: str
    user_id: str
    status: str = Field(
        default="draft", description="상태: draft, processing, published, error"
    )
    created_at: datetime
    updated_at: datetime
    total_chapters: int = Field(default=0, description="총 챕터 수")
    total_duration: int = Field(default=0, description="총 재생 시간(초)")
    cover_image_url: Optional[str] = None
    is_copyrighted: bool = Field(default=False, description="저작권 보호 콘텐츠 여부")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class BookList(BaseModel):
    """책 목록 응답 모델"""

    books: List[Book]
    total: int
    page: int
    size: int
    has_next: bool


@router.post("", response_model=Book, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=Book, status_code=status.HTTP_201_CREATED)
async def create_book(
    book_data: BookCreate,
    claims=Depends(require_admin_scope()),
    db: Session = Depends(get_db),
):
    """
    새 책 생성
    - 사용자 인증 필요
    - PostgreSQL에 책 정보 저장
    """
    user_id = str(claims.get("sub") or claims.get("username") or "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user claims"
        )

    try:
        normalized_narrator = _normalize_optional_text(book_data.narrator)
        created = BookService.create_book(
            db,
            user_id=user_id,
            title=book_data.title,
            author=book_data.author,
            narrator=normalized_narrator,
            description=book_data.description,
            genre=book_data.genre,
            language=book_data.language,
            isbn=book_data.isbn,
            publisher=book_data.publisher,
            published_date=book_data.published_date,
        )

        log_book_created(user_id, created.book_id, created.title)

        return {
            "book_id": created.book_id,
            "user_id": created.user_id,
            "title": created.title,
            "author": created.author,
            "narrator": created.narrator,
            "description": created.description,
            "genre": created.genre,
            "language": created.language,
            "isbn": created.isbn,
            "publisher": created.publisher,
            "published_date": created.published_date,
            "status": created.status,
            "created_at": created.created_at,
            "updated_at": created.updated_at,
            "total_chapters": created.total_chapters,
            "total_duration": created.total_duration,
            "cover_image_url": created.cover_image_url,
            "is_copyrighted": bool(getattr(created, "is_copyrighted", False)),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create book: {str(e)}")


@router.get("", response_model=BookList)
@router.get("/", response_model=BookList)
async def get_books(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(10, ge=1, le=100, description="페이지 크기"),
    status_filter: Optional[str] = Query(None, alias="status", description="책 상태 필터"),
    genre: Optional[str] = Query(None, description="장르 필터"),
    search: Optional[str] = Query(None, description="제목/저자 검색"),
    claims=Depends(require_approved_user()),
    db: Session = Depends(get_db),
):
    """
    책 목록 조회
    - 페이징 지원
    - 상태, 장르, 검색어로 필터링
    - 승인된 사용자만 접근 가능
    """

    try:
        # 가시성 필터 적용 — 저작권 보호 책은 화이트리스트 사용자/admin만 볼 수 있음
        items = BookService.list_books_for_claims(
            db,
            claims=claims,
            status=status_filter,
            genre=genre,
            limit=size if (status_filter or genre) else None,
        )
        total = len(items)

        # simple in-memory search filter (title/author)
        if search:
            s = search.lower()
            items = [
                b
                for b in items
                if s in (b.title or "").lower()
                or s in (b.author or "").lower()
                or s in (b.narrator or "").lower()
            ]
            total = len(items)

        # 카운트 보정: 단일 GROUP BY 쿼리로 N+1 해소
        book_ids = [b.book_id for b in items]
        counts_map = {}
        if book_ids:
            counts_rows = (
                db.query(AudioChapterSQL.book_id, func.count(AudioChapterSQL.id))
                .filter(AudioChapterSQL.book_id.in_(book_ids))
                .group_by(AudioChapterSQL.book_id)
                .all()
            )
            counts_map = {row[0]: row[1] for row in counts_rows}

        return BookList(
            books=[
                Book(
                    book_id=b.book_id,
                    user_id=b.user_id,
                    title=b.title,
                    author=b.author,
                    narrator=b.narrator,
                    description=b.description,
                    genre=b.genre,
                    language=b.language,
                    isbn=b.isbn,
                    publisher=b.publisher,
                    published_date=b.published_date,
                    status=b.status,
                    created_at=b.created_at,
                    updated_at=b.updated_at,
                    total_chapters=counts_map.get(b.book_id, b.total_chapters or 0),
                    total_duration=b.total_duration,
                    cover_image_url=b.cover_image_url,
                    is_copyrighted=bool(b.is_copyrighted),
                )
                for b in items
            ],
            total=total,
            page=page,
            size=size,
            has_next=False,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list books: {str(e)}")


@router.get("/{book_id}", response_model=Book)
async def get_book(
    book_id: str = Path(..., description="책 ID"),
    claims=Depends(require_approved_user()),
    db: Session = Depends(get_db),
):
    """
    특정 책 상세 조회
    - 승인된 사용자만 접근 가능
    """
    try:
        # 전역 읽기: 특정 사용자 소유 제한 없이 조회
        found = BookService.get_book_any_user(db, book_id=book_id)
        if not found:
            # 소유권 노출 방지를 위해 404 반환
            raise HTTPException(status_code=404, detail="Book not found")
        # 저작권 보호 콘텐츠 가시성 검증 — 권한 없으면 존재 자체를 숨김
        if not BookService.is_book_visible(found, claims, db):
            raise HTTPException(status_code=404, detail="Book not found")
        # 상세 카운트 보정
        chapter_count = (
            db.query(func.count(AudioChapterSQL.id))
            .filter(AudioChapterSQL.book_id == book_id)
            .scalar()
        ) or 0

        return {
            "book_id": found.book_id,
            "user_id": found.user_id,
            "title": found.title,
            "author": found.author,
            "narrator": found.narrator,
            "description": found.description,
            "genre": found.genre,
            "language": found.language,
            "isbn": found.isbn,
            "publisher": found.publisher,
            "published_date": found.published_date,
            "status": found.status,
            "created_at": found.created_at,
            "updated_at": found.updated_at,
            "total_chapters": int(chapter_count),
            "total_duration": found.total_duration,
            "cover_image_url": found.cover_image_url,
            "is_copyrighted": bool(found.is_copyrighted),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get book: {str(e)}")


@router.put("/{book_id}", response_model=Book)
async def update_book(
    book_data: BookUpdate,
    book_id: str = Path(..., description="책 ID"),
    claims=Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """
    책 정보 수정
    - 사용자 인증 필요
    - 본인의 책만 수정 가능
    """
    user_id = str(claims.get("sub") or claims.get("username") or "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user claims"
        )

    found = BookService.get_book(db, user_id=user_id, book_id=book_id)
    if not found:
        raise HTTPException(status_code=404, detail="Book not found")

    try:
        explicit_fields = (
            book_data.model_fields_set
            if hasattr(book_data, "model_fields_set")
            else set()
        )
        normalized_narrator = (
            _normalize_optional_text(book_data.narrator)
            if "narrator" in explicit_fields
            else None
        )

        # is_copyrighted 토글은 관리자만 허용
        is_admin = str(claims.get("scope", "")).lower() == "admin"
        copyright_update = (
            book_data.is_copyrighted
            if ("is_copyrighted" in explicit_fields and is_admin)
            else None
        )
        if "is_copyrighted" in explicit_fields and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can change copyright protection",
            )

        updated = BookService.update_book(
            db,
            user_id=user_id,
            book_id=book_id,
            title=book_data.title,
            author=book_data.author,
            narrator=normalized_narrator,
            description=book_data.description,
            genre=book_data.genre,
            language=book_data.language,
            isbn=book_data.isbn,
            publisher=book_data.publisher,
            published_date=book_data.published_date,
            cover_image_url=book_data.cover_image_url,
            cover_image_key=book_data.cover_image_key,
            is_copyrighted=copyright_update,
        )
        if updated is None:
            raise HTTPException(status_code=500, detail="Failed to update book")

        # 커버 이미지 명시적 null 처리 (삭제 시)
        should_commit = False
        if "narrator" in explicit_fields and normalized_narrator is None:
            found.narrator = None
            should_commit = True
        if "cover_image_url" in explicit_fields and book_data.cover_image_url is None:
            found.cover_image_url = None
            should_commit = True
        if "cover_image_key" in explicit_fields and book_data.cover_image_key is None:
            found.cover_image_key = None
            should_commit = True
        if should_commit:
            db.commit()
            db.refresh(found)
            updated = found
        return {
            "book_id": updated.book_id,
            "user_id": updated.user_id,
            "title": updated.title,
            "author": updated.author,
            "narrator": updated.narrator,
            "description": updated.description,
            "genre": updated.genre,
            "language": updated.language,
            "isbn": updated.isbn,
            "publisher": updated.publisher,
            "published_date": updated.published_date,
            "status": updated.status,
            "created_at": updated.created_at,
            "updated_at": updated.updated_at,
            "total_chapters": updated.total_chapters,
            "total_duration": updated.total_duration,
            "cover_image_url": updated.cover_image_url,
            "is_copyrighted": bool(getattr(updated, "is_copyrighted", False)),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update book: {str(e)}")


@router.delete("/{book_id}")
async def delete_book(
    book_id: str = Path(..., description="책 ID"),
    claims=Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """
    책 삭제
    - 사용자 인증 필요
    - 본인의 책만 삭제 가능
    - 연관된 오디오 파일도 함께 삭제
    """
    user_id = str(claims.get("sub") or claims.get("username") or "")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user claims"
        )

    # 소유권 확인
    book = BookService.get_book(db, user_id=user_id, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 연관 리소스 정리: 챕터별 오디오 파일 삭제
    chapters = (
        db.query(AudioChapterSQL).filter(AudioChapterSQL.book_id == book_id).all()
    )
    for chapter in chapters:
        if chapter.audio_key:
            try:
                await storage_service.delete_file(chapter.audio_key)
            except Exception as e:
                logger.warning(
                    "Failed to delete storage file %s: %s", chapter.audio_key, e
                )

    # 커버 이미지 삭제
    cover_key = getattr(book, "cover_image_key", None)
    if cover_key:
        try:
            await storage_service.delete_file(cover_key)
        except Exception as e:
            logger.warning("Failed to delete cover image %s: %s", cover_key, e)
    # DB CASCADE가 챕터 레코드를 자동 삭제함
    try:
        ok = BookService.delete_book(db, user_id=user_id, book_id=book_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Book not found")
        log_book_deleted(user_id, book_id)
        return {"message": f"Book {book_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete book: {str(e)}")
