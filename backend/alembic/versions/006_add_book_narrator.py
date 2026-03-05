"""Add narrator column to books

Revision ID: 006_add_book_narrator
Revises: 005_add_mobile_refresh
Create Date: 2026-03-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_add_book_narrator"
down_revision: Union[str, None] = "005_add_mobile_refresh"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("books", sa.Column("narrator", sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column("books", "narrator")
