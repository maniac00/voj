"""
VOJ Audiobooks API - 인증 엔드포인트
AWS Cognito를 사용한 사용자 인증 관리
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
import boto3
import hmac
import hashlib
import base64

from app.core.config import settings
from app.core.auth.deps import get_current_user_claims, get_bearer_token
from app.core.auth.jwt import verify_cognito_jwt

router = APIRouter()


class LoginRequest(BaseModel):
    """로그인 요청 모델"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """로그인 응답 모델"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str


class RegisterRequest(BaseModel):
    """회원가입 요청 모델"""
    email: EmailStr
    password: str
    name: str


class RegisterResponse(BaseModel):
    """회원가입 응답 모델"""
    user_id: str
    email: str
    message: str


def _get_cognito_client():
    return boto3.client(
        "cognito-idp",
        region_name=settings.COGNITO_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def _calc_secret_hash(username: str, client_id: str, client_secret: Optional[str]) -> Optional[str]:
    if not client_secret:
        return None
    digest = hmac.new(
        client_secret.encode("utf-8"),
        (username + client_id).encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode()


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """
    사용자 로그인 - Cognito USER_PASSWORD_AUTH
    로컬 환경에서 Cognito 설정이 비어있으면 개발용 BYPASS 토큰 반환
    """
    # 로컬 개발 BYPASS (Cognito 값이 비어있는 경우)
    if settings.ENVIRONMENT == "local" and not settings.COGNITO_USER_POOL_ID:
        return LoginResponse(
            access_token="LOCAL_DEV_ACCESS_TOKEN",
            expires_in=3600,
            user_id=settings.LOCAL_BYPASS_SUB,
            email=login_data.email,
        )

    if not settings.COGNITO_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Cognito client configuration missing")

    client = _get_cognito_client()
    secret_hash = _calc_secret_hash(
        username=login_data.email,
        client_id=settings.COGNITO_CLIENT_ID,
        client_secret=settings.COGNITO_CLIENT_SECRET,
    )

    auth_parameters: Dict[str, str] = {
        "USERNAME": login_data.email,
        "PASSWORD": login_data.password,
    }
    if secret_hash:
        auth_parameters["SECRET_HASH"] = secret_hash

    try:
        resp = client.initiate_auth(
            ClientId=settings.COGNITO_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters=auth_parameters,
        )
        result = resp.get("AuthenticationResult") or {}
        access_token = result.get("AccessToken")
        id_token = result.get("IdToken")
        expires_in = result.get("ExpiresIn", 3600)

        if not access_token or not id_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        # ID 토큰 검증 후 사용자 정보 추출
        claims = await verify_cognito_jwt(id_token)
        user_id = claims.get("sub") or ""
        email = claims.get("email") or login_data.email

        return LoginResponse(
            access_token=access_token,
            expires_in=expires_in,
            user_id=user_id,
            email=email,
        )
    except client.exceptions.NotAuthorizedException as e:  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    except client.exceptions.UserNotConfirmedException as e:  # type: ignore[attr-defined]
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not confirmed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/register", response_model=RegisterResponse)
async def register(register_data: RegisterRequest):
    """
    사용자 회원가입 - (MVP 외, 차후 구현)
    """
    if settings.ENVIRONMENT == "local":
        return RegisterResponse(
            user_id="dummy_user_id",
            email=register_data.email,
            message="User registered successfully (local dev mode)",
        )
    raise HTTPException(status_code=501, detail="Registration not implemented yet")


@router.post("/logout")
async def logout(access_token: str = Depends(get_bearer_token)):
    """
    사용자 로그아웃 - GlobalSignOut(접근 토큰 무효화)
    로컬 환경에서는 성공 메시지 반환
    """
    if settings.ENVIRONMENT == "local" and settings.LOCAL_BYPASS_ENABLED:
        return {"message": "Logged out successfully (local dev mode)"}

    try:
        client = _get_cognito_client()
        client.global_sign_out(AccessToken=access_token)
        return {"message": "Logged out successfully"}
    except client.exceptions.NotAuthorizedException:  # type: ignore[attr-defined]
        # 이미 무효화된 토큰 등
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")


@router.get("/me")
async def get_current_user(claims = Depends(get_current_user_claims)):
    """
    현재 사용자 정보 조회
    JWT 토큰에서 사용자 정보 추출
    """
    return {
        "sub": claims.get("sub"),
        "email": claims.get("email"),
        "username": claims.get("cognito:username"),
        "token_use": claims.get("token_use"),
        "scope": claims.get("scope"),
    }

