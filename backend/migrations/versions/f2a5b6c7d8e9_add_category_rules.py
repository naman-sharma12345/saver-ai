"""Add per-user category rules

Revision ID: f2a5b6c7d8e9
Revises: e1f4a5b6c7d8
"""
from alembic import op
import sqlalchemy as sa

revision = 'f2a5b6c7d8e9'
down_revision = 'e1f4a5b6c7d8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'category_rules',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('merchant_key', sa.String(120), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', 'merchant_key', name='uq_rule_user_merchant'),
    )
    op.create_index('ix_category_rules_user_id', 'category_rules', ['user_id'])


def downgrade():
    op.drop_index('ix_category_rules_user_id', table_name='category_rules')
    op.drop_table('category_rules')
