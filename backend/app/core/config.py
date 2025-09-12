"""
VOJ Audiobooks API - 설정 관리 (호환성 유지용)
기존 코드와의 호환성을 위한 설정 모듈
새로운 설정 시스템을 사용하도록 리다이렉트
"""
from .settings.factory import settings

# 기존 코드와의 호환성을 위해 settings를 그대로 export
__all__ = ["settings"]
