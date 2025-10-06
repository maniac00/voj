"""
Book service layer for PostgreSQL (SQLAlchemy).
"""
from typing import List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.book_sql import BookSQL
from app.models.database import get_db


class BookServiceSQL:
    """Service for book operations using PostgreSQL."""

    @staticmethod
    def create_book(
        db: Session,
        *,
        user_id: str,
        title: str,
        author: str,
        description: Optional[str] = None,
        genre: Optional[str] = None,
        language: str = "ko",
        isbn: Optional[str] = None,
        publisher: Optional[str] = None,
        published_date: Optional[datetime] = None,
    ) -> BookSQL:
        book = BookSQL(
            user_id=user_id,
            book_id=str(uuid.uuid4()),
            title=title,
            author=author,
            description=description,
            genre=genre,
            language=language,
            isbn=isbn,
            publisher=publisher,
            published_date=published_date,
            status="draft",
            total_chapters=0,
            total_duration=0,
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        return book

    @staticmethod
    def get_book(db: Session, *, user_id: str, book_id: str) -> Optional[BookSQL]:
        return db.query(BookSQL).filter(
            and_(BookSQL.user_id == user_id, BookSQL.book_id == book_id)
        ).first()

    @staticmethod
    def list_all_books(db: Session, *, user_id: str) -> List[BookSQL]:
        return db.query(BookSQL).filter(BookSQL.user_id == user_id).order_by(BookSQL.created_at.desc()).all()

    @staticmethod
    def list_books_by_status(db: Session, *, user_id: str, status: str, limit: int) -> List[BookSQL]:
        return db.query(BookSQL).filter(
            and_(BookSQL.user_id == user_id, BookSQL.status == status)
        ).order_by(BookSQL.created_at.desc()).limit(limit).all()

    @staticmethod
    def list_books_by_genre(db: Session, *, user_id: str, genre: str, limit: int) -> List[BookSQL]:
        return db.query(BookSQL).filter(
            and_(BookSQL.user_id == user_id, BookSQL.genre == genre)
        ).order_by(BookSQL.created_at.desc()).limit(limit).all()

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
            if value is not None and hasattr(book, field):
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
