"""
EVERef Market Data client for fetching market orders from EVERef's market order snapshots.

This module provides a client for downloading and processing market order data from
EVERef's market order snapshots, which can significantly speed up market data retrieval
compared to using the ESI API directly.
"""
import os
import csv
import logging
import requests
import gzip
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
import pandas as pd
import io

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EVERefMarketClient:
    """Client for fetching market data from EVERef's market order snapshots."""
    
    def __init__(self, cache_dir="everef_cache"):
        """
        Initialize the EVERef Market client.
        
        Args:
            cache_dir: Directory to store downloaded market data
        """
        self.base_url = "https://data.everef.net/market-orders"
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Cache for market orders by region and type
        self.market_orders_cache = {}
        self.last_update_time = None
        self.cache_duration = timedelta(minutes=30)  # Cache duration in minutes
    
    def _get_latest_snapshot_url(self) -> Optional[str]:
        """
        Get the URL of the latest market order snapshot.
        
        Returns:
            URL of the latest snapshot, or None if not found
        """
        try:
            # Get the directory listing
            response = requests.get(self.base_url)
            response.raise_for_status()
            
            # Parse the HTML to find the latest snapshot
            # This is a simple approach - in production, you might want to use a proper HTML parser
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
                return f"{self.base_url}/{snapshots[0]}"
            
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting latest snapshot URL: {e}")
            return None
    
    def _download_snapshot(self, url: str) -> Optional[str]:
        """
        Download a market order snapshot and save it to the cache directory.
        
        Args:
            url: URL of the snapshot to download
            
        Returns:
            Path to the downloaded file, or None if download failed
        """
        try:
            logger.info(f"Downloading market order snapshot from {url}")
            
            # Extract filename from URL
            filename = url.split('/')[-1]
            cache_path = os.path.join(self.cache_dir, filename)
            
            # Check if we already have this snapshot
            if os.path.exists(cache_path):
                logger.info(f"Using cached snapshot: {cache_path}")
                return cache_path
            
            # Download the snapshot
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save the snapshot to the cache directory
            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded snapshot to {cache_path}")
            return cache_path
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading snapshot: {e}")
            return None
    
    def _load_snapshot_to_dataframe(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Load a market order snapshot into a pandas DataFrame.
        
        Args:
            file_path: Path to the snapshot file
            
        Returns:
            DataFrame containing the market orders, or None if loading failed
        """
        try:
            logger.info(f"Loading market order snapshot from {file_path}")
            
            # Open the gzipped CSV file
            with gzip.open(file_path, 'rt') as f:
                # Read the CSV into a pandas DataFrame
                df = pd.read_csv(f)
            
            logger.info(f"Loaded {len(df)} market orders from snapshot")
            return df
        
        except Exception as e:
            logger.error(f"Error loading snapshot: {e}")
            return None
    
    def _filter_orders_by_region_and_type(self, df: pd.DataFrame, region_ids: List[int], type_ids: List[int]) -> pd.DataFrame:
        """
        Filter market orders by region and type.
        
        Args:
            df: DataFrame containing market orders
            region_ids: List of region IDs to filter by
            type_ids: List of type IDs to filter by
            
        Returns:
            DataFrame containing filtered market orders
        """
        # Filter by region
        if region_ids:
            df = df[df['region_id'].isin(region_ids)]
        
        # Filter by type
        if type_ids:
            df = df[df['type_id'].isin(type_ids)]
        
        return df
    
    def _filter_sell_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter for sell orders only.
        
        Args:
            df: DataFrame containing market orders
            
        Returns:
            DataFrame containing only sell orders
        """
        return df[df['is_buy_order'] == False]
    
    def _convert_to_esi_format(self, df: pd.DataFrame) -> List[Dict]:
        """
        Convert the DataFrame to the ESI API format for compatibility.
        
        Args:
            df: DataFrame containing market orders
            
        Returns:
            List of dictionaries in ESI API format
        """
        orders = []
        
        for _, row in df.iterrows():
            order = {
                'order_id': int(row['order_id']),
                'type_id': int(row['type_id']),
                'location_id': int(row['location_id']),
                'volume_total': int(row['volume_total']),
                'volume_remain': int(row['volume_remain']),
                'min_volume': int(row['min_volume']),
                'price': float(row['price']),
                'is_buy_order': bool(row['is_buy_order']),
                'duration': int(row['duration']),
                'issued': row['issued'],
                'range': row['range'],
                'system_id': int(row['system_id']),
                'region_id': int(row['region_id'])
            }
            orders.append(order)
        
        return orders
    
    def get_market_orders(self, region_ids: List[int] = None, type_ids: List[int] = None, order_type: str = 'sell') -> List[Dict]:
        """
        Get market orders from the latest snapshot, filtered by region, type, and order type.
        
        Args:
            region_ids: List of region IDs to filter by
            type_ids: List of type IDs to filter by
            order_type: Order type to filter by ('buy' or 'sell')
            
        Returns:
            List of market orders in ESI API format
        """
        # Check if we need to update the cache
        current_time = datetime.now()
        if (self.last_update_time is None or 
            current_time - self.last_update_time > self.cache_duration or
            not self.market_orders_cache):
            
            # Get the latest snapshot URL
            url = self._get_latest_snapshot_url()
            if not url:
                logger.error("Failed to get latest snapshot URL")
                return []
            
            # Download the snapshot
            file_path = self._download_snapshot(url)
            if not file_path:
                logger.error("Failed to download snapshot")
                return []
            
            # Load the snapshot into a DataFrame
            df = self._load_snapshot_to_dataframe(file_path)
            if df is None:
                logger.error("Failed to load snapshot")
                return []
            
            # Update the cache
            self.market_orders_cache = df
            self.last_update_time = current_time
            logger.info(f"Updated market orders cache with {len(df)} orders")
        
        # Use the cached DataFrame
        df = self.market_orders_cache
        
        # Filter by region and type
        df_filtered = self._filter_orders_by_region_and_type(df, region_ids, type_ids)
        
        # Filter by order type
        if order_type == 'sell':
            df_filtered = self._filter_sell_orders(df_filtered)
        elif order_type == 'buy':
            df_filtered = df_filtered[df_filtered['is_buy_order'] == True]
        
        # Convert to ESI format
        orders = self._convert_to_esi_format(df_filtered)
        
        logger.info(f"Returning {len(orders)} {order_type} orders for {len(type_ids) if type_ids else 'all'} types in {len(region_ids) if region_ids else 'all'} regions")
        
        return orders
    
    def get_market_orders_for_multiple_types(self, region_ids: List[int], type_ids: List[int], order_type: str = 'sell') -> Dict[int, List[Dict]]:
        """
        Get market orders for multiple types, organized by type ID.
        
        Args:
            region_ids: List of region IDs to filter by
            type_ids: List of type IDs to get orders for
            order_type: Order type to filter by ('buy' or 'sell')
            
        Returns:
            Dictionary mapping type IDs to lists of market orders
        """
        orders_by_type = {}
        
        # Get all orders for the specified regions and types
        all_orders = self.get_market_orders(region_ids, type_ids, order_type)
        
        # Organize orders by type ID
        for order in all_orders:
            type_id = order['type_id']
            if type_id not in orders_by_type:
                orders_by_type[type_id] = []
            orders_by_type[type_id].append(order)
        
        return orders_by_type
    
    def get_lowest_sell_prices_by_system(self, region_ids: List[int], type_ids: List[int]) -> Dict[int, Dict[int, float]]:
        """
        Get the lowest sell prices for each type in each system.
        
        Args:
            region_ids: List of region IDs to filter by
            type_ids: List of type IDs to get prices for
            
        Returns:
            Dictionary mapping type IDs to dictionaries mapping system IDs to lowest prices
        """
        # Get all sell orders for the specified regions and types
        all_orders = self.get_market_orders(region_ids, type_ids, 'sell')
        
        # Organize orders by type and system
        lowest_prices = {}
        
        for order in all_orders:
            type_id = order['type_id']
            system_id = order['system_id']
            price = order['price']
            
            if type_id not in lowest_prices:
                lowest_prices[type_id] = {}
            
            if system_id not in lowest_prices[type_id] or price < lowest_prices[type_id][system_id]:
                lowest_prices[type_id][system_id] = price
        
        return lowest_prices