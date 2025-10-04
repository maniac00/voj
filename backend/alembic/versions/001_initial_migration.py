"""Initial migration - Create books and audio_chapters tables

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Books 테이블 생성
    op.create_table(
        'books',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('book_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('author', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('genre', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('isbn', sa.String(length=20), nullable=True),
        sa.Column('publisher', sa.String(length=100), nullable=True),
        sa.Column('published_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'PROCESSING', 'PUBLISHED', 'ERROR', name='bookstatus'), nullable=True),
        sa.Column('total_chapters', sa.Integer(), nullable=True),
        sa.Column('total_duration', sa.Integer(), nullable=True),
        sa.Column('cover_image_url', sa.Text(), nullable=True),
        sa.Column('cover_image_key', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_books_book_id'), 'books', ['book_id'], unique=True)
    op.create_index(op.f('ix_books_genre'), 'books', ['genre'], unique=False)
    op.create_index(op.f('ix_books_id'), 'books', ['id'], unique=False)
    op.create_index(op.f('ix_books_status'), 'books', ['status'], unique=False)
    op.create_index(op.f('ix_books_title'), 'books', ['title'], unique=False)
    op.create_index(op.f('ix_books_user_id'), 'books', ['user_id'], unique=False)

    # Audio Chapters 테이블 생성
    op.create_table(
        'audio_chapters',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('book_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('chapter_id', sa.String(length=255), nullable=False),
        sa.Column('chapter_number', sa.Integer(), nullable=False),
        sa.Column('chapter_title', sa.String(length=200), nullable=True),
        sa.Column('audio_key', sa.String(length=500), nullable=False),
        sa.Column('audio_url', sa.Text(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('content_type', sa.String(length=50), nullable=True),
        sa.Column('bitrate', sa.Integer(), nullable=True),
        sa.Column('sample_rate', sa.Integer(), nullable=True),
        sa.Column('channels', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audio_chapters_book_id'), 'audio_chapters', ['book_id'], unique=False)
    op.create_index(op.f('ix_audio_chapters_chapter_id'), 'audio_chapters', ['chapter_id'], unique=True)
    op.create_index(op.f('ix_audio_chapters_id'), 'audio_chapters', ['id'], unique=False)
    op.create_index(op.f('ix_audio_chapters_user_id'), 'audio_chapters', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audio_chapters_user_id'), table_name='audio_chapters')
    op.drop_index(op.f('ix_audio_chapters_id'), table_name='audio_chapters')
    op.drop_index(op.f('ix_audio_chapters_chapter_id'), table_name='audio_chapters')
    op.drop_index(op.f('ix_audio_chapters_book_id'), table_name='audio_chapters')
    op.drop_table('audio_chapters')

    op.drop_index(op.f('ix_books_user_id'), table_name='books')
    op.drop_index(op.f('ix_books_title'), table_name='books')
    op.drop_index(op.f('ix_books_status'), table_name='books')
    op.drop_index(op.f('ix_books_id'), table_name='books')
    op.drop_index(op.f('ix_books_genre'), table_name='books')
    op.drop_index(op.f('ix_books_book_id'), table_name='books')
    op.drop_table('books')
