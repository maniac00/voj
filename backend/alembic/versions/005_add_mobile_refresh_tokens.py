"""Add mobile refresh token table

Revision ID: 005_add_mobile_refresh
Revises: 004_analytics
Create Date: 2026-03-04
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_add_mobile_refresh"
down_revision: Union[str, None] = "004_analytics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mobile_refresh_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("replaced_by_token_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["replaced_by_token_id"],
            ["mobile_refresh_tokens.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mobile_refresh_tokens_id",
        "mobile_refresh_tokens",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_mobile_refresh_tokens_user_id",
        "mobile_refresh_tokens",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_mobile_refresh_tokens_device_id",
        "mobile_refresh_tokens",
        ["device_id"],
        unique=False,
    )
    op.create_index(
        "ix_mobile_refresh_tokens_token_hash",
        "mobile_refresh_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_mobile_refresh_tokens_expires_at",
        "mobile_refresh_tokens",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_mobile_refresh_tokens_revoked_at",
        "mobile_refresh_tokens",
        ["revoked_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_mobile_refresh_tokens_revoked_at",
        table_name="mobile_refresh_tokens",
    )
    op.drop_index(
        "ix_mobile_refresh_tokens_expires_at",
        table_name="mobile_refresh_tokens",
    )
    op.drop_index(
        "ix_mobile_refresh_tokens_token_hash",
        table_name="mobile_refresh_tokens",
    )
    op.drop_index(
        "ix_mobile_refresh_tokens_device_id",
        table_name="mobile_refresh_tokens",
    )
    op.drop_index(
        "ix_mobile_refresh_tokens_user_id",
        table_name="mobile_refresh_tokens",
    )
    op.drop_index("ix_mobile_refresh_tokens_id", table_name="mobile_refresh_tokens")
    op.drop_table("mobile_refresh_tokens")
