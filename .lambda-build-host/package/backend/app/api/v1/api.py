"""
VOJ Audiobooks API - v1 API 라우터
모든 v1 엔드포인트를 통합하는 메인 라우터
"""
from fastapi import APIRouter

from app.api.v1.endpoints import books, audio, auth, health, files, websocket, logs

# API v1 메인 라우터
api_router = APIRouter()

# 각 엔드포인트 라우터 등록
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(books.router, prefix="/books", tags=["books"])
api_router.include_router(audio.router, prefix="/audio", tags=["audio"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
api_router.include_router(logs.router, prefix="/logs", tags=["logs"])
