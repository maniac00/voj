"""스토리지 서비스 기본 인터페이스와 데이터 구조."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, BinaryIO, Dict, List, Optional


@dataclass
class FileInfo:
    """스토리지에 저장된 단일 파일 정보."""

    key: str
    size: int
    content_type: str
    etag: Optional[str] = None
    last_modified: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


@dataclass
class UploadResult:
    """파일 업로드 결과."""

    success: bool
    key: str
    size: int
    url: Optional[str] = None
    error: Optional[str] = None


class BaseStorageService(ABC):
    """스토리지 서비스가 구현해야 하는 공통 인터페이스."""

    @abstractmethod
    async def upload_file(
        self,
        file_data: BinaryIO,
        key: str,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        """파일을 업로드하고 결과를 반환한다."""

    @abstractmethod
    async def download_file(self, key: str) -> Optional[bytes]:
        """저장소에서 파일을 읽어 바이트로 반환한다."""

    @abstractmethod
    async def delete_file(self, key: str) -> bool:
        """파일을 삭제하고 성공 여부를 반환한다."""

    @abstractmethod
    async def file_exists(self, key: str) -> bool:
        """파일 존재 여부를 확인한다."""

    @abstractmethod
    async def get_file_info(self, key: str) -> Optional[FileInfo]:
        """파일의 메타데이터를 조회한다."""

    @abstractmethod
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[FileInfo]:
        """prefix 기준으로 파일 목록을 반환한다."""

    @abstractmethod
    async def get_download_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """다운로드 URL을 생성한다."""

    @abstractmethod
    async def get_upload_url(
        self,
        key: str,
        content_type: str,
        expires_in: int = 3600,
    ) -> Optional[str]:
        """사전 서명된 업로드 URL을 생성한다."""

    def generate_key(
        self,
        user_id: str,
        book_id: str,
        filename: str,
        prefix: str = "uploads",
    ) -> str:
        """파일 저장에 사용할 표준 키를 생성한다."""

        safe_filename = os.path.basename(filename).replace(" ", "_")
        return f"book/{book_id}/{prefix}/{safe_filename}"

    def get_content_type(self, filename: str) -> str:
        """파일 확장자 기반 Content-Type을 추정한다."""

        _, ext = os.path.splitext(filename.lower())
        return {
            ".mp3": "audio/mpeg",
            ".wav": "audio/wav",
            ".m4a": "audio/mp4",
            ".flac": "audio/flac",
            ".aac": "audio/aac",
            ".ogg": "audio/ogg",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
            ".txt": "text/plain",
        }.get(ext, "application/octet-stream")


__all__ = ["BaseStorageService", "FileInfo", "UploadResult"]
