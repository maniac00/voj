"""
Telegram Bot Webhook 엔드포인트
사용자 승인/거부 콜백을 처리하며, 2단계 확인(실수 방지)을 지원한다.

콜백 데이터 형식: "{action}:{user_id}"
- approve:{id}         → 1차 승인 버튼 클릭 → 확인 요청
- reject:{id}          → 1차 거부 버튼 클릭 → 확인 요청
- confirm_approve:{id} → 2차 확인 → 실제 승인 처리
- confirm_reject:{id}  → 2차 확인 → 실제 거부 처리
- cancel:{id}          → 취소 → 원래 버튼으로 복원
"""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core import telegram as tg
from app.core.config import settings
from app.models.database import SessionLocal
from app.services.user_service import UserService

logger = logging.getLogger(__name__)

router = APIRouter()


def _verify_webhook_secret(secret_token: Optional[str]) -> None:
    """Telegram이 설정한 secret_token과 일치하는지 검증한다."""
    expected = settings.TELEGRAM_WEBHOOK_SECRET
    if expected and secret_token != expected:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(None),
) -> Dict[str, str]:
    _verify_webhook_secret(x_telegram_bot_api_secret_token)

    body: Dict[str, Any] = await request.json()
    callback_query = body.get("callback_query")
    if not callback_query:
        return {"ok": "true"}

    cb_id: str = callback_query["id"]
    data: str = callback_query.get("data", "")
    message: Dict[str, Any] = callback_query.get("message", {})
    chat_id: str = str(message.get("chat", {}).get("id", ""))
    message_id: int = message.get("message_id", 0)

    if not data or not chat_id or not message_id:
        return {"ok": "true"}

    # "action:user_id" 파싱
    parts = data.split(":", 1)
    if len(parts) != 2:
        return {"ok": "true"}

    action, user_id_str = parts[0], parts[1]
    try:
        user_id = int(user_id_str)
    except ValueError:
        return {"ok": "true"}

    db = SessionLocal()
    try:
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            tg.answer_callback_query(cb_id, "❌ 사용자를 찾을 수 없습니다.")
            return {"ok": "true"}

        email = user.email
        display_name = user.display_name or ""
        current_status = user.status.value

        if action in ("approve", "reject"):
            # 1차 클릭: 이미 처리됐으면 안내 후 종료
            if current_status != "pending":
                tg.answer_callback_query(
                    cb_id, f"이미 처리된 사용자입니다. (현재: {current_status})"
                )
                return {"ok": "true"}

            # 확인 메시지로 교체
            action_label = "승인" if action == "approve" else "거부"
            name_part = f"\n이름: {display_name}" if display_name else ""
            tg.edit_message(
                chat_id,
                message_id,
                (
                    f"⚠️ <b>정말 {action_label}하시겠습니까?</b>\n\n"
                    f"이메일: {email}{name_part}"
                ),
                tg.make_confirm_keyboard(action, user_id),
            )
            tg.answer_callback_query(cb_id)

        elif action == "confirm_approve":
            # 2차 확인: 실제 승인
            if current_status != "pending":
                tg.answer_callback_query(
                    cb_id, f"이미 처리된 사용자입니다. (현재: {current_status})"
                )
                return {"ok": "true"}

            UserService.update_user_status(db, user_id, "approved")
            name_part = f"\n이름: {display_name}" if display_name else ""
            tg.edit_message(
                chat_id,
                message_id,
                f"✅ <b>승인 완료</b>\n\n이메일: {email}{name_part}",
            )
            tg.answer_callback_query(cb_id, "✅ 승인했습니다.")
            logger.info("Telegram으로 사용자 승인: user_id=%d, email=%s", user_id, email)

        elif action == "confirm_reject":
            # 2차 확인: 실제 거부 (suspended 처리)
            if current_status != "pending":
                tg.answer_callback_query(
                    cb_id, f"이미 처리된 사용자입니다. (현재: {current_status})"
                )
                return {"ok": "true"}

            UserService.update_user_status(db, user_id, "suspended")
            name_part = f"\n이름: {display_name}" if display_name else ""
            tg.edit_message(
                chat_id,
                message_id,
                f"❌ <b>거부 완료</b>\n\n이메일: {email}{name_part}",
            )
            tg.answer_callback_query(cb_id, "❌ 거부했습니다.")
            logger.info("Telegram으로 사용자 거부: user_id=%d, email=%s", user_id, email)

        elif action == "cancel":
            # 취소: 원래 승인/거부 버튼으로 복원
            name_part = f"\n이름: {display_name}" if display_name else ""
            tg.edit_message(
                chat_id,
                message_id,
                (
                    f"🔔 <b>신규 사용자 가입 요청</b>\n\n"
                    f"ID: {user_id}\n"
                    f"이메일: {email}{name_part}\n\n"
                    f"승인 또는 거부를 선택해주세요."
                ),
                tg.make_user_keyboard(user_id),
            )
            tg.answer_callback_query(cb_id, "취소했습니다.")

    finally:
        db.close()

    return {"ok": "true"}
