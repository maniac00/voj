"""
VOJ Audiobooks API - 사용자 관리 엔드포인트
관리자용 사용자 목록/상태 관리 + 현재 사용자 정보
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.audit import log_user_delete, log_user_status_change
from app.core.auth.simple import get_current_user_claims, require_admin_scope
from app.models.database import get_db
from app.services.user_service import UserService

router = APIRouter()


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    status: str
    role: str
    can_access_copyrighted: bool = False
    created_at: str
    updated_at: str


class UserStatusUpdate(BaseModel):
    status: str  # "approved" | "suspended" | "pending"


class UserCopyrightAccessUpdate(BaseModel):
    can_access_copyrighted: bool


@router.get("", response_model=List[UserResponse])
@router.get("/", response_model=List[UserResponse])
async def list_users(
    status_filter: Optional[str] = Query(None, alias="status"),
    claims: Dict[str, Any] = Depends(require_admin_scope()),
    db: Session = Depends(get_db),
) -> List[UserResponse]:
    """사용자 목록 조회 (관리자 전용)"""
    users = UserService.list_users(db, status_filter=status_filter)
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            display_name=u.display_name,
            photo_url=u.photo_url,
            status=u.status.value,
            role=u.role.value,
            can_access_copyrighted=bool(u.can_access_copyrighted),
            created_at=u.created_at.isoformat() if u.created_at else "",
            updated_at=u.updated_at.isoformat() if u.updated_at else "",
        )
        for u in users
    ]


@router.patch("/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    body: UserStatusUpdate,
    user_id: int = Path(..., description="사용자 ID"),
    claims: Dict[str, Any] = Depends(require_admin_scope()),
    db: Session = Depends(get_db),
) -> UserResponse:
    """사용자 상태 변경 (관리자 전용)"""
    if body.status not in ("pending", "approved", "suspended"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Must be: pending, approved, suspended",
        )

    old_user = UserService.get_user_by_id(db, user_id)
    if not old_user:
        raise HTTPException(status_code=404, detail="User not found")

    old_status = old_user.status.value
    user = UserService.update_user_status(db, user_id, body.status)

    admin_name = claims.get("username", claims.get("email", "unknown"))
    log_user_status_change(admin_name, user_id, old_status, body.status)

    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        photo_url=user.photo_url,
        status=user.status.value,
        role=user.role.value,
        can_access_copyrighted=bool(user.can_access_copyrighted),
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
    )


@router.patch("/{user_id}/copyright-access", response_model=UserResponse)
async def update_user_copyright_access(
    body: UserCopyrightAccessUpdate,
    user_id: int = Path(..., description="사용자 ID"),
    claims: Dict[str, Any] = Depends(require_admin_scope()),
    db: Session = Depends(get_db),
) -> UserResponse:
    """저작권 보호 콘텐츠 접근 권한 토글 (관리자 전용)"""
    user = UserService.update_user_copyright_access(
        db, user_id, body.can_access_copyrighted
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        photo_url=user.photo_url,
        status=user.status.value,
        role=user.role.value,
        can_access_copyrighted=bool(user.can_access_copyrighted),
        created_at=user.created_at.isoformat() if user.created_at else "",
        updated_at=user.updated_at.isoformat() if user.updated_at else "",
    )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Session = Depends(get_db),
) -> None:
    """본인 계정 삭제 (모바일 사용자용) — App Store 가이드라인 5.1.1(v)

    계정과 연관 데이터(리프레시 토큰, 세션 기록)를 삭제하고
    Firebase Auth 계정도 함께 제거한다.
    """
    user_id = claims.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인 계정 인증 정보가 없습니다.",
        )

    user = UserService.get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role.value == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="관리자 계정은 삭제할 수 없습니다.",
        )

    email = user.email
    firebase_uid = user.firebase_uid
    UserService.delete_user(db, user.id)

    from app.core.auth.firebase import delete_firebase_user

    delete_firebase_user(firebase_uid)

    log_user_delete(email, int(user_id), email)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int = Path(..., description="사용자 ID"),
    claims: Dict[str, Any] = Depends(require_admin_scope()),
    db: Session = Depends(get_db),
) -> None:
    """사용자 삭제 (관리자 전용) — 관리자 계정은 삭제 불가"""
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.role.value == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="관리자 계정은 삭제할 수 없습니다.",
        )

    email = user.email
    UserService.delete_user(db, user_id)

    admin_name = claims.get("username", claims.get("email", "unknown"))
    log_user_delete(admin_name, user_id, email)


@router.get("/me")
async def get_my_profile(
    claims: Dict[str, Any] = Depends(get_current_user_claims),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """현재 사용자 프로필 (Firebase 사용자용)"""
    auth_type = claims.get("auth_type", "hmac")

    if auth_type == "firebase":
        user_id = claims.get("user_id")
        if user_id:
            user = UserService.get_user_by_id(db, user_id)
            if user:
                return user.to_dict()

    return {
        "email": claims.get("email"),
        "username": claims.get("username"),
        "scope": claims.get("scope"),
        "auth_type": auth_type,
    }
