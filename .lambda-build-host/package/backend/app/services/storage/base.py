"""
VOJ Audiobooks API - 스토리지 기본 인터페이스
파일 스토리지를 위한 추상 기본 클래스
"""
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Dict, Any, List
from dataclasses import dataclass
import os


@dataclass
class FileInfo:
    """파일 정보"""
    key: str  # 파일 키/경로
    size: int  # 파일 크기 (바이트)
    content_type: str  # MIME 타입
    etag: Optional[str] = None  # ETag (S3용)
    last_modified: Optional[str] = None  # 마지막 수정 시간
    metadata: Optional[Dict[str, str]] = None  # 추가 메타데이터


@dataclass
class UploadResult:
    """업로드 결과"""
    success: bool
    key: str
    size: int
    url: Optional[str] = None  # 접근 URL (있는 경우)
    error: Optional[str] = None  # 오류 메시지


class BaseStorageService(ABC):
    """스토리지 서비스 기본 인터페이스"""
    
    @abstractmethod
    async def upload_file(
        self, 
        file_data: BinaryIO, 
        key: str, 
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        """
        파일 업로드
        
        Args:
            file_data: 파일 데이터
            key: 저장할 키/경로
            content_type: MIME 타입
            metadata: 추가 메타데이터
            
        Returns:
            UploadResult: 업로드 결과
        """
        pass
    
    @abstractmethod
    async def download_file(self, key: str) -> Optional[bytes]:
        """
        파일 다운로드
        
        Args:
            key: 파일 키/경로
            
        Returns:
            bytes: 파일 데이터 (없으면 None)
        """
        pass
    
    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        """
        파일 삭제
        
        Args:
            key: 파일 키/경로
            
        Returns:
            bool: 삭제 성공 여부
        """
        pass
    
    @abstractmethod
    async def file_exists(self, key: str) -> bool:
        """
        파일 존재 여부 확인
        
        Args:
            key: 파일 키/경로
            
        Returns:
            bool: 존재 여부
        """
        pass
    
    @abstractmethod
    async def get_file_info(self, key: str) -> Optional[FileInfo]:
        """
        파일 정보 조회
        
        Args:
            key: 파일 키/경로
            
        Returns:
            FileInfo: 파일 정보 (없으면 None)
        """
        pass
    
    @abstractmethod
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[FileInfo]:
        """
        파일 목록 조회
        
        Args:
            prefix: 접두사 필터
            limit: 최대 개수
            
        Returns:
            List[FileInfo]: 파일 목록
        """
        pass
    
    @abstractmethod
    async def get_download_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """
        다운로드 URL 생성
        
        Args:
            key: 파일 키/경로
            expires_in: 만료 시간 (초)
            
        Returns:
            str: 다운로드 URL (없으면 None)
        """
        pass
    
    @abstractmethod
    async def get_upload_url(
        self, 
        key: str, 
        content_type: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """
        업로드 URL 생성 (Pre-signed URL)
        
        Args:
            key: 파일 키/경로
            content_type: MIME 타입
            expires_in: 만료 시간 (초)
            
        Returns:
            str: 업로드 URL (없으면 None)
        """
        pass
    
    def generate_key(self, user_id: str, book_id: str, filename: str, prefix: str = "uploads") -> str:
        """
        파일 키 생성
        
        Args:
            user_id: 사용자 ID
            book_id: 책 ID
            filename: 파일명
            prefix: 접두사
            
        Returns:
            str: 생성된 키
        """
        # 안전한 파일명 생성 (공백 제거)
        safe_filename = filename.replace(' ', '_')
        # 표준 경로: book/<book_id>/<prefix>/<filename>
        return f"book/{book_id}/{prefix}/{safe_filename}"
    
    def get_content_type(self, filename: str) -> str:
        """
        파일명으로부터 Content-Type 추정
        
        Args:
            filename: 파일명
            
        Returns:
            str: Content-Type
        """
        _, ext = os.path.splitext(filename.lower())
        
        content_types = {
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.flac': 'audio/flac',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.json': 'application/json',
        }
        
        return content_types.get(ext, 'application/octet-stream')

