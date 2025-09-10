"""
Task 1: Daily stock table updates
Updates and maintains the stocks table with current stock information.
"""

import os
import logging
import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json

from database import db

logger = logging.getLogger(__name__)

class StockUpdater:
    """Handles daily updates to the stocks table."""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.polygon_key = os.getenv('POLYGON_API_KEY')
        
        # Common stock symbols to track (can be expanded)
        self.default_symbols = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA',
            'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'DIS',
            'NFLX', 'ADBE', 'CRM', 'BAC', 'XOM', 'KO', 'PFE',
            'INTC', 'CSCO', 'VZ', 'T', 'IBM', 'WMT', 'CVX', 'MRK'
        ]
    
    def get_nasdaq_symbols(self) -> List[str]:
        """Get list of NASDAQ symbols to track."""
        # For now, return default symbols
        # In production, you could fetch from NASDAQ API or file
        return self.default_symbols
    
    def get_stock_data_yfinance(self, symbol: str) -> Optional[Dict]:
        """Get stock data using yfinance (free alternative)."""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            history = stock.history(period="1y")
            recent_history = stock.history(period="5d")
            
            if history.empty or recent_history.empty:
                logger.warning(f"No data available for {symbol}")
                return None
            
            # Calculate year-to-date data
            year_start = datetime(datetime.now().year, 1, 1)
            ytd_history = stock.history(start=year_start)
            
            # Get previous day data
            previous_day = recent_history.iloc[-2] if len(recent_history) >= 2 else recent_history.iloc[-1]
            
            # Calculate averages
            avg_volume = int(history['Volume'].mean()) if not history['Volume'].empty else 0
            avg_low = float(history['Low'].mean()) if not history['Low'].empty else 0
            avg_high = float(history['High'].mean()) if not history['High'].empty else 0
            
            beginning_year_price = float(ytd_history['Close'].iloc[0]) if not ytd_history.empty else 0
            
            stock_data = {
                'symbol': symbol,
                'avg_daily_volume': avg_volume,
                'avg_daily_min_price': round(avg_low, 2),
                'avg_daily_max_price': round(avg_high, 2),
                'beginning_of_year_price': round(beginning_year_price, 2),
                'previous_day_opening_price': round(float(previous_day['Open']), 2),
                'previous_day_closing_price': round(float(previous_day['Close']), 2),
                'exchange': info.get('exchange', 'NASDAQ')
            }
            
            logger.debug(f"Retrieved data for {symbol}: {stock_data}")
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def get_stock_data_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """Get stock data using Alpha Vantage API."""
        if not self.alpha_vantage_key or self.alpha_vantage_key == 'your_api_key_here':
            logger.debug("Alpha Vantage API key not configured")
            return None
        
        try:
            # Get daily data
            daily_url = f"https://www.alphavantage.co/query?function=DAILY&symbol={symbol}&apikey={self.alpha_vantage_key}"
            response = requests.get(daily_url, timeout=30)
            daily_data = response.json()
            
            if 'Error Message' in daily_data:
                logger.error(f"Alpha Vantage error for {symbol}: {daily_data['Error Message']}")
                return None
            
            if 'Time Series (Daily)' not in daily_data:
                logger.warning(f"No daily data available for {symbol}")
                return None
            
            time_series = daily_data['Time Series (Daily)']
            dates = sorted(time_series.keys(), reverse=True)
            
            # Get recent data for calculations
            recent_data = []
            for date in dates[:252]:  # Approximately 1 year of trading days
                day_data = time_series[date]
                recent_data.append({
                    'date': date,
                    'open': float(day_data['1. open']),
                    'high': float(day_data['2. high']),
                    'low': float(day_data['3. low']),
                    'close': float(day_data['4. close']),
                    'volume': int(day_data['5. volume'])
                })
            
            if not recent_data:
                return None
            
            # Calculate averages
            avg_volume = sum(day['volume'] for day in recent_data) // len(recent_data)
            avg_low = sum(day['low'] for day in recent_data) / len(recent_data)
            avg_high = sum(day['high'] for day in recent_data) / len(recent_data)
            
            # Get year beginning price
            year_start = f"{datetime.now().year}-01-01"
            beginning_year_price = recent_data[-1]['close']  # Approximate
            for day in reversed(recent_data):
                if day['date'] >= year_start:
                    beginning_year_price = day['close']
                    break
            
            # Previous day data
            previous_day = recent_data[1] if len(recent_data) > 1 else recent_data[0]
            
            stock_data = {
                'symbol': symbol,
                'avg_daily_volume': avg_volume,
                'avg_daily_min_price': round(avg_low, 2),
                'avg_daily_max_price': round(avg_high, 2),
                'beginning_of_year_price': round(beginning_year_price, 2),
                'previous_day_opening_price': round(previous_day['open'], 2),
                'previous_day_closing_price': round(previous_day['close'], 2),
                'exchange': 'NASDAQ'  # Default to NASDAQ
            }
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {str(e)}")
            return None
    
    def update_stock(self, symbol: str) -> bool:
        """Update a single stock in the database."""
        logger.info(f"Updating stock data for {symbol}")
        
        # Try yfinance first (free and reliable)
        stock_data = self.get_stock_data_yfinance(symbol)
        
        # Fallback to Alpha Vantage if yfinance fails
        if not stock_data:
            stock_data = self.get_stock_data_alpha_vantage(symbol)
        
        if not stock_data:
            logger.error(f"Could not retrieve data for {symbol}")
            return False
        
        try:
            db.insert_or_update_stock(stock_data)
            logger.info(f"Successfully updated {symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to update database for {symbol}: {str(e)}")
            return False
    
    def update_stocks_table(self) -> Dict[str, int]:
        """Main method to update all stocks in the table."""
        logger.info("Starting daily stock table update")
        
        # Test database connection
        if not db.test_connection():
            raise Exception("Database connection failed")
        
        symbols = self.get_nasdaq_symbols()
        logger.info(f"Updating {len(symbols)} stocks")
        
        success_count = 0
        error_count = 0
        
        for symbol in symbols:
            try:
                if self.update_stock(symbol):
                    success_count += 1
                else:
                    error_count += 1
                    
                # Add a small delay to avoid rate limiting
                import time
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Unexpected error updating {symbol}: {str(e)}")
                error_count += 1
        
        result = {
            'success_count': success_count,
            'error_count': error_count,
            'total_processed': len(symbols)
        }
        
        logger.info(f"Stock update completed: {result}")
        return result