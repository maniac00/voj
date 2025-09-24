"""
Book service layer built on top of PynamoDB model `Book`.

Provides CRUD operations and simple listings.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime
import uuid

from app.models.book import Book


@dataclass
class PageResult:
    items: List[Book]
    last_evaluated_key: Optional[dict]


class BookService:
    """Service encapsulating common operations for books."""

    @staticmethod
    def create_book(
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
    ) -> Book:
        book = Book(
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
        book.save()
        return book

    @staticmethod
    def get_book(*, user_id: str, book_id: str) -> Optional[Book]:
        try:
            return Book.get(user_id, book_id)
        except Book.DoesNotExist:
            return None

    @staticmethod
    def list_books(
        *,
        user_id: str,
        limit: int = 10,
        last_evaluated_key: Optional[dict] = None,
    ) -> PageResult:
        query_kwargs = {
            "limit": limit,
            "scan_index_forward": False,
        }
        if last_evaluated_key:
            query_kwargs["last_evaluated_key"] = last_evaluated_key

        result = Book.query(user_id, **query_kwargs)
        items = list(result)
        lek = getattr(result, "last_evaluated_key", None)
        return PageResult(items=items, last_evaluated_key=lek)

    @staticmethod
    def list_all_books(*, user_id: str) -> List[Book]:
        """Return all books for the user by consuming the full iterator.

        Note: Intended for small-to-medium datasets (tests/admin views). For large datasets,
        prefer cursor-based pagination.
        """
        result = Book.query(user_id)
        return list(result)

    @staticmethod
    def list_books_by_status(
        *, user_id: str, status: str, limit: int
    ) -> List[Book]:
        results = Book.list_by_user_and_status(user_id, status=status, limit=limit)
        return list(results)

    @staticmethod
    def list_books_by_genre(
        *, user_id: str, genre: str, limit: int
    ) -> List[Book]:
        results = Book.list_by_user_and_genre(user_id, genre=genre, limit=limit)
        return list(results)

    @staticmethod
    def update_book(
        *,
        user_id: str,
        book_id: str,
        **updates,
    ) -> Optional[Book]:
        book = BookService.get_book(user_id=user_id, book_id=book_id)
        if not book:
            return None

        # Update only provided fields
        for field, value in updates.items():
            if value is not None and hasattr(book, field):
                setattr(book, field, value)
        book.save()
        return book

    @staticmethod
    def delete_book(*, user_id: str, book_id: str) -> bool:
        book = BookService.get_book(user_id=user_id, book_id=book_id)
        if not book:
            return False
        book.delete()
        return True


