"""
Firebase Admin SDK 초기화 및 토큰 검증 모듈
"""
import json
import logging
from typing import Optional

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_app: Optional[firebase_admin.App] = None


def init_firebase() -> bool:
    """Firebase Admin SDK를 초기화한다. 이미 초기화되었으면 건너뛴다."""
    global _firebase_app

    if _firebase_app is not None:
        return True

    sa_json = settings.FIREBASE_SERVICE_ACCOUNT_JSON
    if not sa_json:
        logger.warning("FIREBASE_SERVICE_ACCOUNT_JSON is not set; Firebase auth disabled")
        return False

    try:
        sa_dict = json.loads(sa_json)
        cred = credentials.Certificate(sa_dict)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
        return True
    except Exception as e:
        logger.error("Failed to initialize Firebase Admin SDK: %s", e)
        return False


def is_firebase_initialized() -> bool:
    """Firebase가 초기화되었는지 확인한다."""
    return _firebase_app is not None


def verify_firebase_token(id_token: str) -> dict:
    """
    Firebase ID 토큰을 검증하고 디코딩된 클레임을 반환한다.
    반환값: {"uid": ..., "email": ..., "name": ..., "picture": ..., ...}
    """
    if not is_firebase_initialized():
        raise ValueError("Firebase is not initialized")

    decoded = firebase_auth.verify_id_token(id_token)
    return decoded
