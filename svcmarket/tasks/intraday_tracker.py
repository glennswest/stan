"""
Task 4: Intraday price tracking
Captures stock price movements every 15 minutes during market hours.
"""

import os
import logging
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz

from database import db

logger = logging.getLogger(__name__)

class IntradayTracker:
    """Handles intraday price tracking during market hours."""
    
    def __init__(self):
        # NASDAQ trading hours (EST)
        self.market_timezone = pytz.timezone('US/Eastern')
        self.market_open_time = "09:30"   # 9:30 AM EST
        self.market_close_time = "16:00"  # 4:00 PM EST
        self.tracking_interval = 15       # Track every 15 minutes
        
    def is_market_day(self) -> bool:
        """Check if today is a market trading day (Monday-Friday, excluding holidays)."""
        now = datetime.now(self.market_timezone)
        
        # Check if it's a weekday (0=Monday, 6=Sunday)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Basic holiday check (can be expanded)
        month, day = now.month, now.day
        
        # New Year's Day
        if month == 1 and day == 1:
            return False
        
        # Independence Day
        if month == 7 and day == 4:
            return False
        
        # Christmas Day
        if month == 12 and day == 25:
            return False
        
        # TODO: Add more sophisticated holiday checking
        return True
    
    def is_market_hours(self, force=False) -> bool:
        """Check if market is currently open for trading."""
        if force:
            logger.info("Force flag set, running tracking regardless of market hours")
            return True
            
        if not self.is_market_day():
            logger.debug("Market is closed today")
            return False
        
        now = datetime.now(self.market_timezone)
        current_time = now.strftime("%H:%M")
        
        # Check if current time is within market hours (9:30 AM - 4:00 PM EST)
        if self.market_open_time <= current_time < self.market_close_time:
            return True
        
        logger.debug(f"Outside market hours. Current time: {current_time} EST")
        return False
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current real-time price for a stock symbol."""
        try:
            stock = yf.Ticker(symbol)
            
            # Get the most recent price data
            # Try to get intraday data first
            recent_data = stock.history(period="1d", interval="1m")
            
            if not recent_data.empty:
                # Get the most recent price (last minute)
                current_price = float(recent_data['Close'].iloc[-1])
                logger.debug(f"Current price for {symbol}: ${current_price}")
                return round(current_price, 2)
            
            # Fallback to basic info if intraday data isn't available
            info = stock.info
            if 'regularMarketPrice' in info:
                current_price = float(info['regularMarketPrice'])
                return round(current_price, 2)
            elif 'previousClose' in info:
                # Use previous close as fallback
                current_price = float(info['previousClose'])
                return round(current_price, 2)
            
            logger.warning(f"No current price data available for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {str(e)}")
            return None
    
    def get_stocks_to_track(self) -> List[Dict]:
        """Get list of stocks from database for intraday tracking."""
        try:
            query = """
                SELECT id, symbol 
                FROM stocks 
                WHERE symbol IS NOT NULL 
                ORDER BY symbol
            """
            result = db.execute_query(query)
            
            stocks = [{'id': row[0], 'symbol': row[1]} for row in result]
            logger.debug(f"Found {len(stocks)} stocks for intraday tracking")
            return stocks
            
        except Exception as e:
            logger.error(f"Error fetching stocks from database: {str(e)}")
            return []
    
    def get_daily_record_id(self, stock_id: int) -> Optional[int]:
        """Get the daily record ID for today's trading session."""
        try:
            today = datetime.now(self.market_timezone).date()
            
            query = """
                SELECT id FROM daily 
                WHERE stock_id = :stock_id AND date = :date
                LIMIT 1
            """
            result = db.execute_query(query, {'stock_id': stock_id, 'date': today})
            
            if result:
                return result[0][0]
            
            logger.warning(f"No daily record found for stock_id {stock_id} on {today}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching daily record for stock_id {stock_id}: {str(e)}")
            return None
    
    def insert_tracking_record(self, daily_id: int, stock_id: int, symbol: str, price: float) -> bool:
        """Insert a new tracking record."""
        try:
            now = datetime.now(self.market_timezone)
            
            with db.get_session() as session:
                from sqlalchemy import text
                
                insert_query = """
                    INSERT INTO tracking (
                        daily_id, stock_id, symbol, timestamp, price
                    ) VALUES (
                        :daily_id, :stock_id, :symbol, :timestamp, :price
                    )
                """
                
                session.execute(text(insert_query), {
                    'daily_id': daily_id,
                    'stock_id': stock_id,
                    'symbol': symbol,
                    'timestamp': now,
                    'price': price
                })
                
            logger.debug(f"Inserted tracking record for {symbol}: ${price} at {now.strftime('%H:%M:%S')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert tracking record for {symbol}: {str(e)}")
            return False
    
    def track_stock_price(self, stock_id: int, symbol: str) -> bool:
        """Track current price for a single stock."""
        logger.debug(f"Tracking price for {symbol}")
        
        # Get current price
        current_price = self.get_current_price(symbol)
        if current_price is None:
            return False
        
        # Get daily record ID
        daily_id = self.get_daily_record_id(stock_id)
        if daily_id is None:
            logger.warning(f"No daily record found for {symbol}, skipping tracking")
            return False
        
        # Insert tracking record
        return self.insert_tracking_record(daily_id, stock_id, symbol, current_price)
    
    def should_track_now(self) -> bool:
        """Check if we should track prices at this specific time."""
        if not self.is_market_hours():
            return False
        
        now = datetime.now(self.market_timezone)
        
        # Check if current time is on a 15-minute interval
        # Track at :00, :15, :30, :45 of each hour
        if now.minute % 15 == 0:
            return True
        
        logger.debug(f"Not on 15-minute interval. Current minute: {now.minute}")
        return False
    
    def track_intraday_prices(self, force=False) -> Dict[str, int]:
        """Main method to track intraday prices for all stocks."""
        logger.info("Starting intraday price tracking")
        
        if not force and not self.should_track_now():
            if not self.is_market_hours():
                return {'skipped': True, 'reason': 'Market is closed'}
            else:
                return {'skipped': True, 'reason': 'Not on 15-minute interval'}
        
        if force:
            logger.info("Force flag enabled, tracking regardless of schedule")
        elif not self.is_market_hours(force):
            return {'skipped': True, 'reason': 'Market is closed'}
        
        # Test database connection
        if not db.test_connection():
            raise Exception("Database connection failed")
        
        stocks = self.get_stocks_to_track()
        if not stocks:
            return {'error': 'No stocks found to track'}
        
        logger.info(f"Tracking intraday prices for {len(stocks)} stocks")
        
        success_count = 0
        error_count = 0
        
        for stock in stocks:
            try:
                stock_id = stock['id']
                symbol = stock['symbol']
                
                if self.track_stock_price(stock_id, symbol):
                    success_count += 1
                else:
                    error_count += 1
                
                # Progress reporting every 200 stocks (since this runs more frequently)
                if (success_count + error_count) % 200 == 0:
                    logger.info(f"Intraday tracking - Progress: {success_count + error_count}/{len(stocks)} "
                               f"(Success: {success_count}, Errors: {error_count})")
                
                # Small delay to avoid rate limiting
                import time
                time.sleep(0.1)  # Slightly longer delay for large stock counts
                
            except Exception as e:
                logger.error(f"Unexpected error tracking {symbol}: {str(e)}")
                error_count += 1
        
        result = {
            'success_count': success_count,
            'error_count': error_count,
            'total_processed': len(stocks),
            'timestamp': datetime.now(self.market_timezone).strftime('%H:%M:%S EST')
        }
        
        logger.info(f"Intraday tracking completed: {result}")
        return result