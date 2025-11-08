"""Add missing columns to event and event_participant

Revision ID: 9ab3e6d1f2c7
Revises: 67a5c1aa05f4_remove_picture_field_from_wishlistitem
Create Date: 2025-11-04
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9ab3e6d1f2c7'
down_revision = '67a5c1aa05f4'
branch_labels = None
depends_on = None


def upgrade():
    # Add created_at to event if not present
    with op.batch_alter_table('event') as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(), nullable=True))

    # Add new columns to event_participant
    with op.batch_alter_table('event_participant') as batch_op:
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('invited_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('accepted_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('event_participant') as batch_op:
        batch_op.drop_column('accepted_at')
        batch_op.drop_column('invited_at')
        batch_op.drop_column('is_admin')

    with op.batch_alter_table('event') as batch_op:
        batch_op.drop_column('created_at')
