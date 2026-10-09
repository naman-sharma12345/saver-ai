"""Add weekly_email opt-in to users

Revision ID: c5d8e9f0a1b2
Revises: b4c7d8e9f0a1
"""
from alembic import op
import sqlalchemy as sa

revision = 'c5d8e9f0a1b2'
down_revision = 'b4c7d8e9f0a1'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users') as b:
        b.add_column(sa.Column('weekly_email', sa.Boolean(), nullable=False, server_default='0'))


def downgrade():
    with op.batch_alter_table('users') as b:
        b.drop_column('weekly_email')
