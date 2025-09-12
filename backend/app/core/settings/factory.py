"""
VOJ Audiobooks API - 설정 팩토리
환경에 따라 적절한 설정 클래스를 반환하는 팩토리
"""
import os
from typing import Type
from .base import BaseAppSettings
from .local import LocalSettings
from .production import ProductionSettings


class SettingsFactory:
    """환경별 설정을 생성하는 팩토리 클래스"""
    
    @staticmethod
    def get_settings() -> BaseAppSettings:
        """
        환경 변수를 기반으로 적절한 설정 인스턴스를 반환
        
        Returns:
            BaseAppSettings: 환경에 맞는 설정 인스턴스
        """
        environment = os.getenv("ENVIRONMENT", "local").lower()
        
        if environment == "local":
            return LocalSettings()
        elif environment == "production":
            return ProductionSettings()
        else:
            # 기본값으로 로컬 설정 사용
            return LocalSettings()
    
    @staticmethod
    def get_settings_class(environment: str) -> Type[BaseAppSettings]:
        """
        환경 이름으로 설정 클래스를 반환
        
        Args:
            environment: 환경 이름 ('local', 'production')
            
        Returns:
            Type[BaseAppSettings]: 설정 클래스
        """
        environment = environment.lower()
        
        if environment == "local":
            return LocalSettings
        elif environment == "production":
            return ProductionSettings
        else:
            return LocalSettings


# 전역 설정 인스턴스
settings = SettingsFactory.get_settings()

