"""
EVERef Market Data client for fetching market orders from a local SQLite database
populated by everef_market_data_downloader.py.
"""
import os
import sqlite3 # Use SQLite instead of pandas/bz2
import logging
from datetime import datetime, timedelta # Keep datetime if needed for other logic, but cache is removed
from typing import Dict, List, Optional, Any, Set # Keep typing

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Constants ---
# Define column names to map tuple results to dictionary keys easily
# Ensure these match the column names in the SQLite table ('market_orders')
ORDER_COLUMNS = [
    'order_id', 'type_id', 'location_id', 'volume_total', 'volume_remain',
    'min_volume', 'price', 'is_buy_order', 'duration', 'issued', 'range',
    'system_id', 'region_id'
]


class EVERefMarketClient:
    """Client for fetching market data from a local EVERef SQLite database."""

    def __init__(self, data_dir="everef_data"):
        """
        Initialize the EVERef Market client.

        Args:
            data_dir: Directory where the market data database is stored.
        """
        self.data_dir = data_dir
        self.market_orders_dir = os.path.join(data_dir, "market_orders")
        self.db_path = os.path.join(self.market_orders_dir, "market_orders.db") # Path to the SQLite DB

        # Remove pandas cache logic
        # self.market_orders_cache = None
        # self.last_update_time = None
        # self.cache_duration = timedelta(minutes=30)

        # Check if the database file exists
        if not os.path.exists(self.db_path):
            logger.error(f"Market orders database not found: {self.db_path}")
            logger.error("Please run everef_market_data_downloader.py to download and process market data into the database.")
            # Consider raising an exception here or handling it in methods that need the DB
            # raise FileNotFoundError(f"Database not found at {self.db_path}")


    # Removed _get_latest_market_orders_file and _load_market_orders_from_file
    # Removed _filter_orders_by_region_and_type and _filter_sell_orders (handled by SQL)

    def _convert_db_row_to_esi_format(self, row: tuple) -> Optional[Dict]:
        """
        Convert a database row (tuple) to the ESI API dictionary format.

        Args:
            row: A tuple representing a row fetched from the 'market_orders' table.

        Returns:
            A dictionary in ESI API format, or None if conversion fails.
        """
        if not row or len(row) != len(ORDER_COLUMNS):
            logger.warning(f"Skipping invalid database row: {row}")
            return None
        try:
            order_dict = dict(zip(ORDER_COLUMNS, row))

            # Type conversions to match ESI format
            order = {
                'order_id': int(order_dict['order_id']),
                'type_id': int(order_dict['type_id']),
                'location_id': int(order_dict['location_id']),
                'volume_total': int(order_dict['volume_total']),
                'volume_remain': int(order_dict['volume_remain']),
                'min_volume': int(order_dict['min_volume']),
                'price': float(order_dict['price']),
                 # SQLite stores BOOLEAN as 0 or 1
                'is_buy_order': bool(order_dict['is_buy_order']),
                'duration': int(order_dict['duration']),
                'issued': order_dict['issued'], # Assumes stored as TEXT ISO format
                'range': order_dict['range'],
                'system_id': int(order_dict['system_id']),
                'region_id': int(order_dict['region_id'])
            }
            return order
        except (TypeError, ValueError, KeyError) as e:
            logger.error(f"Error converting database row to ESI format: {e} - Row: {row}")
            return None


    def get_market_orders(self, region_ids: Optional[List[int]] = None, type_ids: Optional[List[int]] = None, order_type: str = 'sell') -> List[Dict]:
        """
        Get market orders from the SQLite database, filtered by region, type, and order type.

        Args:
            region_ids: Optional list of region IDs to filter by.
            type_ids: Optional list of type IDs to filter by.
            order_type: Order type to filter by ('buy' or 'sell', default 'sell').

        Returns:
            List of market orders in ESI API format.
        """
        if not os.path.exists(self.db_path):
             logger.error(f"Database not found at {self.db_path}. Cannot fetch orders.")
             return []

        conn = None
        orders = []
        try:
            conn = sqlite3.connect(self.db_path)
            # Set row_factory for easier column access if needed, but tuple is fine for zip
            # conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build the SQL query dynamically and safely
            query = f"SELECT {', '.join(ORDER_COLUMNS)} FROM market_orders WHERE"
            conditions = []
            params = []

            # Filter by order type
            if order_type == 'sell':
                conditions.append("is_buy_order = ?")
                params.append(0) # False
            elif order_type == 'buy':
                conditions.append("is_buy_order = ?")
                params.append(1) # True
            else:
                 logger.warning(f"Invalid order_type '{order_type}'. Defaulting to 'sell'.")
                 conditions.append("is_buy_order = ?")
                 params.append(0) # False


            # Filter by region IDs (if provided)
            if region_ids:
                if len(region_ids) == 1:
                    conditions.append("region_id = ?")
                    params.append(region_ids[0])
                else:
                    placeholders = ', '.join('?' * len(region_ids))
                    conditions.append(f"region_id IN ({placeholders})")
                    params.extend(region_ids)

            # Filter by type IDs (if provided)
            if type_ids:
                if len(type_ids) == 1:
                    conditions.append("type_id = ?")
                    params.append(type_ids[0])
                else:
                    placeholders = ', '.join('?' * len(type_ids))
                    conditions.append(f"type_id IN ({placeholders})")
                    params.extend(type_ids)

            # Combine conditions
            if conditions:
                query += " " + " AND ".join(conditions)
            else:
                # Handle case with no filters (fetch all) - potentially very large!
                # Remove the initial "WHERE" if no conditions were added
                query = query.replace(" WHERE", "")
                logger.warning("Fetching all market orders without filters. This might be slow and memory-intensive.")


            logger.debug(f"Executing SQL query: {query} with params: {params}")
            cursor.execute(query, params)

            # Fetch and convert results
            # Use fetchmany or iterate cursor for very large results to save memory
            logger.info("Fetching results from database...")
            fetched_count = 0
            while True:
                rows = cursor.fetchmany(10000) # Process in chunks
                if not rows:
                    break
                for row in rows:
                    esi_order = self._convert_db_row_to_esi_format(row)
                    if esi_order:
                        orders.append(esi_order)
                fetched_count += len(rows)
                # logger.debug(f"Fetched {fetched_count} rows so far...")


            logger.info(f"Retrieved {len(orders)} matching market orders from the database.")

        except sqlite3.Error as e:
            logger.error(f"SQLite error executing query: {e}")
        finally:
            if conn:
                conn.close()
                # logger.debug("SQLite connection closed.")

        return orders

    def get_market_orders_for_multiple_types(self, region_ids: List[int], type_ids: List[int], order_type: str = 'sell') -> Dict[int, List[Dict]]:
        """
        Get market orders for multiple types, organized by type ID, using the database.

        Args:
            region_ids: List of region IDs to filter by.
            type_ids: List of type IDs to get orders for.
            order_type: Order type to filter by ('buy' or 'sell').

        Returns:
            Dictionary mapping type IDs to lists of market orders.
        """
        orders_by_type = {type_id: [] for type_id in type_ids} # Initialize dict

        # Get all relevant orders in one query
        all_orders = self.get_market_orders(region_ids, type_ids, order_type)

        # Organize orders by type ID
        for order in all_orders:
            type_id = order['type_id']
            # Should already be filtered by type_ids, but check just in case
            if type_id in orders_by_type:
                orders_by_type[type_id].append(order)
            else:
                 # This case should ideally not happen if get_market_orders filters correctly
                 logger.warning(f"Order found for unexpected type_id {type_id}. Adding to dict.")
                 orders_by_type[type_id] = [order]


        logger.info(f"Organized orders for {len(orders_by_type)} types.")
        return orders_by_type

    def get_lowest_sell_prices_by_system(self, region_ids: List[int], type_ids: List[int]) -> Dict[int, Dict[int, float]]:
        """
        Get the lowest sell prices for each type in each system using an efficient SQL query.

        Args:
            region_ids: List of region IDs to filter by.
            type_ids: List of type IDs to get prices for.

        Returns:
            Dictionary mapping type IDs to dictionaries mapping system IDs to lowest prices.
            Example: {type_id: {system_id: lowest_price, ...}, ...}
        """
        if not os.path.exists(self.db_path):
             logger.error(f"Database not found at {self.db_path}. Cannot fetch prices.")
             return {}

        conn = None
        lowest_prices = {type_id: {} for type_id in type_ids} # Initialize dict

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build the SQL query using GROUP BY and MIN()
            query = """
                SELECT type_id, system_id, MIN(price) as min_price
                FROM market_orders
                WHERE is_buy_order = 0 -- Sell orders only
            """
            params = []

            # Add region ID filtering
            if region_ids:
                if len(region_ids) == 1:
                    query += " AND region_id = ?"
                    params.append(region_ids[0])
                else:
                    placeholders = ', '.join('?' * len(region_ids))
                    query += f" AND region_id IN ({placeholders})"
                    params.extend(region_ids)

            # Add type ID filtering
            if type_ids:
                if len(type_ids) == 1:
                    query += " AND type_id = ?"
                    params.append(type_ids[0])
                else:
                    placeholders = ', '.join('?' * len(type_ids))
                    query += f" AND type_id IN ({placeholders})"
                    params.extend(type_ids)

            query += " GROUP BY type_id, system_id" # Group to find the minimum per type/system

            logger.debug(f"Executing SQL query for lowest prices: {query} with params: {params}")
            cursor.execute(query, params)

            # Fetch results and populate the dictionary
            for row in cursor.fetchall():
                type_id, system_id, min_price = row
                if type_id in lowest_prices: # Ensure type_id is one we asked for
                    lowest_prices[type_id][system_id] = float(min_price) # Store price
                else:
                    # Should not happen if type_id filter is correct, but handle defensively
                     logger.warning(f"Found lowest price for unexpected type_id {type_id}. Adding to dict.")
                     lowest_prices[type_id] = {system_id: float(min_price)}


            logger.info(f"Retrieved lowest sell prices for {len(lowest_prices)} types across systems.")

        except sqlite3.Error as e:
            logger.error(f"SQLite error getting lowest prices: {e}")
        finally:
            if conn:
                conn.close()
                # logger.debug("SQLite connection closed.")

        return lowest_prices