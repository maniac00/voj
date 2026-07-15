"""
Telegram Bot 알림 유틸리티
신규 사용자 승인 요청을 관리자에게 전송하고 인라인 버튼으로 승인/거부를 처리한다.
"""
import json
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org"


def _url(method: str) -> str:
    return f"{_TELEGRAM_API}/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"


def make_user_keyboard(user_id: int) -> Dict[str, Any]:
    """신규 사용자 알림용 인라인 키보드 (승인 / 거부 버튼)"""
    return {
        "inline_keyboard": [
            [
                {"text": "✅ 승인", "callback_data": f"approve:{user_id}"},
                {"text": "❌ 거부", "callback_data": f"reject:{user_id}"},
            ]
        ]
    }


def make_confirm_keyboard(action: str, user_id: int) -> Dict[str, Any]:
    """2차 확인용 인라인 키보드 (확인 / 취소 버튼)"""
    return {
        "inline_keyboard": [
            [
                {"text": "✓ 확인", "callback_data": f"confirm_{action}:{user_id}"},
                {"text": "✗ 취소", "callback_data": f"cancel:{user_id}"},
            ]
        ]
    }


def send_new_user_notification(
    user_id: int,
    email: str,
    display_name: Optional[str] = None,
) -> None:
    """신규 사용자 가입 알림을 관리자 전원에게 전송한다. (가입은 자동 승인됨)"""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.telegram_admin_chat_ids:
        logger.debug("Telegram 설정이 없어 알림을 전송하지 않습니다.")
        return

    name_part = f"\n이름: {display_name}" if display_name else ""
    text = (
        f"🔔 <b>신규 사용자 가입</b>\n\n"
        f"ID: {user_id}\n"
        f"이메일: {email}"
        f"{name_part}\n\n"
        f"자동 승인되었습니다. 저작권 콘텐츠 접근은 관리자 대시보드에서 부여할 수 있습니다."
    )

    for chat_id in settings.telegram_admin_chat_ids:
        _send_message(chat_id, text)


def _send_message(
    chat_id: str,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
) -> None:
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup is not None:
        payload["reply_markup"] = json.dumps(reply_markup)

    try:
        resp = httpx.post(_url("sendMessage"), json=payload, timeout=10.0)
        resp.raise_for_status()
    except Exception as e:
        logger.error("Telegram 메시지 전송 실패 (chat_id=%s): %s", chat_id, e)


def edit_message(
    chat_id: str,
    message_id: int,
    text: str,
    reply_markup: Optional[Dict[str, Any]] = None,
) -> None:
    """기존 메시지 내용과 버튼을 수정한다. reply_markup=None이면 버튼을 제거한다."""
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(reply_markup) if reply_markup is not None else "",
    }

    try:
        resp = httpx.post(_url("editMessageText"), json=payload, timeout=10.0)
        resp.raise_for_status()
    except Exception as e:
        logger.error("Telegram 메시지 수정 실패: %s", e)


def answer_callback_query(callback_query_id: str, text: str = "") -> None:
    """버튼 클릭 후 로딩 스피너를 해제한다."""
    try:
        httpx.post(
            _url("answerCallbackQuery"),
            json={"callback_query_id": callback_query_id, "text": text},
            timeout=10.0,
        )
    except Exception as e:
        logger.error("Telegram callback 응답 실패: %s", e)
