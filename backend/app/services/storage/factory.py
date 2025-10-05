"""환경에 맞는 스토리지 서비스를 제공하는 팩토리."""

from __future__ import annotations

from typing import Type

from app.core.config import settings

from .base import BaseStorageService
from .local import LocalStorageService
# from .s3 import S3StorageService  # AWS 사용 중단


class StorageServiceFactory:
    """환경 변수에 맞춰 올바른 스토리지 구현을 반환한다."""

    @staticmethod
    def get_storage_service() -> BaseStorageService:
        environment = (settings.ENVIRONMENT or "local").lower()

        # 프로덕션 포함 전 환경 Railway 로컬 볼륨 사용
        # if environment == "production":
        #     return S3StorageService()

        # Railway 및 local은 동일하게 로컬 볼륨을 사용
        return LocalStorageService()

    @staticmethod
    def get_storage_service_class(environment: str) -> Type[BaseStorageService]:
        name = (environment or "local").lower()
        # if name == "production":
        #     return S3StorageService
        return LocalStorageService


storage_service: BaseStorageService = StorageServiceFactory.get_storage_service()

__all__ = ["StorageServiceFactory", "storage_service"]
