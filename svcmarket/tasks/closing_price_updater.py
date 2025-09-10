"""
Task 3: Closing price updates
Updates stock closing prices at market close (4:00 PM EST).
"""

import os
import logging
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pytz

from database import db

logger = logging.getLogger(__name__)

class ClosingPriceUpdater:
    """Handles closing price updates at market close."""
    
    def __init__(self):
        # NASDAQ trading hours (EST)
        self.market_timezone = pytz.timezone('US/Eastern')
        self.market_close_time = "16:00"  # NASDAQ closes at 4:00 PM EST
        self.update_time = "16:05"        # Update 5 minutes after close
        
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
        """Check if we should run the closing price update now."""
        if force:
            logger.info("Force flag set, running update regardless of time")
            return True
            
        if not self.is_market_day():
            logger.info("Market is closed today, skipping closing price update")
            return False
        
        now = datetime.now(self.market_timezone)
        current_time = now.strftime("%H:%M")
        
        # Run between 4:05 PM and 6:00 PM EST (after market close)
        if "16:05" <= current_time <= "18:00":
            return True
        
        logger.info(f"Current time {current_time} EST is outside update window (16:05-18:00)")
        return False
    
    def get_closing_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get closing price and other end-of-day data for a stock symbol."""
        try:
            stock = yf.Ticker(symbol)
            
            # Get today's data
            today_data = stock.history(period="1d", interval="1m")
            
            if today_data.empty:
                logger.warning(f"No intraday data available for {symbol}")
                # Fallback to daily data
                daily_data = stock.history(period="2d")
                if daily_data.empty:
                    return None
                
                last_day = daily_data.iloc[-1]
                return {
                    'closing_price': round(float(last_day['Close']), 2),
                    'high_price': round(float(last_day['High']), 2),
                    'low_price': round(float(last_day['Low']), 2),
                    'volume': int(last_day['Volume'])
                }
            
            # Get the closing data (last data point of the day)
            closing_data = today_data.iloc[-1]
            daily_high = float(today_data['High'].max())
            daily_low = float(today_data['Low'].min())
            daily_volume = int(today_data['Volume'].sum())
            
            result = {
                'closing_price': round(float(closing_data['Close']), 2),
                'high_price': round(daily_high, 2),
                'low_price': round(daily_low, 2),
                'volume': daily_volume
            }
            
            logger.debug(f"Closing data for {symbol}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching closing data for {symbol}: {str(e)}")
            return None
    
    def get_stocks_to_update(self) -> List[Dict]:
        """Get list of stocks from database that need closing price updates."""
        try:
            query = """
                SELECT id, symbol 
                FROM stocks 
                WHERE symbol IS NOT NULL 
                ORDER BY symbol
            """
            result = db.execute_query(query)
            
            stocks = [{'id': row[0], 'symbol': row[1]} for row in result]
            logger.info(f"Found {len(stocks)} stocks to update closing prices")
            return stocks
            
        except Exception as e:
            logger.error(f"Error fetching stocks from database: {str(e)}")
            return []
    
    def update_closing_price(self, stock_id: int, symbol: str) -> bool:
        """Update closing price for a specific stock."""
        logger.debug(f"Updating closing price for {symbol} (ID: {stock_id})")
        
        closing_data = self.get_closing_price(symbol)
        if closing_data is None:
            return False
        
        try:
            with db.get_session() as session:
                update_query = """
                    UPDATE stocks 
                    SET previous_day_closing_price = :closing_price,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :stock_id
                """
                from sqlalchemy import text
                session.execute(
                    text(update_query), 
                    {'closing_price': closing_data['closing_price'], 'stock_id': stock_id}
                )
                
            logger.info(f"Updated closing price for {symbol}: ${closing_data['closing_price']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update closing price for {symbol}: {str(e)}")
            return False
    
    def insert_or_update_daily_data(self, stock_id: int, symbol: str, closing_data: Dict[str, float]) -> bool:
        """Insert or update today's complete daily data."""
        try:
            today = datetime.now(self.market_timezone).date()
            
            with db.get_session() as session:
                from sqlalchemy import text
                
                # Check if today's data already exists
                check_query = """
                    SELECT id FROM daily 
                    WHERE stock_id = :stock_id AND date = :date
                """
                result = session.execute(text(check_query), {'stock_id': stock_id, 'date': today})
                existing = result.fetchone()
                
                if existing:
                    # Update existing record with closing data
                    update_query = """
                        UPDATE daily 
                        SET closing_price = :closing_price,
                            max_price = :high_price,
                            min_price = :low_price,
                            volume = :volume,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE stock_id = :stock_id AND date = :date
                    """
                    session.execute(text(update_query), {
                        'closing_price': closing_data['closing_price'],
                        'high_price': closing_data['high_price'],
                        'low_price': closing_data['low_price'],
                        'volume': closing_data['volume'],
                        'stock_id': stock_id,
                        'date': today
                    })
                    logger.debug(f"Updated daily closing data for {symbol}")
                else:
                    # Insert new daily record with closing data
                    insert_query = """
                        INSERT INTO daily (
                            stock_id, symbol, date, closing_price, 
                            max_price, min_price, volume
                        ) VALUES (
                            :stock_id, :symbol, :date, :closing_price,
                            :high_price, :low_price, :volume
                        )
                    """
                    session.execute(text(insert_query), {
                        'stock_id': stock_id,
                        'symbol': symbol,
                        'date': today,
                        'closing_price': closing_data['closing_price'],
                        'high_price': closing_data['high_price'],
                        'low_price': closing_data['low_price'],
                        'volume': closing_data['volume']
                    })
                    logger.debug(f"Inserted new daily record with closing data for {symbol}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to insert/update daily data for {symbol}: {str(e)}")
            return False
    
    def update_closing_prices(self, force=False) -> Dict[str, int]:
        """Main method to update closing prices for all stocks."""
        logger.info("Starting closing price update")
        
        if not self.should_run_update(force):
            return {'skipped': True, 'reason': 'Outside update window or market closed'}
        
        # Test database connection
        if not db.test_connection():
            raise Exception("Database connection failed")
        
        stocks = self.get_stocks_to_update()
        if not stocks:
            return {'error': 'No stocks found to update'}
        
        logger.info(f"Updating closing prices for {len(stocks)} stocks")
        
        success_count = 0
        error_count = 0
        daily_updated = 0
        
        for stock in stocks:
            try:
                stock_id = stock['id']
                symbol = stock['symbol']
                
                closing_data = self.get_closing_price(symbol)
                if closing_data is None:
                    error_count += 1
                    continue
                
                # Update stocks table with closing price
                if self.update_closing_price(stock_id, symbol):
                    success_count += 1
                    
                    # Also insert/update complete daily data
                    if self.insert_or_update_daily_data(stock_id, symbol, closing_data):
                        daily_updated += 1
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
            'daily_records': daily_updated,
            'total_processed': len(stocks)
        }
        
        logger.info(f"Closing price update completed: {result}")
        return result