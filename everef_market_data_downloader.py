#!/usr/bin/env python3
"""
EVERef Market Data Downloader

This script downloads market order data from EVERef's market order snapshots,
processes it, and loads it into an SQLite database.
It's designed to be run manually to create a local database of market data.
"""
import os
import sys
import logging
import argparse
import requests
import bz2
import pandas as pd
import sqlite3 # Added for SQLite functionality
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EVERefMarketDataDownloader:
    """Downloader for EVERef market data snapshots."""

    def __init__(self, data_dir="everef_data"):
        """
        Initialize the EVERef Market Data Downloader.

        Args:
            data_dir: Directory to store downloaded market data
        """
        self.market_orders_url = "https://data.everef.net/market-orders/market-orders-latest.v3.csv.bz2"
        self.data_dir = data_dir
        self.market_orders_dir = os.path.join(data_dir, "market_orders") # Added for clarity
        self.db_path = os.path.join(self.market_orders_dir, "market_orders.db") # Added SQLite DB path

        # Create data directory if it doesn't exist
        os.makedirs(self.market_orders_dir, exist_ok=True) # Updated to use market_orders_dir

    def download_market_orders(self) -> Optional[str]:
        """
        Download the latest market orders snapshot.

        Returns:
            Path to the downloaded file, or None if download failed
        """
        try:
            logger.info(f"Downloading market orders snapshot from {self.market_orders_url}")

            # Extract filename from URL
            filename = "market-orders-latest.v3.csv.bz2"
            file_path = os.path.join(self.market_orders_dir, filename) # Updated path

            # Check if we already have this snapshot and it's less than 1 hour old
            if os.path.exists(file_path):
                file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_age < timedelta(hours=1):
                    logger.info(f"Using cached market orders snapshot: {file_path} (age: {file_age})")
                    return file_path
                else:
                    logger.info(f"Cached snapshot is {file_age} old, downloading fresh data")

            # Download the snapshot
            response = requests.get(self.market_orders_url, stream=True)
            response.raise_for_status()

            # Save the snapshot to the data directory
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"Downloaded market orders snapshot to {file_path}")
            return file_path

        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading market orders snapshot: {e}")
            return None

    def process_and_load_to_db(self, file_path: str) -> bool:
        """
        Process a market orders snapshot (CSV.bz2) and load it into the SQLite database.

        Args:
            file_path: Path to the downloaded snapshot file (csv.bz2)

        Returns:
            True if processing and loading were successful, False otherwise.
        """
        try:
            logger.info(f"Processing market orders snapshot from {file_path}")

            # Check if the database needs updating (source file is newer than DB)
            if os.path.exists(self.db_path):
                 source_mtime = os.path.getmtime(file_path)
                 db_mtime = os.path.getmtime(self.db_path)
                 if db_mtime >= source_mtime:
                     logger.info(f"SQLite database {self.db_path} is already up-to-date.")
                     return True


            # Open the bz2 compressed CSV file
            with bz2.open(file_path, 'rt', encoding='utf-8') as f:
                # Read the CSV into a pandas DataFrame
                logger.info("Reading bz2 compressed CSV file (this may take a moment)...")
                # --- Corrected dtypes using pandas nullable types ---
                dtypes = {
                    'order_id': pd.Int64Dtype(),    # Use nullable Int64
                    'type_id': pd.Int32Dtype(),     # Use nullable Int32
                    'location_id': pd.Int64Dtype(), # Use nullable Int64
                    'volume_total': pd.Int64Dtype(),# Use nullable Int64
                    'volume_remain': pd.Int64Dtype(),# Use nullable Int64
                    'min_volume': pd.Int32Dtype(),  # Use nullable Int32
                    'price': 'float64',             # Float can handle NaN
                    'is_buy_order': 'boolean',      # Pandas boolean handles NA
                    'duration': pd.Int32Dtype(),    # Use nullable Int32 (Fixes the error)
                    # 'issued' will be parsed by parse_dates
                    'range': 'string',              # Pandas string handles NA
                    'system_id': pd.Int32Dtype(),   # Use nullable Int32
                    'region_id': pd.Int32Dtype()    # Use nullable Int32
                 }
                df = pd.read_csv(f, dtype=dtypes, parse_dates=['issued'])
                # ----------------------------------------------------

            logger.info(f"Loaded {len(df)} market orders from snapshot")

            # --- Load data into SQLite Database ---
            logger.info(f"Connecting to SQLite database: {self.db_path}")
            conn = None # Initialize conn to None
            try:
                conn = sqlite3.connect(self.db_path)
                logger.info(f"Writing {len(df)} records to 'market_orders' table (replacing existing)...")
                # Pandas NA values will be correctly written as NULL to SQLite
                df.to_sql('market_orders', conn, if_exists='replace', index=False, chunksize=100000)
                logger.info("Data successfully written to 'market_orders' table.")

                # --- Add Indexes for faster queries ---
                logger.info("Creating indexes on 'market_orders' table...")
                cursor = conn.cursor()
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_region_type_buy ON market_orders (region_id, type_id, is_buy_order)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_type_system ON market_orders (type_id, system_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_location_id ON market_orders (location_id)")
                conn.commit()
                logger.info("Indexes created successfully.")

                return True

            except sqlite3.Error as e:
                 logger.error(f"SQLite error during data loading or index creation: {e}")
                 if conn:
                     conn.rollback() # Rollback changes on error
                 return False
            finally:
                 if conn:
                     conn.close()
                     logger.info("SQLite database connection closed.")
            # --- End SQLite ---

        except pd.errors.EmptyDataError:
            logger.error(f"Error processing market orders: The file {file_path} is empty or corrupted.")
            return False
        except Exception as e:
            # Log the full traceback for better debugging
            logger.exception(f"Error processing market orders snapshot: {e}")
            return False


def main():
    """Parse command line arguments and run the downloader."""
    parser = argparse.ArgumentParser(description="EVERef Market Data Downloader & SQLite Loader")

    # Add command line arguments
    parser.add_argument(
        "--data-dir",
        type=str,
        default="everef_data",
        help="Directory to store downloaded market data and database (default: everef_data)"
    )

    # Parse arguments
    args = parser.parse_args()

    # Create the downloader
    downloader = EVERefMarketDataDownloader(data_dir=args.data_dir)

    # Download market orders
    logger.info("Downloading market orders data...")
    orders_file_bz2 = downloader.download_market_orders()

    if orders_file_bz2:
        # Process and load data into SQLite
        logger.info(f"Processing {orders_file_bz2} and loading into SQLite...")
        success = downloader.process_and_load_to_db(orders_file_bz2)
        if success:
            logger.info(f"Market orders data successfully processed and loaded into: {downloader.db_path}")
        else:
            logger.error("Failed to process market orders data and load into SQLite.")
    else:
        logger.error("Failed to download market orders data.")

    logger.info("EVERef Market Data Downloader script completed.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Downloader stopped by user")
        sys.exit(0)