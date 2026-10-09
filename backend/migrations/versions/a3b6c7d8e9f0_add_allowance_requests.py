"""Add allowance requests (student asks parent for extra money)

Revision ID: a3b6c7d8e9f0
Revises: f2a5b6c7d8e9
"""
from alembic import op
import sqlalchemy as sa

revision = 'a3b6c7d8e9f0'
down_revision = 'f2a5b6c7d8e9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'allowance_requests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('reason', sa.String(140), nullable=False),
        sa.Column('status', sa.String(10), nullable=False),
        sa.Column('parent_note', sa.String(140), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('decided_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_allowance_requests_student_id', 'allowance_requests', ['student_id'])
    op.create_index('ix_allowance_requests_parent_id', 'allowance_requests', ['parent_id'])


def downgrade():
    op.drop_index('ix_allowance_requests_parent_id', table_name='allowance_requests')
    op.drop_index('ix_allowance_requests_student_id', table_name='allowance_requests')
    op.drop_table('allowance_requests')
