"""
사용자 관리 서비스
Firebase 인증 사용자의 생성, 조회, 상태 관리
"""
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user_sql import UserRole, UserSQL, UserStatus

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def get_or_create_user(
        db: Session,
        *,
        firebase_uid: str,
        email: str,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
    ) -> UserSQL:
        """Firebase UID로 사용자를 조회하거나, 없으면 새로 생성한다."""
        user = db.query(UserSQL).filter(UserSQL.firebase_uid == firebase_uid).first()
        if user:
            # 프로필 정보 갱신
            changed = False
            if display_name and user.display_name != display_name:
                user.display_name = display_name
                changed = True
            if photo_url and user.photo_url != photo_url:
                user.photo_url = photo_url
                changed = True
            if changed:
                db.commit()
                db.refresh(user)
            return user

        # 신규 사용자 생성
        admin_emails = settings.admin_emails_list
        is_admin = email.lower() in [e.lower() for e in admin_emails]

        user = UserSQL(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            photo_url=photo_url,
            status=UserStatus.APPROVED if is_admin else UserStatus.PENDING,
            role=UserRole.ADMIN if is_admin else UserRole.USER,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(
            "New user created: email=%s, status=%s, role=%s",
            email,
            user.status.value,
            user.role.value,
        )
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[UserSQL]:
        return db.query(UserSQL).filter(UserSQL.id == user_id).first()

    @staticmethod
    def get_user_by_firebase_uid(db: Session, firebase_uid: str) -> Optional[UserSQL]:
        return db.query(UserSQL).filter(UserSQL.firebase_uid == firebase_uid).first()

    @staticmethod
    def list_users(
        db: Session,
        *,
        status_filter: Optional[str] = None,
    ) -> List[UserSQL]:
        query = db.query(UserSQL).order_by(UserSQL.created_at.desc())
        if status_filter:
            query = query.filter(UserSQL.status == status_filter)
        return query.all()

    @staticmethod
    def delete_user(db: Session, user_id: int) -> Optional[UserSQL]:
        """사용자를 삭제한다. suspended 상태인 경우에만 허용."""
        user = db.query(UserSQL).filter(UserSQL.id == user_id).first()
        if not user:
            return None
        db.delete(user)
        db.commit()
        return user

    @staticmethod
    def update_user_status(
        db: Session,
        user_id: int,
        new_status: str,
    ) -> Optional[UserSQL]:
        user = db.query(UserSQL).filter(UserSQL.id == user_id).first()
        if not user:
            return None
        user.status = UserStatus(new_status)
        db.commit()
        db.refresh(user)
        return user
