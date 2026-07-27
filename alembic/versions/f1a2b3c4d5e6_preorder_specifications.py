"""add specifications column to preorders

Revision ID: f1a2b3c4d5e6
Revises: de0098880725
Create Date: 2026-07-27

Adds one nullable Text column so customers can specify exactly which product
they want in a pre-order request. Nullable -> safe to add to a table that
already has rows (no server_default needed, no NOT-NULL trap).
"""
from typing import Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = 'de0098880725'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('preorders',
                  sa.Column('specifications', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('preorders', 'specifications')
