"""
VOJ Audiobooks API - 간단한 인증 엔드포인트
하드코딩된 계정 인증(MVP)
- 웹 어드민: admin/qwer1234
- 앱: dev@example.com/qwer1234
"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.auth.simple import (
    authenticate_user,
    create_simple_token,
    get_current_user_claims,
)
from app.core.audit import log_login_success, log_login_failure

router = APIRouter()


class LoginRequest(BaseModel):
    """로그인 요청 모델"""

    username: Optional[str] = None
    email: Optional[str] = None  # 호환성을 위한 필드
    password: str

    @property
    def effective_username(self) -> str:
        """실제 사용할 사용자명 (username 또는 email)"""
        return self.username or self.email or ""


class LoginResponse(BaseModel):
    """로그인 응답 모델"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest) -> LoginResponse:
    """
    간단한 하드코딩 로그인 (MVP)
    - 웹 어드민: admin/qwer1234
    - 앱: dev@example.com/qwer1234
    """
    # 사용자 인증
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

    # 토큰 생성
    access_token = create_simple_token(username)

    return LoginResponse(
        access_token=access_token,
        expires_in=86400,  # 24시간
        username=username,
    )


@router.post("/logout")
async def logout() -> Dict[str, str]:
    """
    사용자 로그아웃 - 간단한 성공 응답
    """
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
) -> Dict[str, Any]:
    """
    현재 사용자 정보 조회
    """
    return {
        "sub": claims.get("sub"),
        "username": claims.get("username"),
        "scope": claims.get("scope"),
    }
