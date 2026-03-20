"""update dedup unique constraint

Revision ID: 20260320_0002
Revises: 20260319_0001
Create Date: 2026-03-20 15:50:00
"""

from alembic import op


revision = '20260320_0002'
down_revision = '20260319_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table('articles') as batch_op:
        batch_op.drop_constraint('uq_category_dedup_key', type_='unique')
        batch_op.create_unique_constraint('uq_dedup_key', ['dedup_key'])


def downgrade() -> None:
    with op.batch_alter_table('articles') as batch_op:
        batch_op.drop_constraint('uq_dedup_key', type_='unique')
        batch_op.create_unique_constraint('uq_category_dedup_key', ['category_id', 'dedup_key'])
