"""create nasdaq_stocks table

Revision ID: 4d52db3dee0d
Revises: 
Create Date: 2025-09-10 13:51:17.768746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d52db3dee0d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('nasdaq_stocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('avg_daily_volume', sa.BigInteger(), nullable=True),
        sa.Column('avg_daily_min_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('avg_daily_max_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('beginning_of_year_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('previous_day_opening_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('previous_day_closing_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_symbol', 'symbol', unique=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('nasdaq_stocks')
