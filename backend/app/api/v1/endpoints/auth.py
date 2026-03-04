"""
VOJ Audiobooks API - 인증 엔드포인트
- 관리자 웹: HMAC 토큰 로그인
- 모바일 앱: Firebase Google 로그인 + 자체 JWT 세션
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.audit import log_firebase_login, log_login_failure, log_login_success
from app.core.auth.mobile_tokens import (
    InvalidRefreshTokenError,
    issue_mobile_tokens,
    revoke_refresh_token,
    rotate_mobile_tokens,
)
from app.core.auth.simple import (
    authenticate_user,
    create_simple_token,
    get_current_user_claims,
)
from app.models.database import get_db
from app.models.user_sql import UserSQL
from app.services.user_service import UserService

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


class MobileLoginRequest(BaseModel):
    """모바일 앱 세션 시작 요청"""

    id_token: str
    device_id: str = Field(..., min_length=1, max_length=255)


class MobileRefreshRequest(BaseModel):
    """모바일 Access Token 재발급 요청"""

    refresh_token: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1, max_length=255)


class MobileLogoutRequest(BaseModel):
    """모바일 Refresh Token 폐기 요청"""

    refresh_token: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1, max_length=255)


class MobileLoginResponse(BaseModel):
    """모바일 로그인/갱신 응답"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    status: str
    role: str
    is_new_user: bool = False


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


def _resolve_user_from_firebase_token(
    db: Session,
    *,
    id_token: str,
) -> tuple[UserSQL, bool, str]:
    from app.core.auth.firebase import is_firebase_initialized, verify_firebase_token

    if not is_firebase_initialized():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase authentication is not configured",
        )

    try:
        decoded = verify_firebase_token(id_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase token: {e}",
        )

    firebase_uid = decoded.get("uid", "")
    email = decoded.get("email", "")
    display_name = decoded.get("name", "")
    photo_url = decoded.get("picture", "")

    if not firebase_uid or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token payload",
        )

    existing = UserService.get_user_by_firebase_uid(db, firebase_uid)
    is_new = existing is None
    user = UserService.get_or_create_user(
        db,
        firebase_uid=firebase_uid,
        email=email,
        display_name=display_name,
        photo_url=photo_url,
    )
    return user, is_new, firebase_uid


def _notify_new_pending_user(user: UserSQL, is_new_user: bool) -> None:
    if not is_new_user:
        return
    if user.status.value != "pending":
        return

    from app.core import telegram as tg

    tg.send_new_user_notification(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
    )


@router.post("/firebase-login", response_model=FirebaseLoginResponse)
async def firebase_login(
    body: FirebaseLoginRequest,
    db: Session = Depends(get_db),
) -> FirebaseLoginResponse:
    """
    모바일 앱 Firebase 로그인 (레거시 호환)
    - Firebase ID 토큰 검증
    - 신규 사용자 자동 생성 (pending 상태)
    - ADMIN_EMAILS에 해당하면 자동 승인
    """
    user, is_new, firebase_uid = _resolve_user_from_firebase_token(
        db,
        id_token=body.id_token,
    )
    log_firebase_login(user.email, firebase_uid, is_new)
    _notify_new_pending_user(user, is_new)

    return FirebaseLoginResponse(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        photo_url=user.photo_url,
        status=user.status.value,
        role=user.role.value,
        is_new_user=is_new,
    )


@router.post("/mobile/login", response_model=MobileLoginResponse)
async def mobile_login(
    body: MobileLoginRequest,
    db: Session = Depends(get_db),
) -> MobileLoginResponse:
    """모바일 앱 로그인 (Firebase 검증 + JWT/Refresh 발급)"""
    user, is_new, firebase_uid = _resolve_user_from_firebase_token(
        db,
        id_token=body.id_token,
    )
    log_firebase_login(user.email, firebase_uid, is_new)
    _notify_new_pending_user(user, is_new)

    tokens = issue_mobile_tokens(
        db,
        user=user,
        device_id=body.device_id,
    )
    return MobileLoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        photo_url=user.photo_url,
        status=user.status.value,
        role=user.role.value,
        is_new_user=is_new,
    )


@router.post("/mobile/refresh", response_model=MobileLoginResponse)
async def mobile_refresh(
    body: MobileRefreshRequest,
    db: Session = Depends(get_db),
) -> MobileLoginResponse:
    """모바일 앱 토큰 갱신 (Refresh rotation 적용)"""
    try:
        user, tokens = rotate_mobile_tokens(
            db,
            refresh_token=body.refresh_token,
            device_id=body.device_id,
        )
    except InvalidRefreshTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )

    return MobileLoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        photo_url=user.photo_url,
        status=user.status.value,
        role=user.role.value,
        is_new_user=False,
    )


@router.post("/mobile/logout")
async def mobile_logout(
    body: MobileLogoutRequest,
    db: Session = Depends(get_db),
) -> Dict[str, str]:
    """모바일 로그아웃 (지정 Refresh Token 폐기)"""
    try:
        revoke_refresh_token(
            db,
            refresh_token=body.refresh_token,
            device_id=body.device_id,
        )
    except InvalidRefreshTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    return {"message": "Logged out successfully"}


@router.post("/logout")
async def logout() -> Dict[str, str]:
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> Dict[str, Any]:
    user_id = claims.get("user_id")
    if user_id is None:
        sub = str(claims.get("sub") or "")
        if sub.isdigit():
            user_id = int(sub)

    return {
        "sub": claims.get("sub"),
        "user_id": user_id,
        "device_id": claims.get("device_id"),
        "username": claims.get("username"),
        "scope": claims.get("scope"),
        "email": claims.get("email"),
        "status": claims.get("status"),
        "role": claims.get("role"),
        "auth_type": claims.get("auth_type"),
    }
