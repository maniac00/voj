"""
VOJ Audiobooks API - Book 모델
책 정보를 저장하는 DynamoDB 모델
"""
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, BooleanAttribute,
    UTCDateTimeAttribute, ListAttribute
)
from pynamodb.indexes import LocalSecondaryIndex, AllProjection
from datetime import datetime
from typing import Optional, List

from app.core.config import settings
from .base import BaseModel


class BookStatusIndex(LocalSecondaryIndex):
    """책 상태별 인덱스"""
    
    class Meta:
        index_name = "status-index"
        projection = AllProjection()
    
    user_id = UnicodeAttribute(hash_key=True)
    status = UnicodeAttribute(range_key=True)


class BookGenreIndex(LocalSecondaryIndex):
    """장르별 인덱스"""
    
    class Meta:
        index_name = "genre-index"
        projection = AllProjection()
    
    user_id = UnicodeAttribute(hash_key=True)
    genre = UnicodeAttribute(range_key=True)


class Book(BaseModel):
    """책 모델"""
    
    class Meta:
        table_name = settings.BOOKS_TABLE_NAME
        region = settings.AWS_REGION
        
        # 환경별 엔드포인트 설정
        if settings.ENVIRONMENT == "local" and settings.DYNAMODB_ENDPOINT_URL:
            host = settings.DYNAMODB_ENDPOINT_URL
            aws_access_key_id = "dummy"
            aws_secret_access_key = "dummy"
    
    # Primary Key
    user_id = UnicodeAttribute(hash_key=True, attr_name="user_id")
    book_id = UnicodeAttribute(range_key=True, attr_name="book_id")
    
    # 책 기본 정보
    title = UnicodeAttribute(attr_name="title")
    author = UnicodeAttribute(attr_name="author")
    description = UnicodeAttribute(null=True, attr_name="description")
    genre = UnicodeAttribute(null=True, attr_name="genre")
    language = UnicodeAttribute(default="ko", attr_name="language")
    isbn = UnicodeAttribute(null=True, attr_name="isbn")
    publisher = UnicodeAttribute(null=True, attr_name="publisher")
    published_date = UTCDateTimeAttribute(null=True, attr_name="published_date")
    
    # 책 상태 및 메타데이터
    status = UnicodeAttribute(default="draft", attr_name="status")  # draft, processing, published, error
    total_chapters = NumberAttribute(default=0, attr_name="total_chapters")
    total_duration = NumberAttribute(default=0, attr_name="total_duration")  # 초 단위
    
    # 파일 정보
    cover_image_url = UnicodeAttribute(null=True, attr_name="cover_image_url")
    cover_image_key = UnicodeAttribute(null=True, attr_name="cover_image_key")  # S3 키
    
    # 인덱스
    status_index = BookStatusIndex()
    genre_index = BookGenreIndex()
    
    @classmethod
    def get_by_user_and_book(cls, user_id: str, book_id: str) -> Optional['Book']:
        """사용자 ID와 책 ID로 책 조회"""
        try:
            return cls.get(user_id, book_id)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def list_by_user(cls, user_id: str, limit: int = 10, last_evaluated_key: dict = None):
        """사용자의 책 목록 조회"""
        query_kwargs = {
            'limit': limit,
            'scan_index_forward': False  # 최신순 정렬
        }
        
        if last_evaluated_key:
            query_kwargs['last_evaluated_key'] = last_evaluated_key
        
        return cls.query(user_id, **query_kwargs)
    
    @classmethod
    def list_by_user_and_status(cls, user_id: str, status: str, limit: int = 10):
        """사용자의 특정 상태 책 목록 조회"""
        return cls.status_index.query(
            user_id,
            cls.status == status,
            limit=limit,
            scan_index_forward=False
        )
    
    @classmethod
    def list_by_user_and_genre(cls, user_id: str, genre: str, limit: int = 10):
        """사용자의 특정 장르 책 목록 조회"""
        return cls.genre_index.query(
            user_id,
            cls.genre == genre,
            limit=limit,
            scan_index_forward=False
        )
    
    def to_dict(self) -> dict:
        """모델을 딕셔너리로 변환"""
        return {
            'user_id': self.user_id,
            'book_id': self.book_id,
            'title': self.title,
            'author': self.author,
            'description': self.description,
            'genre': self.genre,
            'language': self.language,
            'isbn': self.isbn,
            'publisher': self.publisher,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'status': self.status,
            'total_chapters': self.total_chapters,
            'total_duration': self.total_duration,
            'cover_image_url': self.cover_image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

