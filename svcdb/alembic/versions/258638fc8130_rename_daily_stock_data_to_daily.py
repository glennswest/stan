"""rename daily_stock_data to daily

Revision ID: 258638fc8130
Revises: fe8be8b699f9
Create Date: 2025-09-10 14:12:04.099179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '258638fc8130'
down_revision: Union[str, Sequence[str], None] = 'fe8be8b699f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename table from daily_stock_data to daily
    op.rename_table('daily_stock_data', 'daily')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename table back to daily_stock_data
    op.rename_table('daily', 'daily_stock_data')
