"""
VOJ Audiobooks API - AudioChapter 모델
오디오 챕터 정보를 저장하는 DynamoDB 모델
"""
from pynamodb.attributes import (
    UnicodeAttribute, NumberAttribute, BooleanAttribute,
    UTCDateTimeAttribute, MapAttribute
)
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from datetime import datetime
from typing import Optional, Dict, Any

from app.core.config import settings
from .base import BaseModel


class BookChaptersIndex(GlobalSecondaryIndex):
    """책별 챕터 인덱스"""
    
    class Meta:
        index_name = "book-chapters-index"
        projection = AllProjection()
        read_capacity_units = 5
        write_capacity_units = 5
    
    book_id = UnicodeAttribute(hash_key=True)
    chapter_number = NumberAttribute(range_key=True)


class ChapterStatusIndex(GlobalSecondaryIndex):
    """챕터 상태별 인덱스"""
    
    class Meta:
        index_name = "status-index"
        projection = AllProjection()
        read_capacity_units = 5
        write_capacity_units = 5
    
    status = UnicodeAttribute(hash_key=True)
    created_at = UTCDateTimeAttribute(range_key=True)


class AudioMetadata(MapAttribute):
    """오디오 메타데이터"""
    duration = NumberAttribute()  # 재생 시간 (초)
    bitrate = NumberAttribute(null=True)  # 비트레이트
    sample_rate = NumberAttribute(null=True)  # 샘플링 레이트
    channels = NumberAttribute(null=True)  # 채널 수
    format = UnicodeAttribute(null=True)  # 파일 형식


class FileInfo(MapAttribute):
    """파일 정보"""
    original_name = UnicodeAttribute()  # 원본 파일명
    file_size = NumberAttribute()  # 파일 크기 (바이트)
    mime_type = UnicodeAttribute()  # MIME 타입
    s3_key = UnicodeAttribute(null=True)  # S3 키 (프로덕션)
    local_path = UnicodeAttribute(null=True)  # 로컬 경로 (개발)


class AudioChapter(BaseModel):
    """오디오 챕터 모델"""
    
    class Meta:
        table_name = settings.AUDIO_CHAPTERS_TABLE_NAME
        region = settings.AWS_REGION
        
        # 환경별 엔드포인트 설정
        if settings.ENVIRONMENT == "local" and settings.DYNAMODB_ENDPOINT_URL:
            host = settings.DYNAMODB_ENDPOINT_URL
            aws_access_key_id = "dummy"
            aws_secret_access_key = "dummy"
    
    # Primary Key
    chapter_id = UnicodeAttribute(hash_key=True, attr_name="chapter_id")
    book_id = UnicodeAttribute(attr_name="book_id")
    
    # 챕터 기본 정보
    chapter_number = NumberAttribute(attr_name="chapter_number")
    title = UnicodeAttribute(attr_name="title")
    description = UnicodeAttribute(null=True, attr_name="description")
    
    # 파일 및 처리 상태
    status = UnicodeAttribute(default="uploading", attr_name="status")  # uploading, processing, ready, error
    error_message = UnicodeAttribute(null=True, attr_name="error_message")
    
    # 파일 정보
    file_info = FileInfo(attr_name="file_info")
    audio_metadata = AudioMetadata(null=True, attr_name="audio_metadata")
    
    # 처리 정보
    processing_started_at = UTCDateTimeAttribute(null=True, attr_name="processing_started_at")
    processing_completed_at = UTCDateTimeAttribute(null=True, attr_name="processing_completed_at")
    
    # 인덱스
    book_chapters_index = BookChaptersIndex()
    status_index = ChapterStatusIndex()
    
    @classmethod
    def get_by_id(cls, chapter_id: str) -> Optional['AudioChapter']:
        """챕터 ID로 챕터 조회"""
        try:
            return cls.get(chapter_id)
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def list_by_book(cls, book_id: str, limit: int = 50):
        """책의 챕터 목록 조회 (챕터 번호 순)"""
        return cls.book_chapters_index.query(
            book_id,
            limit=limit,
            scan_index_forward=True  # 챕터 번호 오름차순
        )
    
    @classmethod
    def list_by_status(cls, status: str, limit: int = 10):
        """상태별 챕터 목록 조회"""
        return cls.status_index.query(
            status,
            limit=limit,
            scan_index_forward=False  # 최신순
        )
    
    @classmethod
    def get_next_chapter_number(cls, book_id: str) -> int:
        """다음 챕터 번호 계산"""
        try:
            chapters = list(cls.book_chapters_index.query(
                book_id,
                scan_index_forward=False,  # 최신 챕터부터
                limit=1
            ))
            
            if chapters:
                return chapters[0].chapter_number + 1
            return 1
        except Exception:
            return 1
    
    def mark_processing_started(self):
        """처리 시작 표시"""
        self.status = "processing"
        self.processing_started_at = datetime.utcnow()
        self.save()
    
    def mark_processing_completed(self, audio_metadata: Dict[str, Any]):
        """처리 완료 표시"""
        self.status = "ready"
        self.processing_completed_at = datetime.utcnow()
        self.audio_metadata = AudioMetadata(**audio_metadata)
        self.save()
    
    def mark_processing_error(self, error_message: str):
        """처리 오류 표시"""
        self.status = "error"
        self.error_message = error_message
        self.save()
    
    def to_dict(self) -> dict:
        """모델을 딕셔너리로 변환"""
        result = {
            'chapter_id': self.chapter_id,
            'book_id': self.book_id,
            'chapter_number': self.chapter_number,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'processing_started_at': self.processing_started_at.isoformat() if self.processing_started_at else None,
            'processing_completed_at': self.processing_completed_at.isoformat() if self.processing_completed_at else None,
        }
        
        # 파일 정보 추가
        if self.file_info:
            result['file_info'] = {
                'original_name': self.file_info.original_name,
                'file_size': self.file_info.file_size,
                'mime_type': self.file_info.mime_type,
                's3_key': self.file_info.s3_key if hasattr(self.file_info, 's3_key') else None,
                'local_path': self.file_info.local_path if hasattr(self.file_info, 'local_path') else None,
            }
        
        # 오디오 메타데이터 추가
        if self.audio_metadata:
            result['audio_metadata'] = {
                'duration': self.audio_metadata.duration,
                'bitrate': self.audio_metadata.bitrate if hasattr(self.audio_metadata, 'bitrate') else None,
                'sample_rate': self.audio_metadata.sample_rate if hasattr(self.audio_metadata, 'sample_rate') else None,
                'channels': self.audio_metadata.channels if hasattr(self.audio_metadata, 'channels') else None,
                'format': self.audio_metadata.format if hasattr(self.audio_metadata, 'format') else None,
            }
        
        return result

