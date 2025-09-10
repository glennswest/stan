"""create tracking table

Revision ID: 7d6099238ac3
Revises: 258638fc8130
Create Date: 2025-09-10 14:14:49.056602

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d6099238ac3'
down_revision: Union[str, Sequence[str], None] = '258638fc8130'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('daily_id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['daily_id'], ['daily.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.Index('idx_daily_timestamp', 'daily_id', 'timestamp'),
        sa.Index('idx_symbol_timestamp', 'symbol', 'timestamp'),
        sa.Index('idx_timestamp', 'timestamp'),
        sa.Index('idx_stock_timestamp', 'stock_id', 'timestamp')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('tracking')
