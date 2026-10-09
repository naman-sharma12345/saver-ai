"""Add parent match fields to goals

Revision ID: b4c7d8e9f0a1
Revises: a3b6c7d8e9f0
"""
from alembic import op
import sqlalchemy as sa

revision = 'b4c7d8e9f0a1'
down_revision = 'a3b6c7d8e9f0'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('goals') as b:
        b.add_column(sa.Column('match_percent', sa.Integer(), nullable=False, server_default='0'))
        b.add_column(sa.Column('match_cap', sa.Float(), nullable=True))
        b.add_column(sa.Column('matched_amount', sa.Float(), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('goals') as b:
        b.drop_column('matched_amount')
        b.drop_column('match_cap')
        b.drop_column('match_percent')
