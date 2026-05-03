"""Add copyright access flags to books and users

Revision ID: 007_add_copyright_flags
Revises: 006_add_book_narrator
Create Date: 2026-05-03
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_add_copyright_flags"
down_revision: Union[str, None] = "006_add_book_narrator"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "books",
        sa.Column(
            "is_copyrighted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "can_access_copyrighted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "can_access_copyrighted")
    op.drop_column("books", "is_copyrighted")
