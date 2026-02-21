"""환경에 맞는 스토리지 서비스를 제공하는 팩토리."""

from __future__ import annotations

import logging
from typing import Type

from app.core.config import settings

from .base import BaseStorageService
from .local import LocalStorageService

logger = logging.getLogger(__name__)


class StorageServiceFactory:
    """환경 변수에 맞춰 올바른 스토리지 구현을 반환한다."""

    @staticmethod
    def get_storage_service() -> BaseStorageService:
        environment = (settings.ENVIRONMENT or "local").lower()

        if environment == "production" and settings.R2_ACCOUNT_ID:
            from .r2 import R2StorageService
            logger.info("R2StorageService 사용 (bucket=%s)", settings.R2_BUCKET_NAME)
            return R2StorageService()

        return LocalStorageService()

    @staticmethod
    def get_storage_service_class(environment: str) -> Type[BaseStorageService]:
        name = (environment or "local").lower()
        if name == "production" and settings.R2_ACCOUNT_ID:
            from .r2 import R2StorageService
            return R2StorageService
        return LocalStorageService


storage_service: BaseStorageService = StorageServiceFactory.get_storage_service()

__all__ = ["StorageServiceFactory", "storage_service"]
