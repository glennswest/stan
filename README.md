# STAN - Stock Trading Analysis Network

A comprehensive stock market data management system consisting of a data collection service and database management utilities.

## Project Overview

STAN is designed to collect, store, and manage stock market data with real-time and historical tracking capabilities. The system is organized into two main components:

- **svcmarket**: Stock market data collection and processing service
- **svcdb**: Database schema management using Alembic migrations

## Architecture

```
stan/
├── svcmarket/          # Stock market data service
│   ├── tasks/         # Modular task implementations
│   ├── main.py        # Service orchestrator
│   └── database.py    # Database connection layer
├── svcdb/             # Database migrations
│   └── alembic/       # Alembic migration scripts
└── README.md          # This file
```

## Components

### 1. Stock Market Service (svcmarket)

A Python service that automates stock market data collection and updates throughout the trading day.

**Key Features:**
- Daily stock metadata updates
- Opening price tracking (9:35 AM EST)
- Closing price updates (4:05 PM EST)
- Intraday price tracking (every 15 minutes during market hours)
- Multi-source data fetching (yfinance, Alpha Vantage)
- Automatic retry and fallback mechanisms

**See [svcmarket/README.md](svcmarket/README.md) for detailed documentation.**

### 2. Database Service (svcdb)

Database schema management using Alembic for version-controlled migrations.

**Database Schema:**
- `stocks` - Stock metadata and daily statistics
- `daily` - Daily OHLC (Open, High, Low, Close) data
- `tracking` - Intraday price tracking data

**See [svcdb/README.md](svcdb/README.md) for migration details.**

## Quick Start

### Prerequisites

- Python 3.9 or higher
- MySQL/MariaDB database server
- API keys (optional): Alpha Vantage for fallback data source

### Installation

1. **Clone the repository**:
   ```bash
   cd /path/to/stan
   ```

2. **Set up svcmarket**:
   ```bash
   cd svcmarket
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   Edit `svcmarket/.env` with your database credentials:
   ```env
   DB_HOST=your_db_host
   DB_NAME=stan
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   ALPHA_VANTAGE_API_KEY=your_api_key  # Optional
   ```

4. **Set up database**:
   ```bash
   cd ../svcdb
   python -m venv venv
   source venv/bin/activate
   pip install alembic pymysql
   alembic upgrade head
   ```

5. **Test the connection**:
   ```bash
   cd ../svcmarket
   python -c "from database import db; print('Connected:', db.test_connection())"
   ```

### Running the Service

**Automated mode** (runs continuously with scheduled tasks):
```bash
cd svcmarket
source venv/bin/activate
python main.py
```

**Manual task execution**:
```bash
python main.py 1  # Daily stock updates
python main.py 2  # Opening prices
python main.py 3  # Closing prices
python main.py 4  # Intraday tracking
```

## Data Sources

1. **yfinance** (Primary) - Free Yahoo Finance API wrapper
2. **Alpha Vantage** (Fallback) - Requires free API key from https://www.alphavantage.co

## Stock Coverage

The system currently tracks 30 major stocks across various sectors:
- Technology: AAPL, GOOGL, MSFT, AMZN, META, NVDA, TSLA
- Financial: JPM, V, MA
- Healthcare: JNJ, UNH
- Consumer: PG, HD, DIS, COST, WMT
- And more...

## Schedule

When running in automated mode:
- **9:00 AM EST**: Daily stock metadata updates
- **9:35 AM EST**: Opening price capture (5 min after market open)
- **9:30 AM - 4:00 PM EST**: Intraday tracking every 15 minutes
- **4:05 PM EST**: Closing prices and daily OHLC data

## Database Schema

### stocks
Stores stock metadata and rolling averages:
- `symbol` - Stock ticker symbol (e.g., AAPL)
- `avg_daily_volume` - Average trading volume
- `avg_daily_min_price` - Average daily low price
- `avg_daily_max_price` - Average daily high price
- `beginning_of_year_price` - Price at year start
- `previous_day_opening_price` - Prior day's opening price
- `previous_day_closing_price` - Prior day's closing price
- `exchange` - Stock exchange (e.g., NASDAQ)
- `stock_cap` - Market capitalization category
- `stock_type` - Stock classification

### daily
Stores daily OHLC data:
- `stock_id` - Foreign key to stocks table
- `date` - Trading date
- `open` - Opening price
- `high` - Highest price
- `low` - Lowest price
- `close` - Closing price
- `volume` - Trading volume

### tracking
Stores intraday price snapshots:
- `stock_id` - Foreign key to stocks table
- `timestamp` - Exact time of price capture
- `price` - Stock price at timestamp

## Logging

All services log to both console and file:
- svcmarket logs: `svcmarket/svcmarket.log`
- Configure log level via environment variable: `LOG_LEVEL=DEBUG|INFO|WARNING|ERROR`

## Error Handling

The system includes robust error handling:
- Database transaction rollback on failures
- Automatic retry with exponential backoff
- Fallback to secondary data sources
- Comprehensive error logging
- Graceful handling of market hours and holidays

## Development

### Adding New Stocks

Edit the stock list in `svcmarket/tasks/stock_updater.py` to add or remove tracked stocks.

### Creating Database Migrations

```bash
cd svcdb
source venv/bin/activate
alembic revision -m "description of changes"
# Edit the generated migration file
alembic upgrade head
```

### Testing

Test individual tasks manually:
```bash
cd svcmarket
python main.py 1  # Test daily updates
python main.py 2  # Test opening prices
```

## Troubleshooting

**Connection errors:**
- Verify database credentials in `.env`
- Ensure database server is running
- Check network connectivity

**Missing data:**
- Verify API keys are correct (if using Alpha Vantage)
- Check market hours (data only available during trading days)
- Review logs for specific error messages

**Schedule not running:**
- Ensure system timezone matches EST/EDT
- Verify cron jobs or service managers are configured correctly

## Contributing

1. Create feature branches from `main`
2. Add appropriate tests
3. Update documentation
4. Submit pull request

## License

Internal project - all rights reserved.

## Support

For issues or questions, contact the development team or review logs in `svcmarket/svcmarket.log`.
