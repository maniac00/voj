"""Default is_copyrighted to true and backfill existing books

Revision ID: 008_copyright_default_true
Revises: 007_add_copyright_flags
Create Date: 2026-07-11
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_copyright_default_true"
down_revision: Union[str, None] = "007_add_copyright_flags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 기존 모든 책을 저작권 보호 콘텐츠로 표시
    op.execute(sa.text("UPDATE books SET is_copyrighted = TRUE"))

    # 신규 책의 DB 기본값도 true로 변경 (batch mode: SQLite 호환)
    with op.batch_alter_table("books") as batch_op:
        batch_op.alter_column(
            "is_copyrighted",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=sa.true(),
        )


def downgrade() -> None:
    with op.batch_alter_table("books") as batch_op:
        batch_op.alter_column(
            "is_copyrighted",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=sa.false(),
        )
