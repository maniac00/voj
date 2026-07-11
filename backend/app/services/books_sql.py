"""
Book service layer for PostgreSQL (SQLAlchemy).
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Query, Session

from app.models.book_sql import BookSQL
from app.models.database import get_db
from app.models.user_sql import UserSQL


ALLOWED_UPDATE_FIELDS = frozenset(
    {
        "title",
        "author",
        "narrator",
        "description",
        "genre",
        "language",
        "isbn",
        "publisher",
        "published_date",
        "status",
        "total_chapters",
        "total_duration",
        "cover_image_url",
        "cover_image_key",
        "is_copyrighted",
    }
)


def _resolve_user_for_claims(
    claims: Optional[Dict[str, Any]], db: Session
) -> Optional[UserSQL]:
    """claims에서 UserSQL 레코드를 찾는다 (HMAC/bypass 사용자는 None)."""
    if not claims:
        return None
    user_id = claims.get("user_id")
    if isinstance(user_id, int):
        user = db.query(UserSQL).filter(UserSQL.id == user_id).first()
        if user:
            return user
    firebase_uid = claims.get("uid") or claims.get("sub")
    if firebase_uid and not str(firebase_uid).startswith("simple-user-"):
        user = (
            db.query(UserSQL)
            .filter(UserSQL.firebase_uid == str(firebase_uid))
            .first()
        )
        if user:
            return user
    email = claims.get("email") or claims.get("username")
    if email:
        user = db.query(UserSQL).filter(UserSQL.email == str(email)).first()
        if user:
            return user
    return None


def _claims_is_admin(claims: Optional[Dict[str, Any]]) -> bool:
    if not claims:
        return False
    if str(claims.get("scope", "")).lower() == "admin":
        return True
    if str(claims.get("role", "")).lower() == "admin":
        return True
    return False


class BookServiceSQL:
    """Service for book operations using PostgreSQL."""

    @staticmethod
    def claims_can_access_copyrighted(
        claims: Optional[Dict[str, Any]], db: Session
    ) -> bool:
        """저작권 보호 콘텐츠 접근 가능 여부.
        - 관리자(scope=admin 또는 role=admin)는 항상 허용
        - 그 외에는 UserSQL.can_access_copyrighted 플래그로 판정
        """
        if _claims_is_admin(claims):
            return True
        user = _resolve_user_for_claims(claims, db)
        return bool(user and user.can_access_copyrighted)

    @staticmethod
    def apply_visibility_filter(
        query: Query, claims: Optional[Dict[str, Any]], db: Session
    ) -> Query:
        """저작권 화이트리스트가 없으면 is_copyrighted=true 책을 제외한다."""
        if BookServiceSQL.claims_can_access_copyrighted(claims, db):
            return query
        return query.filter(BookSQL.is_copyrighted.is_(False))

    @staticmethod
    def is_book_visible(
        book: Optional[BookSQL], claims: Optional[Dict[str, Any]], db: Session
    ) -> bool:
        if book is None:
            return False
        if not bool(book.is_copyrighted):
            return True
        return BookServiceSQL.claims_can_access_copyrighted(claims, db)

    @staticmethod
    def create_book(
        db: Session,
        *,
        user_id: str,
        title: str,
        author: str,
        narrator: Optional[str] = None,
        description: Optional[str] = None,
        genre: Optional[str] = None,
        language: str = "ko",
        isbn: Optional[str] = None,
        publisher: Optional[str] = None,
        published_date: Optional[datetime] = None,
        is_copyrighted: bool = True,
    ) -> BookSQL:
        book = BookSQL(
            user_id=user_id,
            book_id=str(uuid.uuid4()),
            title=title,
            author=author,
            narrator=narrator,
            description=description,
            genre=genre,
            language=language,
            isbn=isbn,
            publisher=publisher,
            published_date=published_date,
            status="draft",
            total_chapters=0,
            total_duration=0,
            is_copyrighted=is_copyrighted,
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        return book

    @staticmethod
    def get_book(db: Session, *, user_id: str, book_id: str) -> Optional[BookSQL]:
        return (
            db.query(BookSQL)
            .filter(and_(BookSQL.user_id == user_id, BookSQL.book_id == book_id))
            .first()
        )

    @staticmethod
    def get_book_any_user(db: Session, *, book_id: str) -> Optional[BookSQL]:
        return db.query(BookSQL).filter(BookSQL.book_id == book_id).first()

    @staticmethod
    def list_all_books(db: Session, *, user_id: str) -> List[BookSQL]:
        return (
            db.query(BookSQL)
            .filter(BookSQL.user_id == user_id)
            .order_by(BookSQL.created_at.desc())
            .all()
        )

    @staticmethod
    def list_all_books_any_user(db: Session) -> List[BookSQL]:
        """관리자용: 사용자 구분 없이 전체 책 목록 반환 (MVP 편의)."""
        return db.query(BookSQL).order_by(BookSQL.created_at.desc()).all()

    @staticmethod
    def list_books_for_claims(
        db: Session,
        *,
        claims: Optional[Dict[str, Any]],
        status: Optional[str] = None,
        genre: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[BookSQL]:
        """가시성 필터를 적용해 책 목록을 반환한다."""
        q = db.query(BookSQL)
        q = BookServiceSQL.apply_visibility_filter(q, claims, db)
        if status:
            q = q.filter(BookSQL.status == status)
        if genre:
            q = q.filter(BookSQL.genre == genre)
        q = q.order_by(BookSQL.created_at.desc())
        if limit:
            q = q.limit(limit)
        return q.all()

    @staticmethod
    def list_books_by_status(
        db: Session, *, user_id: str, status: str, limit: int
    ) -> List[BookSQL]:
        return (
            db.query(BookSQL)
            .filter(and_(BookSQL.user_id == user_id, BookSQL.status == status))
            .order_by(BookSQL.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def list_books_by_status_any_user(
        db: Session, *, status: str, limit: int
    ) -> List[BookSQL]:
        return (
            db.query(BookSQL)
            .filter(BookSQL.status == status)
            .order_by(BookSQL.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def list_books_by_genre(
        db: Session, *, user_id: str, genre: str, limit: int
    ) -> List[BookSQL]:
        return (
            db.query(BookSQL)
            .filter(and_(BookSQL.user_id == user_id, BookSQL.genre == genre))
            .order_by(BookSQL.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def list_books_by_genre_any_user(
        db: Session, *, genre: str, limit: int
    ) -> List[BookSQL]:
        return (
            db.query(BookSQL)
            .filter(BookSQL.genre == genre)
            .order_by(BookSQL.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def update_book(
        db: Session,
        *,
        user_id: str,
        book_id: str,
        **updates,
    ) -> Optional[BookSQL]:
        book = BookServiceSQL.get_book(db, user_id=user_id, book_id=book_id)
        if not book:
            return None

        for field, value in updates.items():
            if value is not None and field in ALLOWED_UPDATE_FIELDS:
                setattr(book, field, value)

        db.commit()
        db.refresh(book)
        return book

    @staticmethod
    def update_book_any_user(
        db: Session,
        *,
        book_id: str,
        **updates,
    ) -> Optional[BookSQL]:
        book = BookServiceSQL.get_book_any_user(db, book_id=book_id)
        if not book:
            return None

        for field, value in updates.items():
            if value is not None and field in ALLOWED_UPDATE_FIELDS:
                setattr(book, field, value)

        db.commit()
        db.refresh(book)
        return book

    @staticmethod
    def delete_book(db: Session, *, user_id: str, book_id: str) -> bool:
        book = BookServiceSQL.get_book(db, user_id=user_id, book_id=book_id)
        if not book:
            return False
        db.delete(book)
        db.commit()
        return True

    @staticmethod
    def delete_book_any_user(db: Session, *, book_id: str) -> bool:
        book = BookServiceSQL.get_book_any_user(db, book_id=book_id)
        if not book:
            return False
        db.delete(book)
        db.commit()
        return True
