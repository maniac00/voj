"""
VOJ Audiobooks API - 간단한 인증 엔드포인트
하드코딩된 admin/admin123 계정 인증
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict

from app.core.config import settings
from app.core.auth.simple import (
    get_current_user_claims,
    authenticate_user,
    create_simple_token
)

router = APIRouter()


class LoginRequest(BaseModel):
    """로그인 요청 모델"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """로그인 응답 모델"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str




@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """
    간단한 하드코딩 로그인 - admin/admin123
    """
    # 사용자 인증
    if not authenticate_user(login_data.username, login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # 토큰 생성
    access_token = create_simple_token(login_data.username)
    
    return LoginResponse(
        access_token=access_token,
        expires_in=86400,  # 24시간
        username=login_data.username,
    )


@router.post("/logout")
async def logout():
    """
    사용자 로그아웃 - 간단한 성공 응답
    """
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(claims = Depends(get_current_user_claims)):
    """
    현재 사용자 정보 조회
    """
    return {
        "sub": claims.get("sub"),
        "username": claims.get("username"),
        "scope": claims.get("scope"),
    }

