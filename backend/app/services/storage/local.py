"""Railway 및 로컬 개발 환경에서 사용하는 파일 스토리지 구현."""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from datetime import datetime
from typing import BinaryIO, Dict, List, Optional, Union

import aiofiles

from app.core.config import settings

from .base import BaseStorageService, FileInfo, UploadResult


class LocalStorageService(BaseStorageService):
    """로컬 파일 시스템을 사용한 스토리지 서비스."""

    def __init__(self) -> None:
        # 설정된 기본 경로가 쓰기 불가한 경우를 대비하여 안전한 경로로 폴백
        configured_base = getattr(settings, "LOCAL_STORAGE_PATH", "./storage")
        self.base_path = self._choose_base_path(
            [
                configured_base,
                "/app/storage",
                "/tmp/storage",
            ]
        )
        port = getattr(settings, "PORT", 8000) or 8000
        self.base_url = (
            getattr(settings, "PUBLIC_STORAGE_URL", None)
            or f"http://localhost:{port}/storage"
        )
        self._ensure_directories()

    # ------------------------------------------------------------------
    # 내부 유틸리티
    # ------------------------------------------------------------------
    def _full_path(self, key: str) -> str:
        return os.path.join(self.base_path, key.lstrip("/"))

    def _metadata_path(self, key: str) -> str:
        return self._full_path(key) + ".metadata"

    def _ensure_directories(self) -> None:
        # 설정상의 하위 경로가 /data 기반으로 지정되어 있더라도, 실제 쓰기 가능한 base_path 하위로 생성
        directories = [
            self.base_path,
            os.path.join(self.base_path, "uploads"),
            os.path.join(self.base_path, "media"),
            os.path.join(self.base_path, "books"),
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def _is_writable_dir(self, path: str) -> bool:
        try:
            os.makedirs(path, exist_ok=True)
            test_file = os.path.join(path, ".write_test")
            with open(test_file, "w") as fp:
                fp.write("ok")
            os.remove(test_file)
            return True
        except Exception:
            return False

    def _choose_base_path(self, candidates: List[str]) -> str:
        for p in candidates:
            if not p:
                continue
            if self._is_writable_dir(p):
                return p
        # 최후 수단: 저장소 디렉토리 생성 (상대 경로)
        fallback = "./storage"
        os.makedirs(fallback, exist_ok=True)
        return fallback

    def _cleanup_empty_dirs(self, start_dir: str) -> None:
        current = start_dir
        while current.startswith(self.base_path):
            try:
                os.rmdir(current)
            except OSError:
                break
            current = os.path.dirname(current)

    async def _save_metadata(self, key: str, metadata: Dict[str, str]) -> None:
        path = self._metadata_path(key)
        async with aiofiles.open(path, "w") as fp:
            await fp.write(json.dumps(metadata))

    async def _load_metadata(self, key: str) -> Optional[Dict[str, str]]:
        path = self._metadata_path(key)
        if not os.path.exists(path):
            return None
        async with aiofiles.open(path, "r") as fp:
            data = await fp.read()
        try:
            return json.loads(data) if data else None
        except json.JSONDecodeError:
            return None

    async def _delete_metadata(self, key: str) -> None:
        path = self._metadata_path(key)
        if os.path.exists(path):
            os.remove(path)

    async def _generate_etag(self, full_path: str) -> Optional[str]:
        import hashlib

        if not os.path.exists(full_path):
            return None
        loop = asyncio.get_event_loop()

        def _hash() -> str:
            hasher = hashlib.md5()
            with open(full_path, "rb") as fp:
                for chunk in iter(lambda: fp.read(8192), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()

        return await loop.run_in_executor(None, _hash)

    # ------------------------------------------------------------------
    # BaseStorageService 구현
    # ------------------------------------------------------------------
    async def upload_file(
        self,
        file_data: Union[BinaryIO, bytes],
        key: str,
        content_type: str,
        metadata: Optional[Dict[str, str]] = None,
    ) -> UploadResult:
        full_path = self._full_path(key)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # BytesIO 또는 UploadFile 지원
        if hasattr(file_data, "seek"):
            file_data.seek(0)

        data: Union[bytes, str]
        reader = getattr(file_data, "read", None)
        if callable(reader):
            result = reader()
            if inspect.isawaitable(result):
                result = await result
            data = result
        else:
            data = file_data  # type: ignore[assignment]
        if isinstance(data, str):
            data = data.encode("utf-8")

        async with aiofiles.open(full_path, "wb") as fp:
            await fp.write(data)

        if metadata:
            await self._save_metadata(key, metadata)

        return UploadResult(
            success=True,
            key=key,
            size=len(data),
            url=self._build_url(key),
        )

    async def download_file(self, key: str) -> Optional[bytes]:
        full_path = self._full_path(key)
        if not os.path.exists(full_path):
            return None
        async with aiofiles.open(full_path, "rb") as fp:
            return await fp.read()

    async def delete_file(self, key: str) -> bool:
        full_path = self._full_path(key)
        if not os.path.exists(full_path):
            return False

        os.remove(full_path)
        await self._delete_metadata(key)
        self._cleanup_empty_dirs(os.path.dirname(full_path))
        return True

    async def file_exists(self, key: str) -> bool:
        return os.path.exists(self._full_path(key))

    async def get_file_info(self, key: str) -> Optional[FileInfo]:
        full_path = self._full_path(key)
        if not os.path.exists(full_path):
            return None

        stat = os.stat(full_path)
        metadata = await self._load_metadata(key)
        etag = await self._generate_etag(full_path)

        return FileInfo(
            key=key,
            size=stat.st_size,
            content_type=self.get_content_type(key),
            etag=etag,
            last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            metadata=metadata,
        )

    async def list_files(self, prefix: str = "", limit: int = 100) -> List[FileInfo]:
        files: List[FileInfo] = []
        root = self._full_path(prefix) if prefix else self.base_path

        if not os.path.exists(root):
            return files

        for directory, _, filenames in os.walk(root):
            for filename in filenames:
                if filename.endswith(".metadata") or filename.startswith("."):
                    continue
                relative = os.path.relpath(
                    os.path.join(directory, filename), self.base_path
                )
                info = await self.get_file_info(relative.replace(os.sep, "/"))
                if info:
                    files.append(info)
                    if len(files) >= limit:
                        return files
        return files

    async def get_download_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        return self._build_url(key) if await self.file_exists(key) else None

    async def get_upload_url(
        self,
        key: str,
        content_type: str,
        expires_in: int = 3600,
    ) -> Optional[str]:
        # 로컬 환경에서는 사전 서명 URL 대신 같은 경로를 반환
        return self._build_url(key)

    # ------------------------------------------------------------------
    # 헬퍼
    # ------------------------------------------------------------------
    def _build_url(self, key: str) -> str:
        return f"{self.base_url}/{key.lstrip('/')}"


__all__ = ["LocalStorageService"]
