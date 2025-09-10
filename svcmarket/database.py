"""
Database connection and utilities for svcmarket service.
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Database:
    """Database connection manager."""
    
    def __init__(self):
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '3306')
        self.db_name = os.getenv('DB_NAME', 'stan')
        self.db_user = os.getenv('DB_USER', 'stan')
        self.db_password = os.getenv('DB_PASSWORD', 'stan123')
        
        # Create connection string
        self.connection_string = (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
        
        # Create engine
        self.engine = create_engine(
            self.connection_string,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False  # Set to True for SQL debugging
        )
        
        # Create session factory
        self.Session = sessionmaker(bind=self.engine)
        
        logger.info(f"Database connection configured for {self.db_host}:{self.db_port}/{self.db_name}")
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions."""
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def test_connection(self):
        """Test database connection."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone() is not None
        except SQLAlchemyError as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False
    
    def execute_query(self, query, params=None):
        """Execute a raw SQL query."""
        try:
            with self.get_session() as session:
                result = session.execute(text(query), params or {})
                return result.fetchall()
        except SQLAlchemyError as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def get_stock_by_symbol(self, symbol):
        """Get stock information by symbol."""
        query = "SELECT * FROM stocks WHERE symbol = :symbol"
        result = self.execute_query(query, {'symbol': symbol})
        return result[0] if result else None
    
    def insert_or_update_stock(self, stock_data):
        """Insert or update stock in the stocks table."""
        try:
            with self.get_session() as session:
                # Check if stock exists
                existing = session.execute(
                    text("SELECT id FROM stocks WHERE symbol = :symbol"),
                    {'symbol': stock_data['symbol']}
                ).fetchone()
                
                if existing:
                    # Update existing stock
                    update_query = """
                        UPDATE stocks SET 
                            avg_daily_volume = :avg_daily_volume,
                            avg_daily_min_price = :avg_daily_min_price,
                            avg_daily_max_price = :avg_daily_max_price,
                            beginning_of_year_price = :beginning_of_year_price,
                            previous_day_opening_price = :previous_day_opening_price,
                            previous_day_closing_price = :previous_day_closing_price,
                            exchange = :exchange,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE symbol = :symbol
                    """
                    session.execute(text(update_query), stock_data)
                    logger.info(f"Updated stock: {stock_data['symbol']}")
                    return existing[0]
                else:
                    # Insert new stock
                    insert_query = """
                        INSERT INTO stocks (
                            symbol, avg_daily_volume, avg_daily_min_price,
                            avg_daily_max_price, beginning_of_year_price,
                            previous_day_opening_price, previous_day_closing_price,
                            exchange
                        ) VALUES (
                            :symbol, :avg_daily_volume, :avg_daily_min_price,
                            :avg_daily_max_price, :beginning_of_year_price,
                            :previous_day_opening_price, :previous_day_closing_price,
                            :exchange
                        )
                    """
                    result = session.execute(text(insert_query), stock_data)
                    logger.info(f"Inserted new stock: {stock_data['symbol']}")
                    return result.lastrowid
                    
        except SQLAlchemyError as e:
            logger.error(f"Failed to insert/update stock {stock_data['symbol']}: {str(e)}")
            raise

# Global database instance
db = Database()