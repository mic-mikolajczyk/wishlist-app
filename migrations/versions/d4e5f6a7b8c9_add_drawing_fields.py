"""add drawing fields

Revision ID: d4e5f6a7b8c9
revises: c1e2f3a4b5c6
Create Date: 2025-11-05 00:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('event', sa.Column('drawing_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
    with op.batch_alter_table('event') as batch_op:
        batch_op.alter_column('drawing_enabled', server_default=None)

    op.add_column('event_participant', sa.Column('assigned_recipient_user_id', sa.Integer(), nullable=True))
    op.add_column('event_participant', sa.Column('drawn_at', sa.DateTime(), nullable=True))
    # Foreign key to user for recipient
    with op.batch_alter_table('event_participant') as batch_op:
        batch_op.create_foreign_key('fk_event_participant_recipient_user', 'user', ['assigned_recipient_user_id'], ['id'])


def downgrade():
    with op.batch_alter_table('event_participant') as batch_op:
        batch_op.drop_constraint('fk_event_participant_recipient_user', type_='foreignkey')
    op.drop_column('event_participant', 'drawn_at')
    op.drop_column('event_participant', 'assigned_recipient_user_id')
    op.drop_column('event', 'drawing_enabled')
