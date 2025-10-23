# STAN Database Service (svcdb)

Database schema management and migrations for the STAN stock market data system.

## Overview

This service manages the database schema using Alembic, providing version-controlled database migrations. It defines the structure for storing stock metadata, daily OHLC data, and intraday price tracking.

## Database Schema

### Tables

#### stocks
Primary table for stock metadata and rolling statistics.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `symbol` | VARCHAR(10) | Stock ticker symbol (unique) |
| `avg_daily_volume` | BIGINT | Average daily trading volume |
| `avg_daily_min_price` | DECIMAL(10,2) | Average daily low price |
| `avg_daily_max_price` | DECIMAL(10,2) | Average daily high price |
| `beginning_of_year_price` | DECIMAL(10,2) | Price at start of year |
| `previous_day_opening_price` | DECIMAL(10,2) | Previous trading day's open |
| `previous_day_closing_price` | DECIMAL(10,2) | Previous trading day's close |
| `exchange` | VARCHAR(50) | Stock exchange (e.g., NASDAQ, NYSE) |
| `stock_cap` | VARCHAR(50) | Market cap category (Large, Mid, Small) |
| `stock_type` | VARCHAR(50) | Stock classification |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes:**
- `idx_symbol` - Unique index on symbol column

#### daily
Stores daily OHLC (Open, High, Low, Close) data for each stock.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `stock_id` | INTEGER | Foreign key to stocks.id |
| `date` | DATE | Trading date |
| `open` | DECIMAL(10,2) | Opening price |
| `high` | DECIMAL(10,2) | Highest price of the day |
| `low` | DECIMAL(10,2) | Lowest price of the day |
| `close` | DECIMAL(10,2) | Closing price |
| `volume` | BIGINT | Trading volume |
| `created_at` | DATETIME | Record creation timestamp |
| `updated_at` | DATETIME | Last update timestamp |

**Indexes:**
- `idx_stock_date` - Unique index on (stock_id, date)

**Foreign Keys:**
- `stock_id` → `stocks.id` (CASCADE on delete)

#### tracking
Captures intraday price snapshots for tracking price movements.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `stock_id` | INTEGER | Foreign key to stocks.id |
| `timestamp` | DATETIME | Exact time of price capture |
| `price` | DECIMAL(10,2) | Stock price at timestamp |

**Indexes:**
- `idx_stock_timestamp` - Index on (stock_id, timestamp)

**Foreign Keys:**
- `stock_id` → `stocks.id` (CASCADE on delete)

## Setup

### Prerequisites

- Python 3.9+
- MySQL/MariaDB server
- Database credentials with CREATE/ALTER privileges

### Installation

1. **Create virtual environment**:
   ```bash
   cd svcdb
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install alembic pymysql sqlalchemy
   ```

3. **Configure database connection**:
   Edit `alembic.ini` and update the database URL:
   ```ini
   sqlalchemy.url = mysql+pymysql://user:password@host:port/stan
   ```

4. **Initialize database**:
   ```bash
   alembic upgrade head
   ```

## Usage

### View Migration History

```bash
alembic history
```

### Check Current Version

```bash
alembic current
```

### Upgrade to Latest Version

```bash
alembic upgrade head
```

### Upgrade to Specific Version

```bash
alembic upgrade <revision_id>
```

### Downgrade One Version

```bash
alembic downgrade -1
```

### Downgrade to Specific Version

```bash
alembic downgrade <revision_id>
```

## Migration History

The database schema has evolved through the following migrations:

1. **4d52db3dee0d** - Create nasdaq_stocks table
   - Initial table for stock metadata

2. **deffbb5ac342** - Rename nasdaq_stocks to stocks and add fields
   - Renamed table for broader use
   - Added exchange and other fields

3. **fe8be8b699f9** - Create daily_stock_data table
   - Added table for daily OHLC data

4. **258638fc8130** - Rename daily_stock_data to daily
   - Simplified table name

5. **7d6099238ac3** - Create tracking table
   - Added intraday price tracking capability

6. **eb2d99661454** - Add stock_cap and stock_type fields to stocks
   - Enhanced stock classification

7. **06b048d7cc82** - Change stock_cap to string for market cap categories
   - Modified field type for better categorization

## Creating New Migrations

### Generate Migration Automatically

Alembic can auto-generate migrations by comparing your models to the database:

```bash
alembic revision --autogenerate -m "description of changes"
```

### Create Empty Migration

For manual migrations:

```bash
alembic revision -m "description of changes"
```

This creates a new file in `alembic/versions/` with two functions:
- `upgrade()` - Changes to apply
- `downgrade()` - How to revert changes

### Example Migration

```python
def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('stocks',
        sa.Column('new_field', sa.String(50), nullable=True)
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('stocks', 'new_field')
```

### Apply the Migration

```bash
alembic upgrade head
```

## Common Operations

### Add a New Column

```bash
alembic revision -m "add column_name to table_name"
```

Edit the generated file:
```python
def upgrade():
    op.add_column('table_name',
        sa.Column('column_name', sa.String(100), nullable=True)
    )

def downgrade():
    op.drop_column('table_name', 'column_name')
```

### Create a New Table

```bash
alembic revision -m "create new_table"
```

Edit the generated file:
```python
def upgrade():
    op.create_table('new_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('new_table')
```

### Add an Index

```python
def upgrade():
    op.create_index('idx_column_name', 'table_name', ['column_name'])

def downgrade():
    op.drop_index('idx_column_name', 'table_name')
```

## Troubleshooting

### Connection Errors

If you encounter connection issues:
1. Verify database server is running
2. Check credentials in `alembic.ini`
3. Ensure the database exists (`CREATE DATABASE stan;`)
4. Verify network connectivity to database host

### Migration Conflicts

If migrations are out of sync:
```bash
# Check current version
alembic current

# View migration history
alembic history

# Manually set version (use with caution)
alembic stamp <revision_id>
```

### Rollback Failed Migration

```bash
# Downgrade to previous version
alembic downgrade -1

# Fix the migration file
# Then upgrade again
alembic upgrade head
```

## Best Practices

1. **Always test migrations** on a development database first
2. **Backup production data** before running migrations
3. **Use descriptive migration messages** that explain what changed
4. **Keep migrations small and focused** on single changes
5. **Never modify existing migrations** that have been deployed
6. **Always provide downgrade paths** for easy rollback

## Database Maintenance

### Backup Database

```bash
mysqldump -u user -p stan > backup_$(date +%Y%m%d).sql
```

### Restore from Backup

```bash
mysql -u user -p stan < backup_20250910.sql
```

### Check Table Sizes

```sql
SELECT
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS size_mb
FROM information_schema.TABLES
WHERE table_schema = 'stan'
ORDER BY size_mb DESC;
```

## Related Documentation

- [Main Project README](../README.md)
- [svcmarket Service Documentation](../svcmarket/README.md)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

## Support

For issues with migrations or database schema, check:
1. Alembic documentation
2. Migration history: `alembic history`
3. Database logs
4. Contact development team
