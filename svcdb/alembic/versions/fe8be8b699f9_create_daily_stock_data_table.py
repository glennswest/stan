"""create daily_stock_data table

Revision ID: fe8be8b699f9
Revises: deffbb5ac342
Create Date: 2025-09-10 14:06:05.086922

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fe8be8b699f9'
down_revision: Union[str, Sequence[str], None] = 'deffbb5ac342'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('daily_stock_data',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stock_id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('opening_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('closing_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('max_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('min_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('volume', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ondelete='CASCADE'),
        sa.Index('idx_stock_date', 'stock_id', 'date', unique=True),
        sa.Index('idx_symbol_date', 'symbol', 'date'),
        sa.Index('idx_date', 'date')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('daily_stock_data')
