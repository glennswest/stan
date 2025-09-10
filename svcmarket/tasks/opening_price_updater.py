"""
Task 2: Opening price updates
Updates stock opening prices 5 minutes after NASDAQ market opens (9:35 AM EST).
"""

import os
import logging
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz

from database import db

logger = logging.getLogger(__name__)

class OpeningPriceUpdater:
    """Handles opening price updates after market open."""
    
    def __init__(self):
        # NASDAQ trading hours (EST)
        self.market_timezone = pytz.timezone('US/Eastern')
        self.market_open_time = "09:30"  # NASDAQ opens at 9:30 AM EST
        self.update_time = "09:35"       # Update 5 minutes after open
        
    def is_market_day(self) -> bool:
        """Check if today is a market trading day (Monday-Friday, excluding holidays)."""
        now = datetime.now(self.market_timezone)
        
        # Check if it's a weekday (0=Monday, 6=Sunday)
        if now.weekday() >= 5:  # Saturday or Sunday
            return False
        
        # Basic holiday check (can be expanded)
        # For now, just check major holidays that are consistent each year
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
        # (MLK Day, Presidents Day, Good Friday, Memorial Day, Labor Day, Thanksgiving, etc.)
        
        return True
    
    def should_run_update(self, force=False) -> bool:
        """Check if we should run the opening price update now."""
        if force:
            logger.info("Force flag set, running update regardless of time")
            return True
            
        if not self.is_market_day():
            logger.info("Market is closed today, skipping opening price update")
            return False
        
        now = datetime.now(self.market_timezone)
        current_time = now.strftime("%H:%M")
        
        # Only run between 9:35 and 10:00 AM EST
        if "09:35" <= current_time <= "10:00":
            return True
        
        logger.info(f"Current time {current_time} EST is outside update window (09:35-10:00)")
        return False
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current/opening price for a stock symbol."""
        try:
            stock = yf.Ticker(symbol)
            
            # Get today's data
            today_data = stock.history(period="1d", interval="1m")
            
            if today_data.empty:
                logger.warning(f"No intraday data available for {symbol}")
                return None
            
            # Get the opening price (first data point of the day)
            opening_price = float(today_data['Open'].iloc[0])
            
            logger.debug(f"Opening price for {symbol}: ${opening_price}")
            return round(opening_price, 2)
            
        except Exception as e:
            logger.error(f"Error fetching opening price for {symbol}: {str(e)}")
            return None
    
    def get_stocks_to_update(self) -> List[Dict]:
        """Get list of stocks from database that need opening price updates."""
        try:
            query = """
                SELECT id, symbol 
                FROM stocks 
                WHERE symbol IS NOT NULL 
                ORDER BY symbol
            """
            result = db.execute_query(query)
            
            stocks = [{'id': row[0], 'symbol': row[1]} for row in result]
            logger.info(f"Found {len(stocks)} stocks to update opening prices")
            return stocks
            
        except Exception as e:
            logger.error(f"Error fetching stocks from database: {str(e)}")
            return []
    
    def update_opening_price(self, stock_id: int, symbol: str) -> bool:
        """Update opening price for a specific stock."""
        logger.debug(f"Updating opening price for {symbol} (ID: {stock_id})")
        
        opening_price = self.get_current_price(symbol)
        if opening_price is None:
            return False
        
        try:
            with db.get_session() as session:
                update_query = """
                    UPDATE stocks 
                    SET previous_day_opening_price = :opening_price,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :stock_id
                """
                from sqlalchemy import text
                session.execute(
                    text(update_query), 
                    {'opening_price': opening_price, 'stock_id': stock_id}
                )
                
            logger.info(f"Updated opening price for {symbol}: ${opening_price}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update opening price for {symbol}: {str(e)}")
            return False
    
    def insert_daily_data(self, stock_id: int, symbol: str, opening_price: float) -> bool:
        """Insert today's opening data into daily table."""
        try:
            today = datetime.now(self.market_timezone).date()
            
            # Check if today's data already exists
            check_query = """
                SELECT id FROM daily 
                WHERE stock_id = :stock_id AND date = :date
            """
            existing = db.execute_query(check_query, {'stock_id': stock_id, 'date': today})
            
            if existing:
                # Update existing record
                update_query = """
                    UPDATE daily 
                    SET opening_price = :opening_price,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE stock_id = :stock_id AND date = :date
                """
                db.execute_query(update_query, {
                    'opening_price': opening_price,
                    'stock_id': stock_id,
                    'date': today
                })
                logger.debug(f"Updated daily opening price for {symbol}")
            else:
                # Insert new daily record
                insert_query = """
                    INSERT INTO daily (stock_id, symbol, date, opening_price)
                    VALUES (:stock_id, :symbol, :date, :opening_price)
                """
                db.execute_query(insert_query, {
                    'stock_id': stock_id,
                    'symbol': symbol,
                    'date': today,
                    'opening_price': opening_price
                })
                logger.debug(f"Inserted new daily record for {symbol}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert/update daily data for {symbol}: {str(e)}")
            return False
    
    def update_opening_prices(self, force=False) -> Dict[str, int]:
        """Main method to update opening prices for all stocks."""
        logger.info("Starting opening price update")
        
        if not self.should_run_update(force):
            return {'skipped': True, 'reason': 'Outside update window or market closed'}
        
        # Test database connection
        if not db.test_connection():
            raise Exception("Database connection failed")
        
        stocks = self.get_stocks_to_update()
        if not stocks:
            return {'error': 'No stocks found to update'}
        
        logger.info(f"Updating opening prices for {len(stocks)} stocks")
        
        success_count = 0
        error_count = 0
        daily_inserted = 0
        
        for stock in stocks:
            try:
                stock_id = stock['id']
                symbol = stock['symbol']
                
                opening_price = self.get_current_price(symbol)
                if opening_price is None:
                    error_count += 1
                    continue
                
                # Update stocks table
                if self.update_opening_price(stock_id, symbol):
                    success_count += 1
                    
                    # Also insert/update daily data
                    if self.insert_daily_data(stock_id, symbol, opening_price):
                        daily_inserted += 1
                else:
                    error_count += 1
                
                # Small delay to avoid rate limiting
                import time
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Unexpected error updating {symbol}: {str(e)}")
                error_count += 1
        
        result = {
            'success_count': success_count,
            'error_count': error_count,
            'daily_records': daily_inserted,
            'total_processed': len(stocks)
        }
        
        logger.info(f"Opening price update completed: {result}")
        return result