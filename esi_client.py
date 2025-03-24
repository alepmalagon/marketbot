"""
EVE ESI API client for fetching market data.
"""
import requests
import logging
from typing import Dict, List, Optional, Any, Union

import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ESIClient:
    """Client for interacting with the EVE Online ESI API."""
    
    def __init__(self):
        """Initialize the ESI client."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MarketBot/1.0 (github.com/alepmalagon/marketbot)'
        })
    
    def _make_request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Union[Dict, List, None]:
        """
        Make a request to the ESI API.
        
        Args:
            url: The URL to request
            params: Optional query parameters
            
        Returns:
            The JSON response or None if the request failed
        """
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            return None
    
    def get_market_orders(self, region_id: int, type_id: Optional[int] = None, order_type: Optional[str] = None) -> List[Dict]:
        """
        Get market orders from a specific region, optionally filtered by type ID and order type.
        
        Args:
            region_id: The region ID to get orders from
            type_id: Optional type ID to filter orders by
            order_type: Optional order type to filter by ('buy' or 'sell')
            
        Returns:
            A list of market orders
        """
        url = config.MARKET_ORDERS_ENDPOINT.format(region_id=region_id)
        params = {}
        
        if type_id is not None:
            params['type_id'] = type_id
        
        if order_type is not None:
            params['order_type'] = order_type
        
        response = self._make_request(url, params)
        return response if response else []
    
    def get_type_info(self, type_id: int) -> Dict:
        """
        Get information about a specific type.
        
        Args:
            type_id: The type ID to get information for
            
        Returns:
            Information about the type
        """
        url = config.UNIVERSE_TYPES_ENDPOINT.format(type_id=type_id)
        response = self._make_request(url)
        return response if response else {}
    
    def get_system_info(self, system_id: int) -> Dict:
        """
        Get information about a specific system.
        
        Args:
            system_id: The system ID to get information for
            
        Returns:
            Information about the system
        """
        url = config.UNIVERSE_SYSTEMS_ENDPOINT.format(system_id=system_id)
        response = self._make_request(url)
        return response if response else {}
    
    def get_route(self, origin: int, destination: int) -> List[int]:
        """
        Get the route between two systems.
        
        Args:
            origin: The origin system ID
            destination: The destination system ID
            
        Returns:
            A list of system IDs representing the route
        """
        url = config.ROUTE_ENDPOINT.format(origin=origin, destination=destination)
        response = self._make_request(url)
        return response if response else []
    
    def get_jump_distance(self, origin: int, destination: int) -> int:
        """
        Get the number of jumps between two systems.
        
        Args:
            origin: The origin system ID
            destination: The destination system ID
            
        Returns:
            The number of jumps between the systems
        """
        route = self.get_route(origin, destination)
        # The route includes both origin and destination, so the number of jumps is len(route) - 1
        # If the route is empty, return a large number to indicate that the systems are not connected
        return len(route) - 1 if route else 999