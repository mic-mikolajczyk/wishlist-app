"""stub restore is_active revision (already applied in DB)

Revision ID: c1e2f3a4b5c6
Revises: b4c7d2e9d111
Create Date: 2025-11-05 01:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'c1e2f3a4b5c6'
down_revision = 'b4c7d2e9d111'
branch_labels = None
depends_on = None


def upgrade():
    # Column likely already exists; ensure idempotency.
    conn = op.get_bind()
    existing = [c['name'] for c in conn.execute(sa.text('PRAGMA table_info(event)')).fetchall()]
    if 'is_active' not in existing:
        op.add_column('event', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
        with op.batch_alter_table('event') as batch_op:
            batch_op.alter_column('is_active', server_default=None)


def downgrade():
    conn = op.get_bind()
    existing = [c['name'] for c in conn.execute(sa.text('PRAGMA table_info(event)')).fetchall()]
    if 'is_active' in existing:
        op.drop_column('event', 'is_active')
