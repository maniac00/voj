"""
VOJ Audiobooks API - 인증 엔드포인트
- 관리자 웹: HMAC 토큰 로그인
- 모바일 앱: Firebase Google 로그인
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth.simple import (
    authenticate_user,
    create_simple_token,
    get_current_user_claims,
)
from app.core.audit import log_login_success, log_login_failure, log_firebase_login

router = APIRouter()


class LoginRequest(BaseModel):
    """로그인 요청 모델"""

    username: Optional[str] = None
    email: Optional[str] = None
    password: str

    @property
    def effective_username(self) -> str:
        return self.username or self.email or ""


class LoginResponse(BaseModel):
    """로그인 응답 모델"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str


class FirebaseLoginRequest(BaseModel):
    """Firebase 로그인 요청 모델"""

    id_token: str


class FirebaseLoginResponse(BaseModel):
    """Firebase 로그인 응답 모델"""

    user_id: int
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    status: str
    role: str
    is_new_user: bool


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest) -> LoginResponse:
    """
    관리자 웹 HMAC 토큰 로그인
    """
    username = login_data.effective_username
    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email is required",
        )

    if not authenticate_user(username, login_data.password):
        log_login_failure(username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    log_login_success(username)
    access_token = create_simple_token(username)

    return LoginResponse(
        access_token=access_token,
        expires_in=86400,
        username=username,
    )


@router.post("/firebase-login", response_model=FirebaseLoginResponse)
async def firebase_login(body: FirebaseLoginRequest) -> FirebaseLoginResponse:
    """
    모바일 앱 Firebase 로그인
    - Firebase ID 토큰 검증
    - 신규 사용자 자동 생성 (pending 상태)
    - ADMIN_EMAILS에 해당하면 자동 승인
    """
    from app.core.auth.firebase import is_firebase_initialized, verify_firebase_token
    from app.models.database import SessionLocal
    from app.services.user_service import UserService

    if not is_firebase_initialized():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase authentication is not configured",
        )

    try:
        decoded = verify_firebase_token(body.id_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {e}",
        )

    firebase_uid = decoded.get("uid", "")
    email = decoded.get("email", "")
    display_name = decoded.get("name", "")
    photo_url = decoded.get("picture", "")

    db = SessionLocal()
    try:
        # 기존 사용자 확인 (새 사용자 여부 판단용)
        existing = UserService.get_user_by_firebase_uid(db, firebase_uid)
        is_new = existing is None

        user = UserService.get_or_create_user(
            db,
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            photo_url=photo_url,
        )

        log_firebase_login(email, firebase_uid, is_new)

        # 신규 사용자(pending)인 경우 Telegram으로 관리자에게 알림
        if is_new and user.status.value == "pending":
            from app.core import telegram as tg
            tg.send_new_user_notification(
                user_id=user.id,
                email=user.email,
                display_name=user.display_name,
            )

        return FirebaseLoginResponse(
            user_id=user.id,
            email=user.email,
            display_name=user.display_name,
            photo_url=user.photo_url,
            status=user.status.value,
            role=user.role.value,
            is_new_user=is_new,
        )
    finally:
        db.close()


@router.post("/logout")
async def logout() -> Dict[str, str]:
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> Dict[str, Any]:
    return {
        "sub": claims.get("sub"),
        "username": claims.get("username"),
        "scope": claims.get("scope"),
        "email": claims.get("email"),
        "status": claims.get("status"),
        "role": claims.get("role"),
        "auth_type": claims.get("auth_type"),
    }
