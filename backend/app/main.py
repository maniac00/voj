"""
VOJ Audiobooks API - FastAPI 메인 애플리케이션
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.services.websocket.log_streamer import setup_websocket_logging

# FastAPI 애플리케이션 인스턴스 생성
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="VOJ Audiobooks - 오디오북 스트리밍 플랫폼 API",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT == "local" else None,
    docs_url="/docs" if settings.ENVIRONMENT == "local" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "local" else None,
)

# CORS 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ORIGINS", ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Trusted Host 미들웨어 설정 (프로덕션 환경)
# ALLOWED_HOSTS에 '*'가 포함되면 신뢰 호스트 검사 비활성화 (ALB 헬스체크/내부 트래픽 허용)
allowed_hosts = getattr(settings, "ALLOWED_HOSTS", [])
if settings.ENVIRONMENT == "production" and allowed_hosts and "*" not in allowed_hosts:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )

# API 라우터 등록
app.include_router(api_router, prefix=settings.API_V1_STR)

# 애플리케이션 이벤트 핸들러
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    try:
        setup_websocket_logging()
    except Exception as e:
        print(f"Warning: Failed to initialize application components: {e}")

@app.on_event("shutdown") 
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    try:
        pass
    except Exception as e:
        print(f"Warning: Failed to cleanup application components: {e}")


@app.get("/")
async def root():
    """루트 엔드포인트 - API 상태 확인"""
    return {
        "message": "VOJ Audiobooks API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "local",
        log_level="info"
    )
