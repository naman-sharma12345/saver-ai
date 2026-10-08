"""Add plan, trial and billing fields to users

Revision ID: b7c1d2e3f4a5
Revises: a4d7cb520a2a
"""
from alembic import op
import sqlalchemy as sa

revision = 'b7c1d2e3f4a5'
down_revision = 'a4d7cb520a2a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('plan', sa.String(length=20), nullable=False, server_default='free'))
        batch_op.add_column(sa.Column('trial_ends_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('plan_expires_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('billing_ref', sa.String(length=100), nullable=True))
    # Existing users get a fresh trial starting now so nobody is locked out at launch.
    op.execute("UPDATE users SET trial_ends_at = datetime('now', '+7 days') WHERE trial_ends_at IS NULL"
               if op.get_bind().dialect.name == 'sqlite'
               else "UPDATE users SET trial_ends_at = now() + interval '7 days' WHERE trial_ends_at IS NULL")


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('billing_ref')
        batch_op.drop_column('plan_expires_at')
        batch_op.drop_column('trial_ends_at')
        batch_op.drop_column('plan')
