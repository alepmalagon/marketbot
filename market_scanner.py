"""
Market scanner for finding good deals on T1 battleship hulls.
"""
import logging
from typing import Dict, List, Tuple
from collections import defaultdict

from esi_client import ESIClient
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketScanner:
    """Scanner for finding good deals on T1 battleship hulls."""
    
    def __init__(self):
        """Initialize the market scanner."""
        self.esi_client = ESIClient()
        self.type_names = {}  # Cache for type names
        self.system_names = {}  # Cache for system names
        self.system_distances = {}  # Cache for system distances
    
    def get_type_name(self, type_id: int) -> str:
        """
        Get the name of a type.
        
        Args:
            type_id: The type ID to get the name for
            
        Returns:
            The name of the type
        """
        if type_id not in self.type_names:
            type_info = self.esi_client.get_type_info(type_id)
            self.type_names[type_id] = type_info.get('name', f'Unknown Type {type_id}')
        return self.type_names[type_id]
    
    def get_system_name(self, system_id: int) -> str:
        """
        Get the name of a system.
        
        Args:
            system_id: The system ID to get the name for
            
        Returns:
            The name of the system
        """
        if system_id not in self.system_names:
            system_info = self.esi_client.get_system_info(system_id)
            self.system_names[system_id] = system_info.get('name', f'Unknown System {system_id}')
        return self.system_names[system_id]
    
    def get_distance_to_sosala(self, system_id: int) -> int:
        """
        Get the distance from a system to Sosala.
        
        Args:
            system_id: The system ID to get the distance for
            
        Returns:
            The number of jumps from the system to Sosala
        """
        if system_id == config.SOSALA_SYSTEM_ID:
            return 0
        
        cache_key = (system_id, config.SOSALA_SYSTEM_ID)
        if cache_key not in self.system_distances:
            distance = self.esi_client.get_jump_distance(system_id, config.SOSALA_SYSTEM_ID)
            self.system_distances[cache_key] = distance
        
        return self.system_distances[cache_key]
    
    def fetch_battleship_orders(self) -> Dict[int, List[Dict]]:
        """
        Fetch all sell orders for T1 battleship hulls in the Lonetrek region.
        
        Returns:
            A dictionary mapping type IDs to lists of sell orders
        """
        logger.info("Fetching T1 battleship sell orders from Lonetrek region...")
        
        # Dictionary to store orders by type ID
        orders_by_type = defaultdict(list)
        
        # Fetch orders for each battleship type
        for type_id in config.T1_BATTLESHIP_TYPE_IDS:
            type_name = self.get_type_name(type_id)
            logger.info(f"Fetching orders for {type_name} (Type ID: {type_id})")
            
            # Get sell orders for this type in Lonetrek
            orders = self.esi_client.get_market_orders(
                region_id=config.LONETREK_REGION_ID,
                type_id=type_id,
                order_type='sell'
            )
            
            # Filter orders by minimum price
            filtered_orders = [
                order for order in orders
                if order.get('price', 0) >= config.MIN_PRICE
            ]
            
            # Add system names and distances to orders
            for order in filtered_orders:
                system_id = order.get('system_id')
                if system_id:
                    order['system_name'] = self.get_system_name(system_id)
                    order['distance_to_sosala'] = self.get_distance_to_sosala(system_id)
            
            # Filter orders by distance to Sosala
            nearby_orders = [
                order for order in filtered_orders
                if order.get('distance_to_sosala', 999) <= config.MAX_JUMPS
            ]
            
            if nearby_orders:
                logger.info(f"Found {len(nearby_orders)} nearby sell orders for {type_name}")
                orders_by_type[type_id].extend(nearby_orders)
            else:
                logger.info(f"No nearby sell orders found for {type_name}")
        
        return orders_by_type
    
    def fetch_jita_prices(self) -> Dict[int, float]:
        """
        Fetch the lowest sell prices for T1 battleship hulls in Jita.
        
        Returns:
            A dictionary mapping type IDs to lowest sell prices
        """
        logger.info("Fetching T1 battleship sell prices from Jita...")
        
        # Dictionary to store lowest prices by type ID
        lowest_prices = {}
        
        # Fetch orders for each battleship type
        for type_id in config.T1_BATTLESHIP_TYPE_IDS:
            type_name = self.get_type_name(type_id)
            logger.info(f"Fetching Jita prices for {type_name} (Type ID: {type_id})")
            
            # Get sell orders for this type in The Forge (Jita's region)
            orders = self.esi_client.get_market_orders(
                region_id=config.FORGE_REGION_ID,
                type_id=type_id,
                order_type='sell'
            )
            
            # Filter orders to only include those in Jita
            jita_orders = [
                order for order in orders
                if order.get('system_id') == config.JITA_SYSTEM_ID
            ]
            
            if jita_orders:
                # Find the lowest price
                lowest_price = min(order.get('price', float('inf')) for order in jita_orders)
                lowest_prices[type_id] = lowest_price
                logger.info(f"Lowest Jita price for {type_name}: {lowest_price:,.2f} ISK")
            else:
                logger.info(f"No Jita sell orders found for {type_name}")
        
        return lowest_prices
    
    def find_good_deals(self) -> List[Dict]:
        """
        Find good deals on T1 battleship hulls near Sosala.
        
        A good deal is defined as:
        1. Within MAX_JUMPS jumps of Sosala
        2. Price is at or below the lowest Jita price
        3. Price is above MIN_PRICE
        
        Returns:
            A list of good deals
        """
        logger.info("Finding good deals on T1 battleship hulls near Sosala...")
        
        # Fetch all relevant orders
        battleship_orders = self.fetch_battleship_orders()
        jita_prices = self.fetch_jita_prices()
        
        # List to store good deals
        good_deals = []
        
        # Check each order against our criteria
        for type_id, orders in battleship_orders.items():
            type_name = self.get_type_name(type_id)
            jita_price = jita_prices.get(type_id, float('inf'))
            
            for order in orders:
                price = order.get('price', 0)
                system_name = order.get('system_name', 'Unknown')
                distance = order.get('distance_to_sosala', 999)
                
                # Check if this is a good deal
                if price <= jita_price:
                    good_deal = {
                        'type_id': type_id,
                        'type_name': type_name,
                        'price': price,
                        'jita_price': jita_price,
                        'savings': jita_price - price,
                        'savings_percent': ((jita_price - price) / jita_price) * 100 if jita_price > 0 else 0,
                        'system_id': order.get('system_id'),
                        'system_name': system_name,
                        'distance_to_sosala': distance,
                        'volume_remain': order.get('volume_remain', 0),
                        'order_id': order.get('order_id')
                    }
                    good_deals.append(good_deal)
                    logger.info(
                        f"Found good deal: {type_name} in {system_name} "
                        f"({distance} jumps from Sosala) for {price:,.2f} ISK "
                        f"(Jita: {jita_price:,.2f} ISK, "
                        f"Savings: {good_deal['savings']:,.2f} ISK, "
                        f"{good_deal['savings_percent']:.2f}%)"
                    )
        
        # Sort deals by savings percentage (best deals first)
        good_deals.sort(key=lambda deal: deal['savings_percent'], reverse=True)
        
        return good_deals