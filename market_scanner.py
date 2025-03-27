"""
Market scanner for finding good deals on EVE Online ship hulls.
"""
import logging
from typing import Dict, List
from collections import defaultdict

from esi_client import ESIClient
from solar_system_data import get_regions_to_search
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MarketScanner:
    """Scanner for finding good deals on ship hulls."""
    
    def __init__(self, reference_system_id=None, reference_system_name=None):
        self.esi_client = ESIClient()
        self.type_names = {}
        self.system_names = {}
        self.system_distances = {}
        
        self.reference_system_id = reference_system_id or config.REFERENCE_SYSTEM_ID
        self.reference_system_name = reference_system_name or config.REFERENCE_SYSTEM_NAME
    
    def get_type_name(self, type_id: int) -> str:
        if type_id not in self.type_names:
            type_info = self.esi_client.get_type_info(type_id)
            self.type_names[type_id] = type_info.get('name', f'Unknown Type {type_id}')
        return self.type_names[type_id]
    
    def get_system_name(self, system_id: int) -> str:
        if system_id not in self.system_names:
            system_info = self.esi_client.get_system_info(system_id)
            self.system_names[system_id] = system_info.get('name', f'Unknown System {system_id}')
        return self.system_names[system_id]
    
    def get_distance_to_reference(self, system_id: int) -> int:
        if system_id == self.reference_system_id:
            return 0
        
        cache_key = (system_id, self.reference_system_id)
        if cache_key not in self.system_distances:
            distance = self.esi_client.get_jump_distance(system_id, self.reference_system_id)
            self.system_distances[cache_key] = distance
        
        return self.system_distances[cache_key]
    
    def fetch_ship_orders(self, ship_type='battleship') -> Dict[int, List[Dict]]:
        """Fetch market orders for the specified ship type."""
        logger.info(f"Fetching {ship_type} sell orders from regions around {self.reference_system_name}...")
        
        orders_by_type = defaultdict(list)
        
        search_region_ids = get_regions_to_search(config.SOLAR_SYSTEM_DATA_PATH, self.reference_system_id)
        logger.info(f"Discovered {len(search_region_ids)} regions to search: {search_region_ids}")
        
        # Determine which ship type IDs to use
        if ship_type == 'battleship':
            type_ids = config.ALL_BATTLESHIP_TYPE_IDS
        elif ship_type == 'cruiser':
            type_ids = config.ALL_CRUISER_TYPE_IDS
        else:
            logger.warning(f"Unknown ship type: {ship_type}, defaulting to battleships")
            type_ids = config.ALL_BATTLESHIP_TYPE_IDS
        
        for type_id in type_ids:
            type_name = self.get_type_name(type_id)
            logger.info(f"Fetching orders for {type_name} (Type ID: {type_id})")
            
            all_orders = []
            for region_id in search_region_ids:
                logger.debug(f"Searching region ID: {region_id}")
                orders = self.esi_client.get_market_orders(
                    region_id=region_id,
                    type_id=type_id,
                    order_type='sell'
                )
                all_orders.extend(orders)
            
            filtered_orders = [
                order for order in all_orders
                if order.get('price', 0) >= config.MIN_PRICE
            ]
            
            for order in filtered_orders:
                system_id = order.get('system_id')
                if system_id:
                    order['system_name'] = self.get_system_name(system_id)
                    order['distance_to_reference'] = self.get_distance_to_reference(system_id)
            
            nearby_orders = [
                order for order in filtered_orders
                if order.get('distance_to_reference', 999) <= config.MAX_JUMPS
            ]
            
            if nearby_orders:
                logger.info(f"Found {len(nearby_orders)} nearby sell orders for {type_name}")
                orders_by_type[type_id].extend(nearby_orders)
            else:
                logger.info(f"No nearby sell orders found for {type_name}")
        
        return orders_by_type
    
    def fetch_jita_prices(self, ship_type='battleship') -> Dict[int, float]:
        """Fetch Jita prices for the specified ship type."""
        logger.info(f"Fetching {ship_type} sell prices from Jita...")
        
        lowest_prices = {}
        
        # Determine which ship type IDs to use
        if ship_type == 'battleship':
            type_ids = config.ALL_BATTLESHIP_TYPE_IDS
        elif ship_type == 'cruiser':
            type_ids = config.ALL_CRUISER_TYPE_IDS
        else:
            logger.warning(f"Unknown ship type: {ship_type}, defaulting to battleships")
            type_ids = config.ALL_BATTLESHIP_TYPE_IDS
        
        for type_id in type_ids:
            type_name = self.get_type_name(type_id)
            logger.info(f"Fetching Jita prices for {type_name} (Type ID: {type_id})")
            
            orders = self.esi_client.get_market_orders(
                region_id=config.FORGE_REGION_ID,
                type_id=type_id,
                order_type='sell'
            )
            
            jita_orders = [
                order for order in orders
                if order.get('system_id') == config.JITA_SYSTEM_ID
            ]
            
            if jita_orders:
                lowest_price = min(order.get('price', float('inf')) for order in jita_orders)
                lowest_prices[type_id] = lowest_price
                logger.info(f"Lowest Jita price for {type_name}: {lowest_price:,.2f} ISK")
            else:
                logger.info(f"No Jita sell orders found for {type_name}")
        
        return lowest_prices
    
    def find_good_deals(self, ship_type='battleship') -> List[Dict]:
        """Find good deals on ship hulls near the reference system."""
        logger.info(f"Finding good deals on {ship_type} hulls near {self.reference_system_name}...")
        
        ship_orders = self.fetch_ship_orders(ship_type)
        jita_prices = self.fetch_jita_prices(ship_type)
        
        good_deals = []
        
        for type_id, orders in ship_orders.items():
            type_name = self.get_type_name(type_id)
            jita_price = jita_prices.get(type_id, float('inf'))
            
            for order in orders:
                price = order.get('price', 0)
                system_name = order.get('system_name', 'Unknown')
                distance = order.get('distance_to_reference', 999)
                
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
                        'distance_to_reference': distance,
                        'volume_remain': order.get('volume_remain', 0),
                        'order_id': order.get('order_id')
                    }
                    good_deals.append(good_deal)
                    logger.info(
                        f"Found good deal: {type_name} in {system_name} "
                        f"({distance} jumps from {self.reference_system_name}) for {price:,.2f} ISK "
                        f"(Jita: {jita_price:,.2f} ISK, "
                        f"Savings: {good_deal['savings']:,.2f} ISK, "
                        f"{good_deal['savings_percent']:.2f}%)"
                    )
        
        good_deals.sort(key=lambda deal: deal['savings_percent'], reverse=True)
        
        return good_deals