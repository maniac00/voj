"""
VOJ Audiobooks API - 분석/통계 엔드포인트
기기 등록, heartbeat, 재생 세션 기록, 관리자 통계 조회
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.auth.simple import get_current_user_claims, require_admin_scope
from app.models.analytics_sql import DeviceInstallationSQL, PlaybackProgressSQL, PlaybackSessionSQL
from app.models.book_sql import BookSQL
from app.models.database import get_db
from app.models.user_sql import UserSQL

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response 모델 ──────────────────────────────


class DeviceRegisterRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(default="android", max_length=20)
    os_version: Optional[str] = Field(None, max_length=50)
    app_version: Optional[str] = Field(None, max_length=20)
    device_model: Optional[str] = Field(None, max_length=100)


class HeartbeatRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=255)
    app_version: Optional[str] = Field(None, max_length=20)


class PlaySessionRequest(BaseModel):
    device_id: Optional[str] = Field(None, max_length=255)
    book_id: str = Field(..., min_length=1)
    chapter_id: str = Field(..., min_length=1)
    started_at: str = Field(...)
    ended_at: Optional[str] = None
    duration_seconds: int = Field(default=0, ge=0)
    completed: bool = False


# ── 공개 엔드포인트 ──────────────────────────────────────


@router.post("/device-register", status_code=201)
async def register_device(
    payload: DeviceRegisterRequest,
    claims=Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """기기 등록 (최초 실행 시)"""
    user_id = _resolve_user_id(claims, db)

    existing = db.query(DeviceInstallationSQL).filter(
        DeviceInstallationSQL.device_id == payload.device_id
    ).first()

    if existing:
        existing.last_seen_at = func.now()
        existing.app_version = payload.app_version or existing.app_version
        existing.os_version = payload.os_version or existing.os_version
        existing.device_model = payload.device_model or existing.device_model
        if user_id:
            existing.user_id = user_id
        existing.is_active = True
        db.commit()
        return {"ok": True, "status": "updated"}

    device = DeviceInstallationSQL(
        device_id=payload.device_id,
        user_id=user_id,
        platform=payload.platform,
        os_version=payload.os_version,
        app_version=payload.app_version,
        device_model=payload.device_model,
    )
    db.add(device)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"ok": True, "status": "created"}


@router.post("/heartbeat")
async def heartbeat(
    payload: HeartbeatRequest,
    claims=Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """활성 상태 업데이트 (앱 실행마다)"""
    device = db.query(DeviceInstallationSQL).filter(
        DeviceInstallationSQL.device_id == payload.device_id
    ).first()

    if device:
        device.last_seen_at = func.now()
        if payload.app_version:
            device.app_version = payload.app_version
        device.is_active = True
        user_id = _resolve_user_id(claims, db)
        if user_id:
            device.user_id = user_id
        db.commit()

    return {"ok": True}


@router.post("/play-session")
async def record_play_session(
    payload: PlaySessionRequest,
    claims=Depends(get_current_user_claims),
    db: Session = Depends(get_db),
):
    """재생 세션 기록"""
    user_id = _resolve_user_id(claims, db)
    if not user_id:
        raise HTTPException(status_code=401, detail="User not found")

    started_at = _parse_datetime(payload.started_at)
    ended_at = _parse_datetime(payload.ended_at) if payload.ended_at else None

    session = PlaybackSessionSQL(
        user_id=user_id,
        device_id=payload.device_id,
        book_id=payload.book_id,
        chapter_id=payload.chapter_id,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=payload.duration_seconds,
        completed=payload.completed,
    )
    db.add(session)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"ok": True, "session_id": session.id}


# ── 관리자 전용 엔드포인트 ────────────────────────────────


@router.get("/admin/overview")
async def admin_overview(
    claims=Depends(require_admin_scope()),
    db: Session = Depends(get_db),
):
    """대시보드 통계 개요"""
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # 설치 현황
    total_installations = db.query(func.count(DeviceInstallationSQL.id)).scalar() or 0
    active_devices = db.query(func.count(DeviceInstallationSQL.id)).filter(
        DeviceInstallationSQL.is_active == True  # noqa: E712
    ).scalar() or 0

    # 활성 사용자
    daily_active = db.query(func.count(func.distinct(PlaybackSessionSQL.user_id))).filter(
        PlaybackSessionSQL.started_at >= day_ago
    ).scalar() or 0
    weekly_active = db.query(func.count(func.distinct(PlaybackSessionSQL.user_id))).filter(
        PlaybackSessionSQL.started_at >= week_ago
    ).scalar() or 0
    monthly_active = db.query(func.count(func.distinct(PlaybackSessionSQL.user_id))).filter(
        PlaybackSessionSQL.started_at >= month_ago
    ).scalar() or 0

    # 재생 통계
    total_play_seconds = db.query(func.coalesce(func.sum(PlaybackSessionSQL.duration_seconds), 0)).scalar() or 0
    total_sessions = db.query(func.count(PlaybackSessionSQL.id)).scalar() or 0
    avg_session_seconds = (total_play_seconds // total_sessions) if total_sessions > 0 else 0
    completed_sessions = db.query(func.count(PlaybackSessionSQL.id)).filter(
        PlaybackSessionSQL.completed == True  # noqa: E712
    ).scalar() or 0

    # 최근 7일 일별 활성 사용자 (차트용)
    daily_stats = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = db.query(func.count(func.distinct(PlaybackSessionSQL.user_id))).filter(
            and_(
                PlaybackSessionSQL.started_at >= day_start,
                PlaybackSessionSQL.started_at < day_end,
            )
        ).scalar() or 0
        daily_stats.append({
            "date": day_start.strftime("%m/%d"),
            "users": count,
        })

    # 인기 도서 Top 10
    popular_books_query = (
        db.query(
            PlaybackSessionSQL.book_id,
            func.sum(PlaybackSessionSQL.duration_seconds).label("total_seconds"),
            func.count(PlaybackSessionSQL.id).label("session_count"),
        )
        .group_by(PlaybackSessionSQL.book_id)
        .order_by(func.sum(PlaybackSessionSQL.duration_seconds).desc())
        .limit(10)
        .all()
    )
    popular_books = []
    for row in popular_books_query:
        book = db.query(BookSQL).filter(BookSQL.book_id == row.book_id).first()
        popular_books.append({
            "book_id": row.book_id,
            "title": book.title if book else row.book_id,
            "total_seconds": row.total_seconds or 0,
            "session_count": row.session_count or 0,
        })

    return {
        "installations": {
            "total": total_installations,
            "active": active_devices,
        },
        "active_users": {
            "daily": daily_active,
            "weekly": weekly_active,
            "monthly": monthly_active,
        },
        "playback": {
            "total_seconds": total_play_seconds,
            "total_sessions": total_sessions,
            "avg_session_seconds": avg_session_seconds,
            "completed_sessions": completed_sessions,
        },
        "daily_active_users": daily_stats,
        "popular_books": popular_books,
    }


@router.get("/admin/user-stats")
async def admin_user_stats(
    claims=Depends(require_admin_scope()),
    db: Session = Depends(get_db),
):
    """사용자별 통계"""
    users = db.query(UserSQL).all()

    result = []
    for user in users:
        total_seconds = db.query(
            func.coalesce(func.sum(PlaybackSessionSQL.duration_seconds), 0)
        ).filter(PlaybackSessionSQL.user_id == user.id).scalar() or 0

        session_count = db.query(func.count(PlaybackSessionSQL.id)).filter(
            PlaybackSessionSQL.user_id == user.id
        ).scalar() or 0

        last_session = db.query(PlaybackSessionSQL).filter(
            PlaybackSessionSQL.user_id == user.id
        ).order_by(PlaybackSessionSQL.started_at.desc()).first()

        completed_books = (
            db.query(func.count(func.distinct(PlaybackSessionSQL.book_id)))
            .filter(
                and_(
                    PlaybackSessionSQL.user_id == user.id,
                    PlaybackSessionSQL.completed == True,  # noqa: E712
                )
            )
            .scalar() or 0
        )

        device = db.query(DeviceInstallationSQL).filter(
            DeviceInstallationSQL.user_id == user.id
        ).first()

        result.append({
            "user_id": user.id,
            "display_name": user.display_name or user.email,
            "email": user.email,
            "status": user.status.value if hasattr(user.status, "value") else str(user.status),
            "total_play_seconds": total_seconds,
            "session_count": session_count,
            "last_activity": last_session.started_at.isoformat() if last_session else None,
            "completed_books": completed_books,
            "device_model": device.device_model if device else None,
            "app_version": device.app_version if device else None,
        })

    result.sort(key=lambda x: x["total_play_seconds"], reverse=True)
    return {"users": result}


# ── 헬퍼 ────────────────────────────────────────────────


def _resolve_user_id(claims: dict, db: Session) -> Optional[int]:
    """claims에서 DB user.id를 찾는다."""
    # 1. Firebase JWT 경로: _verify_firebase_jwt가 user_id를 이미 넣어줌
    user_id = claims.get("user_id")
    if user_id is not None:
        return int(user_id)

    # 2. Firebase UID 기반 (직접 uid가 있는 경우)
    firebase_uid = claims.get("uid") or ""
    if firebase_uid:
        user = db.query(UserSQL).filter(UserSQL.firebase_uid == str(firebase_uid)).first()
        if user:
            return user.id

    # 3. email 기반 fallback (HMAC 관리자 토큰 등)
    email = claims.get("email") or ""
    if email and "@" in email:
        user = db.query(UserSQL).filter(UserSQL.email == email).first()
        if user:
            return user.id

    return None


def _parse_datetime(value: str) -> datetime:
    """ISO 8601 문자열을 datetime으로 파싱"""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)
