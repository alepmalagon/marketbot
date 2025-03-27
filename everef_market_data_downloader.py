#!/usr/bin/env python3
"""
EVERef Market Data Downloader

This script downloads and processes market order data from EVERef's market order snapshots.
It's designed to be run manually to create a local cache of market data for faster processing.
"""
import os
import sys
import logging
import argparse
import requests
import bz2
import pandas as pd
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
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "market_orders"), exist_ok=True)
    
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
            file_path = os.path.join(self.data_dir, "market_orders", filename)
            
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
    
    def process_market_orders(self, file_path: str) -> Optional[str]:
        """
        Process a market orders snapshot and save it as a CSV file.
        
        Args:
            file_path: Path to the downloaded snapshot file
            
        Returns:
            Path to the processed CSV file, or None if processing failed
        """
        try:
            logger.info(f"Processing market orders snapshot from {file_path}")
            
            # Extract the base filename without extension
            base_filename = os.path.basename(file_path).replace('.csv.bz2', '')
            processed_file_path = os.path.join(self.data_dir, "market_orders", f"{base_filename}_processed.csv")
            
            # Check if we already have the processed file and it's not older than the source file
            if os.path.exists(processed_file_path):
                source_mtime = os.path.getmtime(file_path)
                processed_mtime = os.path.getmtime(processed_file_path)
                
                if processed_mtime >= source_mtime:
                    logger.info(f"Using cached processed market orders: {processed_file_path}")
                    return processed_file_path
            
            # Open the bz2 compressed CSV file
            with bz2.open(file_path, 'rt') as f:
                # Read the CSV into a pandas DataFrame
                logger.info("Reading bz2 compressed CSV file (this may take a moment)...")
                df = pd.read_csv(f)
            
            logger.info(f"Loaded {len(df)} market orders from snapshot")
            
            # Save the processed DataFrame to a CSV file
            logger.info(f"Saving processed data to {processed_file_path}...")
            df.to_csv(processed_file_path, index=False)
            
            logger.info(f"Saved processed market orders to {processed_file_path}")
            return processed_file_path
        
        except Exception as e:
            logger.error(f"Error processing market orders snapshot: {e}")
            return None

def main():
    """Parse command line arguments and run the downloader."""
    parser = argparse.ArgumentParser(description="EVERef Market Data Downloader")
    
    # Add command line arguments
    parser.add_argument(
        "--data-dir", 
        type=str,
        default="everef_data",
        help="Directory to store downloaded market data (default: everef_data)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create the downloader
    downloader = EVERefMarketDataDownloader(data_dir=args.data_dir)
    
    # Download and process market orders
    logger.info("Downloading and processing market orders data...")
    orders_file = downloader.download_market_orders()
    if orders_file:
        processed_orders_file = downloader.process_market_orders(orders_file)
        if processed_orders_file:
            logger.info(f"Market orders data ready at: {processed_orders_file}")
        else:
            logger.error("Failed to process market orders data")
    else:
        logger.error("Failed to download market orders data")
    
    logger.info("EVERef Market Data Downloader completed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Downloader stopped by user")
        sys.exit(0)