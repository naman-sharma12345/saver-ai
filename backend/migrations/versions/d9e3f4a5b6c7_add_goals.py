"""Add savings goals

Revision ID: d9e3f4a5b6c7
Revises: c8d2e3f4a5b6
"""
from alembic import op
import sqlalchemy as sa

revision = 'd9e3f4a5b6c7'
down_revision = 'c8d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'goals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('name', sa.String(80), nullable=False),
        sa.Column('target_amount', sa.Float(), nullable=False),
        sa.Column('saved_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_goals_user_id', 'goals', ['user_id'])


def downgrade():
    op.drop_index('ix_goals_user_id', table_name='goals')
    op.drop_table('goals')
