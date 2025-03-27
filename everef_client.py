"""
EVERef API client for fetching reference data from the EVE Online universe.

This module provides a client for interacting with the EVERef API,
which offers comprehensive reference data about the EVE Online universe.
"""
import logging
import requests
from typing import Dict, List, Any, Optional, Union
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EVERefClient:
    """Client for interacting with the EVERef API."""
    
    def __init__(self):
        """Initialize the EVERef client."""
        self.base_url = "https://ref-data.everef.net"
        self.cache = {}
        self.cache_expiry = {}
        self.cache_duration = 3600  # Cache duration in seconds (1 hour)
        self.request_delay = 0.5  # Delay between requests in seconds
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting to avoid overwhelming the API."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.request_delay:
            sleep_time = self.request_delay - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str) -> Optional[Dict]:
        """
        Make a request to the EVERef API.
        
        Args:
            endpoint: API endpoint to request
            
        Returns:
            Response data as a dictionary, or None if the request failed
        """
        # Check cache first
        if endpoint in self.cache and time.time() < self.cache_expiry.get(endpoint, 0):
            logger.debug(f"Using cached data for {endpoint}")
            return self.cache[endpoint]
        
        # Apply rate limiting
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        logger.debug(f"Making request to {url}")
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Cache the response
            self.cache[endpoint] = data
            self.cache_expiry[endpoint] = time.time() + self.cache_duration
            
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to {url}: {e}")
            return None
    
    def get_type_info(self, type_id: int) -> Optional[Dict]:
        """
        Get information about a specific type.
        
        Args:
            type_id: EVE Online type ID
            
        Returns:
            Type information as a dictionary, or None if not found
        """
        return self._make_request(f"types/{type_id}")
    
    def get_region_info(self, region_id: int) -> Optional[Dict]:
        """
        Get information about a specific region.
        
        Args:
            region_id: EVE Online region ID
            
        Returns:
            Region information as a dictionary, or None if not found
        """
        return self._make_request(f"regions/{region_id}")
    
    def get_system_info(self, system_id: int) -> Optional[Dict]:
        """
        Get information about a specific solar system.
        
        Args:
            system_id: EVE Online solar system ID
            
        Returns:
            System information as a dictionary, or None if not found
        """
        # Note: The EVERef API doesn't have a direct endpoint for systems
        # This would need to be implemented if they add it in the future
        logger.warning("EVERef API doesn't currently support direct system lookups")
        return None
    
    def get_all_ship_types(self, category: Optional[str] = None) -> List[Dict]:
        """
        Get all ship types, optionally filtered by category.
        
        Args:
            category: Optional category to filter by (e.g., 'battleship', 'cruiser')
            
        Returns:
            List of ship type information dictionaries
        """
        # This would need to be implemented based on the EVERef API structure
        # For now, return an empty list as a placeholder
        logger.warning("get_all_ship_types not yet implemented for EVERef API")
        return []
    
    def get_market_group_info(self, group_id: int) -> Optional[Dict]:
        """
        Get information about a specific market group.
        
        Args:
            group_id: EVE Online market group ID
            
        Returns:
            Market group information as a dictionary, or None if not found
        """
        return self._make_request(f"market_groups/{group_id}")
    
    def get_dogma_attributes(self, type_id: int) -> Optional[Dict]:
        """
        Get dogma attributes for a specific type.
        
        Args:
            type_id: EVE Online type ID
            
        Returns:
            Dogma attributes as a dictionary, or None if not found
        """
        type_info = self.get_type_info(type_id)
        if type_info and 'dogma_attributes' in type_info:
            return type_info['dogma_attributes']
        return None