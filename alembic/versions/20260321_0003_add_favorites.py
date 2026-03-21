"""add favorites table

Revision ID: 20260321_0003
Revises: 20260320_0002
Create Date: 2026-03-21 22:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = '20260321_0003'
down_revision = '20260320_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('articles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('article_id', name='uq_favorites_article_id'),
    )
    op.create_index('ix_favorites_article_id', 'favorites', ['article_id'])


def downgrade() -> None:
    op.drop_index('ix_favorites_article_id', table_name='favorites')
    op.drop_table('favorites')
