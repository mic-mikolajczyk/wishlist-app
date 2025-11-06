"""add archived flag to event

Revision ID: e5f7a9c0d1e2
revises: d4e5f6a7b8c9
Create Date: 2025-11-06 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e5f7a9c0d1e2'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'event',
        sa.Column(
            'archived',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )
    with op.batch_alter_table('event') as batch_op:
        batch_op.alter_column('archived', server_default=None)


def downgrade():
    op.drop_column('event', 'archived')
