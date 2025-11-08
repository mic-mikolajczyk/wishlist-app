"""Add currency column to wishlist_item

Revision ID: b4c7d2e9d111
Revises: 9ab3e6d1f2c7_add_missing_event_participant_columns
Create Date: 2025-11-05
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b4c7d2e9d111'
down_revision = '9ab3e6d1f2c7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('wishlist_item') as batch_op:
        batch_op.add_column(sa.Column('currency', sa.String(length=3), nullable=True))
    # Optionally backfill null currency to 'PLN'
    op.execute("UPDATE wishlist_item SET currency='PLN' WHERE currency IS NULL")


def downgrade():
    with op.batch_alter_table('wishlist_item') as batch_op:
        batch_op.drop_column('currency')
