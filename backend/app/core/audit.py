"""
감사(Audit) 로깅 유틸리티.
보안 관련 이벤트(로그인, 데이터 변경 등)를 구조화된 JSON으로 기록한다.
"""
import json
import logging
from typing import Any, Dict, Optional

audit_logger = logging.getLogger("audit")


def _log(
    action: str,
    *,
    user: Optional[str] = None,
    detail: Optional[Dict[str, Any]] = None,
    success: bool = True,
) -> None:
    entry: Dict[str, Any] = {
        "action": action,
        "user": user,
        "success": success,
    }
    if detail:
        entry["detail"] = detail
    audit_logger.info(json.dumps(entry, default=str))


def log_login_success(username: str) -> None:
    _log("auth.login", user=username, success=True)


def log_login_failure(username: str) -> None:
    _log("auth.login", user=username, success=False)


def log_book_created(user: str, book_id: str, title: str) -> None:
    _log("book.create", user=user, detail={"book_id": book_id, "title": title})


def log_book_deleted(user: str, book_id: str) -> None:
    _log("book.delete", user=user, detail={"book_id": book_id})


def log_audio_uploaded(user: str, book_id: str, chapter_id: str, filename: str) -> None:
    _log(
        "audio.upload",
        user=user,
        detail={"book_id": book_id, "chapter_id": chapter_id, "filename": filename},
    )


def log_audio_deleted(user: str, book_id: str, chapter_id: str) -> None:
    _log("audio.delete", user=user, detail={"book_id": book_id, "chapter_id": chapter_id})


def log_firebase_login(email: str, firebase_uid: str, is_new: bool) -> None:
    _log(
        "auth.firebase_login",
        user=email,
        detail={"firebase_uid": firebase_uid, "is_new_user": is_new},
    )


def log_user_delete(admin: str, target_user_id: int, email: str) -> None:
    _log(
        "user.delete",
        user=admin,
        detail={"target_user_id": target_user_id, "email": email},
    )


def log_user_status_change(
    admin: str, target_user_id: int, old_status: str, new_status: str
) -> None:
    _log(
        "user.status_change",
        user=admin,
        detail={
            "target_user_id": target_user_id,
            "old_status": old_status,
            "new_status": new_status,
        },
    )
