"""init tables

Revision ID: 20260319_0001
Revises: None
Create Date: 2026-03-19 10:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = '20260319_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'articles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('category_id', sa.String(length=100), nullable=False),
        sa.Column('source_name', sa.String(length=255), nullable=False),
        sa.Column('entry_id', sa.String(length=1000), nullable=False, server_default=''),
        sa.Column('dedup_key', sa.String(length=1000), nullable=False),
        sa.Column('title', sa.String(length=1000), nullable=False),
        sa.Column('link', sa.String(length=2000), nullable=False),
        sa.Column('summary_short', sa.String(length=200), nullable=False, server_default=''),
        sa.Column('summary_keypoints', sa.Text(), nullable=False, server_default=''),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('category_id', 'dedup_key', name='uq_category_dedup_key'),
    )
    op.create_index('ix_articles_category_id', 'articles', ['category_id'])


def downgrade() -> None:
    op.drop_index('ix_articles_category_id', table_name='articles')
    op.drop_table('articles')
