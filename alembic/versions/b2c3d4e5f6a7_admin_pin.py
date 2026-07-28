"""add pin_hash to administrators (retailer action confirmation)

Revision ID: b2c3d4e5f6a7
Revises: f1a2b3c4d5e6
Create Date: 2026-07-28

Nullable column, safe to add to a populated table (no default needed). Stores a
hashed PIN a retailer types to confirm an irreversible order status change.
"""
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('administrators',
                  sa.Column('pin_hash', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('administrators', 'pin_hash')
