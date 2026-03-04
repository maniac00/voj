"""
VOJ Audiobooks API - 로컬 파일 스토리지 서비스
로컬 파일 시스템을 사용한 스토리지 구현
"""
import os
import shutil
import aiofiles
from typing import Optional, BinaryIO, Dict, List
from datetime import datetime
import hashlib

from app.core.config import settings
from .base import BaseStorageService, FileInfo, UploadResult


class LocalStorageService(BaseStorageService):
    """로컬 파일 시스템 스토리지 서비스"""
    
    def __init__(self):
        self.base_path = settings.LOCAL_STORAGE_PATH
        self.base_url = f"http://localhost:{settings.PORT}/storage"
        
        # 기본 디렉토리 생성
        self._ensure_directories()
    
    def _ensure_directories(self):
        """필요한 디렉토리들을 생성"""
        directories = [
            self.base_path,
            settings.LOCAL_UPLOADS_PATH,
            settings.LOCAL_MEDIA_PATH,
            settings.LOCAL_BOOKS_PATH,
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def _get_full_path(self, key: str) -> str:
        """키로부터 전체 파일 경로 생성"""
        return os.path.join(self.base_path, key.lstrip('/'))
    
    def _get_url(self, key: str) -> str:
        """키로부터 접근 URL 생성"""
        return f"{self.base_url}/{key.lstrip('/')}"
    
    async def upload_file(
        self, 
        file_data: BinaryIO, 
        key: str, 
        content_type: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UploadResult:
        """파일 업로드"""
        try:
            full_path = self._get_full_path(key)
            
            # 디렉토리 생성
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # 파일 저장
            file_size = 0
            async with aiofiles.open(full_path, 'wb') as f:
                if hasattr(file_data, 'read'):
                    # 파일 객체인 경우
                    content = file_data.read()
                    if isinstance(content, str):
                        content = content.encode('utf-8')
                    await f.write(content)
                    file_size = len(content)
                else:
                    # 바이트 데이터인 경우
                    await f.write(file_data)
                    file_size = len(file_data)
            
            # 메타데이터 저장 (확장 속성 또는 별도 파일)
            if metadata:
                await self._save_metadata(key, metadata)
            
            return UploadResult(
                success=True,
                key=key,
                size=file_size,
                url=self._get_url(key)
            )
            
        except Exception as e:
            return UploadResult(
                success=False,
                key=key,
                size=0,
                error=str(e)
            )
    
    async def download_file(self, key: str) -> Optional[bytes]:
        """파일 다운로드"""
        try:
            full_path = self._get_full_path(key)
            
            if not os.path.exists(full_path):
                return None
            
            async with aiofiles.open(full_path, 'rb') as f:
                return await f.read()
                
        except Exception:
            return None
    
    async def delete_file(self, key: str) -> bool:
        """파일 삭제"""
        try:
            full_path = self._get_full_path(key)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                
                # 메타데이터도 삭제
                await self._delete_metadata(key)
                
                # 빈 디렉토리 정리
                self._cleanup_empty_directories(os.path.dirname(full_path))
                
                return True
            return False
            
        except Exception:
            return False
    
    async def file_exists(self, key: str) -> bool:
        """파일 존재 여부 확인"""
        full_path = self._get_full_path(key)
        return os.path.exists(full_path)
    
    async def get_file_info(self, key: str) -> Optional[FileInfo]:
        """파일 정보 조회"""
        try:
            full_path = self._get_full_path(key)
            
            if not os.path.exists(full_path):
                return None
            
            stat = os.stat(full_path)
            
            # 메타데이터 로드
            metadata = await self._load_metadata(key)
            
            # ETag 생성 (파일 내용 기반)
            etag = await self._generate_etag(full_path)
            
            return FileInfo(
                key=key,
                size=stat.st_size,
                content_type=self.get_content_type(key),
                etag=etag,
                last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                metadata=metadata
            )
            
        except Exception:
            return None
    
    async def list_files(self, prefix: str = "", limit: int = 100) -> List[FileInfo]:
        """파일 목록 조회"""
        files = []
        prefix_path = self._get_full_path(prefix) if prefix else self.base_path
        
        try:
            count = 0
            for root, dirs, filenames in os.walk(prefix_path):
                if count >= limit:
                    break
                    
                for filename in filenames:
                    if count >= limit:
                        break
                    
                    if filename.startswith('.') or filename.endswith('.metadata'):  # 숨김 파일 및 메타데이터 파일 제외
                        continue
                    
                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, self.base_path)
                    key = relative_path.replace(os.sep, '/')
                    
                    file_info = await self.get_file_info(key)
                    if file_info:
                        files.append(file_info)
                        count += 1
            
            return files
            
        except Exception:
            return []
    
    async def get_download_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """다운로드 URL 생성"""
        if await self.file_exists(key):
            return self._get_url(key)
        return None
    
    async def get_upload_url(
        self, 
        key: str, 
        content_type: str,
        expires_in: int = 3600
    ) -> Optional[str]:
        """업로드 URL 생성 (로컬에서는 직접 업로드 사용)"""
        # 로컬 환경에서는 Pre-signed URL 대신 직접 업로드 엔드포인트 반환
        return f"{self.base_url}/upload/{key}"
    
    async def _save_metadata(self, key: str, metadata: Dict[str, str]):
        """메타데이터 저장"""
        try:
            metadata_path = self._get_full_path(f"{key}.metadata")
            os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
            
            import json
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata))
        except Exception:
            pass  # 메타데이터 저장 실패는 무시
    
    async def _load_metadata(self, key: str) -> Optional[Dict[str, str]]:
        """메타데이터 로드"""
        try:
            metadata_path = self._get_full_path(f"{key}.metadata")
            
            if not os.path.exists(metadata_path):
                return None
            
            import json
            async with aiofiles.open(metadata_path, 'r') as f:
                content = await f.read()
                return json.loads(content)
        except Exception:
            return None
    
    async def _delete_metadata(self, key: str):
        """메타데이터 삭제"""
        try:
            metadata_path = self._get_full_path(f"{key}.metadata")
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
        except Exception:
            pass
    
    async def _generate_etag(self, file_path: str) -> str:
        """파일의 ETag 생성"""
        try:
            hasher = hashlib.md5()
            async with aiofiles.open(file_path, 'rb') as f:
                chunk = await f.read(8192)
                while chunk:
                    hasher.update(chunk)
                    chunk = await f.read(8192)
            return hasher.hexdigest()
        except Exception:
            return ""
    
    def _cleanup_empty_directories(self, directory: str):
        """빈 디렉토리 정리"""
        try:
            if directory != self.base_path and os.path.exists(directory):
                if not os.listdir(directory):  # 디렉토리가 비어있으면
                    os.rmdir(directory)
                    # 상위 디렉토리도 확인
                    self._cleanup_empty_directories(os.path.dirname(directory))
        except Exception:
            pass
