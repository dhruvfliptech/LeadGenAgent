"""Add region to locations

Revision ID: 003
Revises: 002
Create Date: 2025-08-23 00:00:00
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('locations') as batch_op:
        try:
            batch_op.add_column(sa.Column('region', sa.String(length=100), nullable=True))
        except Exception:
            pass
        try:
            batch_op.create_index('ix_locations_region', ['region'], unique=False)
        except Exception:
            pass


def downgrade():
    with op.batch_alter_table('locations') as batch_op:
        try:
            batch_op.drop_index('ix_locations_region')
        except Exception:
            pass
        try:
            batch_op.drop_column('region')
        except Exception:
            pass


