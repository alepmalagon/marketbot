"""
EVERef Market Data client for fetching market orders from EVERef's market order snapshots.

This module provides a client for loading and processing market order data from
locally downloaded EVERef market order snapshots, which can significantly speed up
market data retrieval compared to using the ESI API directly.
"""
import os
import csv
import logging
import gzip
import bz2
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
    """Client for fetching market data from locally downloaded EVERef market order snapshots."""
    
    def __init__(self, data_dir="everef_data"):
        """
        Initialize the EVERef Market client.
        
        Args:
            data_dir: Directory where downloaded market data is stored
        """
        self.data_dir = data_dir
        self.market_orders_dir = os.path.join(data_dir, "market_orders")
        self.market_history_dir = os.path.join(data_dir, "market_history")
        
        # Cache for market orders by region and type
        self.market_orders_cache = None
        self.last_update_time = None
        self.cache_duration = timedelta(minutes=30)  # Cache duration in minutes
        
        # Check if data directories exist
        if not os.path.exists(self.market_orders_dir):
            logger.warning(f"Market orders directory not found: {self.market_orders_dir}")
            logger.warning("Please run everef_market_data_downloader.py to download market data")
        
        if not os.path.exists(self.market_history_dir):
            logger.warning(f"Market history directory not found: {self.market_history_dir}")
            logger.warning("Please run everef_market_data_downloader.py to download market data")
    
    def _get_latest_market_orders_file(self) -> Optional[str]:
        """
        Get the path to the latest processed market orders file.
        
        Returns:
            Path to the latest processed market orders file, or None if not found
        """
        if not os.path.exists(self.market_orders_dir):
            logger.error(f"Market orders directory not found: {self.market_orders_dir}")
            return None
        
        # Get all processed market orders files
        processed_files = [
            os.path.join(self.market_orders_dir, f)
            for f in os.listdir(self.market_orders_dir)
            if f.endswith('_processed.csv')
        ]
        
        if not processed_files:
            logger.error("No processed market orders files found")
            return None
        
        # Sort by modification time (newest first)
        processed_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
        
        return processed_files[0]
    
    def _load_market_orders_from_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Load market orders from a processed CSV file.
        
        Args:
            file_path: Path to the processed market orders file
            
        Returns:
            DataFrame containing the market orders, or None if loading failed
        """
        try:
            logger.info(f"Loading market orders from {file_path}")
            
            # Read the CSV into a pandas DataFrame
            df = pd.read_csv(file_path)
            
            logger.info(f"Loaded {len(df)} market orders from file")
            return df
        
        except Exception as e:
            logger.error(f"Error loading market orders from file: {e}")
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
        if (self.market_orders_cache is None or 
            self.last_update_time is None or 
            current_time - self.last_update_time > self.cache_duration):
            
            # Get the latest processed market orders file
            file_path = self._get_latest_market_orders_file()
            if not file_path:
                logger.error("Failed to get latest market orders file")
                return []
            
            # Load the market orders from the file
            df = self._load_market_orders_from_file(file_path)
            if df is None:
                logger.error("Failed to load market orders from file")
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