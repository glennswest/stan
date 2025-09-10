"""change stock_cap to string for market cap categories

Revision ID: 06b048d7cc82
Revises: eb2d99661454
Create Date: 2025-09-10 15:39:58.424023

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06b048d7cc82'
down_revision: Union[str, Sequence[str], None] = 'eb2d99661454'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change stock_cap from DECIMAL to VARCHAR for market cap categories
    op.alter_column('stocks', 'stock_cap', type_=sa.String(20), comment='Market cap category (Mega-Cap, Large-Cap, Mid-Cap, Small-Cap, Micro-Cap, Nano-Cap)')


def downgrade() -> None:
    """Downgrade schema."""
    # Revert stock_cap back to DECIMAL
    op.alter_column('stocks', 'stock_cap', type_=sa.DECIMAL(15, 2), comment='Market capitalization in billions USD')
