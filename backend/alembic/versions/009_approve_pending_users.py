"""Approve all pending users (signup no longer requires admin approval)

Revision ID: 009_approve_pending_users
Revises: 008_copyright_default_true
Create Date: 2026-07-15
"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "009_approve_pending_users"
down_revision: Union[str, None] = "008_copyright_default_true"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 가입 승인 절차 폐지 — 기존 pending 사용자를 모두 승인 처리
    # (저작권 보호 콘텐츠는 can_access_copyrighted 화이트리스트로 별도 통제)
    op.execute(sa.text("UPDATE users SET status = 'approved' WHERE status = 'pending'"))


def downgrade() -> None:
    # 승인된 사용자 중 누가 pending이었는지 복원 불가 — no-op
    pass
