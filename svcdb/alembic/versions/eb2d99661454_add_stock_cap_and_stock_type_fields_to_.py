"""add stock_cap and stock_type fields to stocks table

Revision ID: eb2d99661454
Revises: 7d6099238ac3
Create Date: 2025-09-10 15:38:47.937961

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eb2d99661454'
down_revision: Union[str, Sequence[str], None] = '7d6099238ac3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add stock_cap field (market capitalization category)
    op.add_column('stocks', sa.Column('stock_cap', sa.String(20), nullable=True, comment='Market cap category (Mega-Cap, Large-Cap, Mid-Cap, Small-Cap, Micro-Cap, Nano-Cap)'))
    
    # Add stock_type field (e.g., 'Common Stock', 'ETF', 'REIT', etc.)
    op.add_column('stocks', sa.Column('stock_type', sa.String(50), nullable=True, comment='Type of security (Common Stock, ETF, REIT, etc.)'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the added columns
    op.drop_column('stocks', 'stock_type')
    op.drop_column('stocks', 'stock_cap')
