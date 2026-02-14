"""Add FK constraint on audio_chapters.book_id and unique constraint on (book_id, chapter_number)

Revision ID: 002_add_fk
Revises: 001_initial
Create Date: 2026-02-14
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002_add_fk"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # FK: audio_chapters.book_id -> books.book_id
    op.create_foreign_key(
        "fk_audio_chapters_book_id",
        "audio_chapters",
        "books",
        ["book_id"],
        ["book_id"],
        ondelete="CASCADE",
    )
    # Unique constraint: (book_id, chapter_number)
    op.create_unique_constraint(
        "uq_book_chapter_number",
        "audio_chapters",
        ["book_id", "chapter_number"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_book_chapter_number", "audio_chapters", type_="unique")
    op.drop_constraint("fk_audio_chapters_book_id", "audio_chapters", type_="foreignkey")
