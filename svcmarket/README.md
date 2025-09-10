# Stock Market Data Service (svcmarket)

A Python service that manages stock market data updates and processing tasks.

## Features

### Task 1: Daily Stock Table Updates
- Updates the `stocks` table with current market data
- Fetches data from multiple sources (yfinance, Alpha Vantage)
- Calculates averages and key metrics
- Runs automatically once per day at 9:00 AM EST

### Task 2: Opening Price Updates
- Updates stock opening prices 5 minutes after NASDAQ opens (9:35 AM EST)
- Fetches real-time opening prices using yfinance
- Updates both `stocks` and `daily` tables
- Only runs on market trading days (Monday-Friday, excluding holidays)

### Task 3: Closing Price Updates
- Updates stock closing prices 5 minutes after market close (4:05 PM EST)
- Fetches end-of-day prices, high/low, and volume data
- Updates `stocks` table closing prices and complete `daily` OHLCV data
- Provides comprehensive daily trading summary

## Setup

1. **Install Dependencies**:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Edit `.env` file with your database credentials and API keys:
   ```env
   DB_HOST=192.168.1.72
   DB_NAME=stan
   DB_USER=stan
   DB_PASSWORD=stan123
   ALPHA_VANTAGE_API_KEY=your_api_key_here
   ```

3. **Test Database Connection**:
   ```bash
   python -c "from database import db; print('Connected:', db.test_connection())"
   ```

## Usage

### Run Continuously (Scheduled)
```bash
python main.py
```
The service will schedule all tasks:
- **9:00 AM EST**: Task 1 - Daily stock updates
- **9:35 AM EST**: Task 2 - Opening price updates  
- **4:05 PM EST**: Task 3 - Closing price updates

### Run Task Manually
```bash
python main.py 1  # Run Task 1 manually (Daily stock updates)
python main.py 2  # Run Task 2 manually (Opening price updates)
python main.py 3  # Run Task 3 manually (Closing price updates)
```

## Database Schema

The service works with the following tables:
- `stocks` - Stock metadata and daily averages
- `daily` - Daily OHLC data
- `tracking` - Intraday price tracking

## Data Sources

1. **yfinance** (Primary) - Free Yahoo Finance API
2. **Alpha Vantage** (Fallback) - Requires API key

## Stock Coverage

Currently tracks 30 major stocks including:
- AAPL, GOOGL, MSFT, AMZN, TSLA, META, NVDA
- JPM, JNJ, V, PG, UNH, HD, MA, DIS
- And 15 others...

## Logging

Logs are written to:
- Console output
- `svcmarket.log` file

## Error Handling

- Automatic retry with fallback data sources
- Database transaction rollback on errors
- Comprehensive error logging
- Graceful handling of API rate limits