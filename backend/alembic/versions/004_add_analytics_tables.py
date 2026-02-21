"""Add analytics tables for device installations, playback progress, and sessions

Revision ID: 004_analytics
Revises: 003_add_users
Create Date: 2026-02-15
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_analytics"
down_revision: Union[str, None] = "003_add_users"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 기기 설치 기록
    op.create_table(
        "device_installations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("device_id", sa.String(255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("platform", sa.String(20), nullable=False, server_default="android"),
        sa.Column("os_version", sa.String(50), nullable=True),
        sa.Column("app_version", sa.String(20), nullable=True),
        sa.Column("device_model", sa.String(100), nullable=True),
        sa.Column("first_installed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_device_installations_device_id", "device_installations", ["device_id"], unique=True)
    op.create_index("ix_device_installations_user_id", "device_installations", ["user_id"])

    # 재생 진행률
    op.create_table(
        "playback_progress",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.String(255), nullable=False),
        sa.Column("chapter_id", sa.String(255), nullable=False),
        sa.Column("position_seconds", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_played_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "book_id", "chapter_id", name="uq_playback_progress_user_book_chapter"),
    )
    op.create_index("ix_playback_progress_user_id", "playback_progress", ["user_id"])
    op.create_index("ix_playback_progress_book_id", "playback_progress", ["book_id"])

    # 재생 세션
    op.create_table(
        "playback_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.String(255), nullable=True),
        sa.Column("book_id", sa.String(255), nullable=False),
        sa.Column("chapter_id", sa.String(255), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("completed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_playback_sessions_user_id", "playback_sessions", ["user_id"])
    op.create_index("ix_playback_sessions_book_id", "playback_sessions", ["book_id"])
    op.create_index("ix_playback_sessions_started_at", "playback_sessions", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_playback_sessions_started_at", table_name="playback_sessions")
    op.drop_index("ix_playback_sessions_book_id", table_name="playback_sessions")
    op.drop_index("ix_playback_sessions_user_id", table_name="playback_sessions")
    op.drop_table("playback_sessions")

    op.drop_index("ix_playback_progress_book_id", table_name="playback_progress")
    op.drop_index("ix_playback_progress_user_id", table_name="playback_progress")
    op.drop_table("playback_progress")

    op.drop_index("ix_device_installations_user_id", table_name="device_installations")
    op.drop_index("ix_device_installations_device_id", table_name="device_installations")
    op.drop_table("device_installations")
