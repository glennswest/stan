"""rename nasdaq_stocks to stocks and add exchange field

Revision ID: deffbb5ac342
Revises: 4d52db3dee0d
Create Date: 2025-09-10 13:55:29.033487

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'deffbb5ac342'
down_revision: Union[str, Sequence[str], None] = '4d52db3dee0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add exchange column to existing table
    op.add_column('nasdaq_stocks', sa.Column('exchange', sa.String(20), nullable=True))
    
    # Rename table from nasdaq_stocks to stocks
    op.rename_table('nasdaq_stocks', 'stocks')


def downgrade() -> None:
    """Downgrade schema."""
    # Rename table back to nasdaq_stocks
    op.rename_table('stocks', 'nasdaq_stocks')
    
    # Drop exchange column
    op.drop_column('nasdaq_stocks', 'exchange')
