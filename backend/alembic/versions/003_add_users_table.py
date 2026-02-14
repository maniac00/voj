"""Add users table for Firebase auth

Revision ID: 003_add_users
Revises: 002_add_fk
Create Date: 2026-02-14
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_add_users"
down_revision: Union[str, None] = "002_add_fk"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("firebase_uid", sa.String(128), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "suspended", name="userstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="userrole"),
            nullable=False,
            server_default="user",
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_status", "users", ["status"])


def downgrade() -> None:
    op.drop_index("ix_users_status", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_firebase_uid", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
    # Enum 타입 정리
    sa.Enum(name="userstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="userrole").drop(op.get_bind(), checkfirst=True)
