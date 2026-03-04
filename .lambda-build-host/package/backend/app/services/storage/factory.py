"""
VOJ Audiobooks API - 스토리지 팩토리
환경에 따라 적절한 스토리지 서비스를 제공하는 팩토리
"""
from typing import Type

from app.core.config import settings
from .base import BaseStorageService
from .local import LocalStorageService
from .s3 import S3StorageService


class StorageServiceFactory:
    """스토리지 서비스 팩토리"""
    
    @staticmethod
    def get_storage_service() -> BaseStorageService:
        """
        환경에 따라 적절한 스토리지 서비스 인스턴스를 반환
        
        Returns:
            BaseStorageService: 스토리지 서비스 인스턴스
        """
        if settings.ENVIRONMENT == "local":
            return LocalStorageService()
        elif settings.ENVIRONMENT == "production":
            return S3StorageService()
        else:
            # 기본값으로 로컬 스토리지 사용
            return LocalStorageService()
    
    @staticmethod
    def get_storage_service_class(environment: str) -> Type[BaseStorageService]:
        """
        환경 이름으로 스토리지 서비스 클래스를 반환
        
        Args:
            environment: 환경 이름 ('local', 'production')
            
        Returns:
            Type[BaseStorageService]: 스토리지 서비스 클래스
        """
        environment = environment.lower()
        
        if environment == "local":
            return LocalStorageService
        elif environment == "production":
            return S3StorageService
        else:
            return LocalStorageService


# 전역 스토리지 서비스 인스턴스
storage_service = StorageServiceFactory.get_storage_service()

