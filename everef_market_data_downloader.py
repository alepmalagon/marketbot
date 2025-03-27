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
import gzip
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
        self.market_orders_base_url = "https://data.everef.net/market-orders"
        self.market_history_base_url = "https://data.everef.net/market-history"
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, "market_orders"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "market_history"), exist_ok=True)
    
    def _get_latest_market_orders_url(self) -> Optional[str]:
        """
        Get the URL of the latest market order snapshot.
        
        Returns:
            URL of the latest snapshot, or None if not found
        """
        try:
            # Get the directory listing
            response = requests.get(self.market_orders_base_url)
            response.raise_for_status()
            
            # Parse the HTML to find the latest snapshot
            lines = response.text.split('\n')
            snapshots = []
            
            for line in lines:
                if 'href="' in line and '.csv.gz"' in line:
                    # Extract the snapshot filename
                    start = line.find('href="') + 6
                    end = line.find('"', start)
                    filename = line[start:end]
                    
                    if filename.endswith('.csv.gz'):
                        snapshots.append(filename)
            
            if snapshots:
                # Sort snapshots by name (which should be by date)
                snapshots.sort(reverse=True)
                return f"{self.market_orders_base_url}/{snapshots[0]}"
            
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting latest market orders snapshot URL: {e}")
            return None
    
    def _get_latest_market_history_url(self) -> Optional[str]:
        """
        Get the URL of the latest market history snapshot.
        
        Returns:
            URL of the latest snapshot, or None if not found
        """
        try:
            # Get the current year
            current_year = datetime.now().year
            
            # Get the directory listing for the current year
            year_url = f"{self.market_history_base_url}/{current_year}"
            response = requests.get(year_url)
            response.raise_for_status()
            
            # Parse the HTML to find the latest snapshot
            lines = response.text.split('\n')
            snapshots = []
            
            for line in lines:
                if 'href="' in line and '.csv.bz2"' in line:
                    # Extract the snapshot filename
                    start = line.find('href="') + 6
                    end = line.find('"', start)
                    filename = line[start:end]
                    
                    if filename.endswith('.csv.bz2'):
                        snapshots.append(filename)
            
            if snapshots:
                # Sort snapshots by name (which should be by date)
                snapshots.sort(reverse=True)
                return f"{year_url}/{snapshots[0]}"
            
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting latest market history snapshot URL: {e}")
            return None
    
    def download_market_orders(self) -> Optional[str]:
        """
        Download the latest market orders snapshot.
        
        Returns:
            Path to the downloaded file, or None if download failed
        """
        # Get the latest snapshot URL
        url = self._get_latest_market_orders_url()
        if not url:
            logger.error("Failed to get latest market orders snapshot URL")
            return None
        
        try:
            logger.info(f"Downloading market orders snapshot from {url}")
            
            # Extract filename from URL
            filename = url.split('/')[-1]
            file_path = os.path.join(self.data_dir, "market_orders", filename)
            
            # Check if we already have this snapshot
            if os.path.exists(file_path):
                logger.info(f"Using cached market orders snapshot: {file_path}")
                return file_path
            
            # Download the snapshot
            response = requests.get(url, stream=True)
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
    
    def download_market_history(self) -> Optional[str]:
        """
        Download the latest market history snapshot.
        
        Returns:
            Path to the downloaded file, or None if download failed
        """
        # Get the latest snapshot URL
        url = self._get_latest_market_history_url()
        if not url:
            logger.error("Failed to get latest market history snapshot URL")
            return None
        
        try:
            logger.info(f"Downloading market history snapshot from {url}")
            
            # Extract filename from URL
            filename = url.split('/')[-1]
            file_path = os.path.join(self.data_dir, "market_history", filename)
            
            # Check if we already have this snapshot
            if os.path.exists(file_path):
                logger.info(f"Using cached market history snapshot: {file_path}")
                return file_path
            
            # Download the snapshot
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save the snapshot to the data directory
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded market history snapshot to {file_path}")
            return file_path
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading market history snapshot: {e}")
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
            base_filename = os.path.basename(file_path).replace('.csv.gz', '')
            processed_file_path = os.path.join(self.data_dir, "market_orders", f"{base_filename}_processed.csv")
            
            # Check if we already have the processed file
            if os.path.exists(processed_file_path):
                logger.info(f"Using cached processed market orders: {processed_file_path}")
                return processed_file_path
            
            # Open the gzipped CSV file
            with gzip.open(file_path, 'rt') as f:
                # Read the CSV into a pandas DataFrame
                df = pd.read_csv(f)
            
            logger.info(f"Loaded {len(df)} market orders from snapshot")
            
            # Save the processed DataFrame to a CSV file
            df.to_csv(processed_file_path, index=False)
            
            logger.info(f"Saved processed market orders to {processed_file_path}")
            return processed_file_path
        
        except Exception as e:
            logger.error(f"Error processing market orders snapshot: {e}")
            return None
    
    def process_market_history(self, file_path: str) -> Optional[str]:
        """
        Process a market history snapshot and save it as a CSV file.
        
        Args:
            file_path: Path to the downloaded snapshot file
            
        Returns:
            Path to the processed CSV file, or None if processing failed
        """
        try:
            logger.info(f"Processing market history snapshot from {file_path}")
            
            # Extract the base filename without extension
            base_filename = os.path.basename(file_path).replace('.csv.bz2', '')
            processed_file_path = os.path.join(self.data_dir, "market_history", f"{base_filename}_processed.csv")
            
            # Check if we already have the processed file
            if os.path.exists(processed_file_path):
                logger.info(f"Using cached processed market history: {processed_file_path}")
                return processed_file_path
            
            # Open the bz2 compressed CSV file
            with bz2.open(file_path, 'rt') as f:
                # Read the CSV into a pandas DataFrame
                df = pd.read_csv(f)
            
            logger.info(f"Loaded {len(df)} market history records from snapshot")
            
            # Save the processed DataFrame to a CSV file
            df.to_csv(processed_file_path, index=False)
            
            logger.info(f"Saved processed market history to {processed_file_path}")
            return processed_file_path
        
        except Exception as e:
            logger.error(f"Error processing market history snapshot: {e}")
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
    
    parser.add_argument(
        "--orders-only",
        action="store_true",
        help="Download only market orders data (not history)"
    )
    
    parser.add_argument(
        "--history-only",
        action="store_true",
        help="Download only market history data (not orders)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create the downloader
    downloader = EVERefMarketDataDownloader(data_dir=args.data_dir)
    
    # Download and process market orders
    if not args.history_only:
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
    
    # Download and process market history
    if not args.orders_only:
        logger.info("Downloading and processing market history data...")
        history_file = downloader.download_market_history()
        if history_file:
            processed_history_file = downloader.process_market_history(history_file)
            if processed_history_file:
                logger.info(f"Market history data ready at: {processed_history_file}")
            else:
                logger.error("Failed to process market history data")
        else:
            logger.error("Failed to download market history data")
    
    logger.info("EVERef Market Data Downloader completed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Downloader stopped by user")
        sys.exit(0)