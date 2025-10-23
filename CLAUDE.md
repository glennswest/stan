# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

STAN (Stock Trading Analysis Network) is a stock market data management system with two main services:

1. **svcmarket** - Stock market data collection and processing service
2. **svcdb** - Database schema management using Alembic migrations

## Development Commands

### svcmarket Service

```bash
cd svcmarket
source venv/bin/activate

# Run service continuously (scheduled mode)
python main.py

# Run individual tasks manually
python main.py 1  # Daily stock updates
python main.py 2  # Opening prices
python main.py 3  # Closing prices
python main.py 4  # Intraday tracking

# Test database connection
python -c "from database import db; print('Connected:', db.test_connection())"
```

### svcdb Database Migrations

```bash
cd svcdb
source venv/bin/activate

# View migration history
alembic history

# Check current version
alembic current

# Upgrade to latest
alembic upgrade head

# Create new migration
alembic revision -m "description of changes"
```

## Architecture

```
stan/
├── svcmarket/              # Stock market data service
│   ├── tasks/             # Modular task implementations
│   │   ├── stock_updater.py           # Daily stock updates
│   │   ├── opening_price_updater.py   # Opening price tracking
│   │   ├── closing_price_updater.py   # Closing price updates
│   │   └── intraday_tracker.py        # 15-min price tracking
│   ├── main.py            # Service orchestrator with scheduling
│   ├── database.py        # SQLAlchemy connection layer
│   ├── requirements.txt   # Python dependencies
│   └── .env              # Environment configuration (not in git)
├── svcdb/                 # Database migrations
│   ├── alembic/          # Alembic migration scripts
│   │   └── versions/     # Individual migration files
│   └── alembic.ini       # Alembic configuration
└── README.md             # Main project documentation
```

## Database Schema

- **stocks** - Stock metadata and rolling statistics
- **daily** - Daily OHLC (Open, High, Low, Close) data
- **tracking** - Intraday price snapshots (every 15 minutes)

## Dependencies

### svcmarket
- yfinance - Yahoo Finance data fetching
- SQLAlchemy - Database ORM
- PyMySQL - MySQL connector
- schedule - Task scheduling
- python-dotenv - Environment variable management

### svcdb
- alembic - Database migrations
- SQLAlchemy - Database toolkit

## Testing

```bash
# Test svcmarket tasks individually
cd svcmarket
python main.py 1  # Test daily updates
python main.py 2  # Test opening prices (use force=True for manual testing)

# Test database connection
python -c "from database import db; print('Connected:', db.test_connection())"
```

## Notes

- Git repository initialized and tracked
- Virtual environments in each service directory (not tracked in git)
- Environment variables stored in `.env` files (not tracked in git)
- Logging to both console and `svcmarket.log`
- Scheduled tasks run automatically when service is running
- Database migrations are version-controlled with Alembic