"""DPDP: date of birth, guardian consent, terms acceptance

Revision ID: e1f4a5b6c7d8
Revises: d9e3f4a5b6c7
"""
from alembic import op
import sqlalchemy as sa

revision = 'e1f4a5b6c7d8'
down_revision = 'd9e3f4a5b6c7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as b:
        b.add_column(sa.Column('date_of_birth', sa.Date(), nullable=True))
        b.add_column(sa.Column('guardian_email', sa.String(120), nullable=True))
        b.add_column(sa.Column('consent_status', sa.String(20), nullable=False, server_default='granted'))
        b.add_column(sa.Column('consent_at', sa.DateTime(), nullable=True))
        b.add_column(sa.Column('terms_accepted_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as b:
        for c in ('terms_accepted_at', 'consent_at', 'consent_status', 'guardian_email', 'date_of_birth'):
            b.drop_column(c)
