#!/usr/bin/env python3
"""
Stock Market Data Service (svcmarket)
Main script that runs multiple subtasks for stock data management.
"""

import os
import sys
import logging
import schedule
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import task modules
from tasks.stock_updater import StockUpdater
from tasks.opening_price_updater import OpeningPriceUpdater
from tasks.closing_price_updater import ClosingPriceUpdater
from tasks.intraday_tracker import IntradayTracker

class StockMarketService:
    """Main service class that orchestrates all stock market data tasks."""
    
    def __init__(self):
        self.setup_logging()
        self.stock_updater = StockUpdater()
        self.opening_price_updater = OpeningPriceUpdater()
        self.closing_price_updater = ClosingPriceUpdater()
        self.intraday_tracker = IntradayTracker()
        
    def setup_logging(self):
        """Configure logging for the service."""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_file = os.getenv('LOG_FILE', 'svcmarket.log')
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Stock Market Service initialized")
    
    def schedule_tasks(self):
        """Schedule all recurring tasks."""
        # Task 1: Daily stock table updates - runs once per day at 9:00 AM EST
        schedule.every().day.at("09:00").do(self.run_task_1)
        
        # Task 2: Opening price updates - runs at 9:35 AM EST (5 min after NASDAQ open)
        schedule.every().day.at("09:35").do(self.run_task_2)
        
        # Task 3: Closing price updates - runs at 4:05 PM EST (5 min after market close)
        schedule.every().day.at("16:05").do(self.run_task_3)
        
        # Task 4: Intraday tracking - runs every minute, but only tracks every 15 minutes during market hours
        schedule.every().minute.do(self.run_task_4)
        
        self.logger.info("All tasks scheduled")
    
    def run_task_1(self):
        """Task 1: Daily stock table updates."""
        try:
            self.logger.info("Starting Task 1: Daily stock table updates")
            result = self.stock_updater.update_stocks_table()
            self.logger.info(f"Task 1 completed: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Task 1 failed: {str(e)}")
            raise
    
    def run_task_2(self, force=False):
        """Task 2: Opening price updates."""
        try:
            self.logger.info("Starting Task 2: Opening price updates")
            result = self.opening_price_updater.update_opening_prices(force)
            self.logger.info(f"Task 2 completed: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Task 2 failed: {str(e)}")
            raise
    
    def run_task_3(self, force=False):
        """Task 3: Closing price updates."""
        try:
            self.logger.info("Starting Task 3: Closing price updates")
            result = self.closing_price_updater.update_closing_prices(force)
            self.logger.info(f"Task 3 completed: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Task 3 failed: {str(e)}")
            raise
    
    def run_task_4(self, force=False):
        """Task 4: Intraday price tracking."""
        try:
            result = self.intraday_tracker.track_intraday_prices(force)
            
            # Only log if actually processed (not skipped)
            if not result.get('skipped', False):
                self.logger.info(f"Task 4 completed: {result}")
            
            return result
        except Exception as e:
            self.logger.error(f"Task 4 failed: {str(e)}")
            raise
    
    def run_manual_task(self, task_number):
        """Run a specific task manually."""
        if task_number == 1:
            return self.run_task_1()
        elif task_number == 2:
            return self.run_task_2(force=True)  # Force run for manual testing
        elif task_number == 3:
            return self.run_task_3(force=True)  # Force run for manual testing
        elif task_number == 4:
            return self.run_task_4(force=True)  # Force run for manual testing
        else:
            self.logger.error(f"Unknown task number: {task_number}")
            return False
    
    def run_scheduler(self):
        """Main scheduler loop."""
        self.logger.info("Starting scheduler...")
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run(self):
        """Main entry point."""
        if len(sys.argv) > 1:
            # Manual task execution
            try:
                task_num = int(sys.argv[1])
                self.logger.info(f"Running task {task_num} manually")
                result = self.run_manual_task(task_num)
                sys.exit(0 if result else 1)
            except ValueError:
                self.logger.error("Invalid task number provided")
                sys.exit(1)
        else:
            # Schedule and run continuously
            self.schedule_tasks()
            self.run_scheduler()

if __name__ == "__main__":
    service = StockMarketService()
    service.run()