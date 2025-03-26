"""
Solar system data loader and region discovery functionality.
"""
import pickle
import logging
from typing import Dict, List, Set, TypedDict
from collections import deque

import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SolarSystem(TypedDict):
    """Type definition for solar system data."""
    name: str
    solar_system_id: str
    region: str
    region_id: str
    constellation: str
    constellation_id: str
    adjacent: List[str]  # list of all adjacent Solar Systems in the network

def load_solar_systems(filepath: str) -> Dict[str, SolarSystem]:
    """
    Load solar system data from a pickle file.
    
    Args:
        filepath: Path to the pickle file containing solar system data
        
    Returns:
        Dictionary mapping solar system IDs to solar system data
    """
    try:
        with open(filepath, 'rb') as f:
            solar_systems = pickle.load(f)
        logger.info(f"Loaded {len(solar_systems)} solar systems from {filepath}")
        return solar_systems
    except Exception as e:
        logger.error(f"Error loading solar system data from {filepath}: {e}")
        return {}

def discover_regions_within_jumps(
    solar_systems: Dict[str, SolarSystem], 
    start_system_id: str, 
    max_jumps: int
) -> Set[str]:
    """
    Discover all regions within a certain number of jumps from a starting system.
    Uses Breadth-First Search (BFS) to traverse the solar system network.
    
    Args:
        solar_systems: Dictionary mapping solar system IDs to solar system data
        start_system_id: ID of the starting solar system
        max_jumps: Maximum number of jumps to consider
        
    Returns:
        Set of region IDs within the specified number of jumps
    """
    start_system_id = int(start_system_id)
    if start_system_id not in solar_systems:
        logger.error(f"Starting system ID {start_system_id} not found in solar system data")
        return set()
    
    logger.info(f"Discovering regions within {max_jumps} jumps of {solar_systems[start_system_id]['solar_system_name']}...")
    
    # Set to store discovered region IDs
    region_ids = set()
    
    # Set to track visited systems
    visited = set()
    
    # Queue for BFS, storing (system_id, distance) pairs
    queue = deque([(start_system_id, 0)])
    visited.add(start_system_id)
    
    # Add the region of the starting system
    region_ids.add(solar_systems[start_system_id]['region_id'])
    
    # BFS to discover regions
    while queue:
        system_id, distance = queue.popleft()
        
        # If we've reached the maximum distance, don't explore further
        if distance >= max_jumps:
            continue
        
        # Get the current system
        system = solar_systems.get(system_id)
        if not system:
            continue
        
        # Add the region ID to our set
        region_ids.add(system['region_id'])
        logger.info(f"Discovered region ID: {system['region_name']} ({system['region_id']})")   
        # Explore adjacent systems
        for adjacent_id in system['adjacent']:
            if adjacent_id not in visited:
                visited.add(adjacent_id)
                queue.append((adjacent_id, distance + 1))
    
    logger.info(f"Discovered {len(region_ids)} regions within {max_jumps} jumps of {solar_systems[start_system_id]['solar_system_name']}")
    return region_ids

def get_regions_to_search(solar_system_data_path: str = "solar_systems.pickle", reference_system_id: int = None) -> List[int]:
    """
    Get the list of region IDs to search based on the configured max jumps from the reference system.
    
    Args:
        solar_system_data_path: Path to the pickle file containing solar system data
        reference_system_id: ID of the reference system (defaults to config.REFERENCE_SYSTEM_ID)
        
    Returns:
        List of region IDs to search
    """
    # Use the provided reference system ID or fall back to the configured one
    reference_system_id = reference_system_id or config.REFERENCE_SYSTEM_ID
    
    # Load solar system data
    solar_systems = load_solar_systems(solar_system_data_path)
    
    if not solar_systems:
        logger.warning("No solar system data loaded, falling back to predefined regions")
        return config.FALLBACK_REGION_IDS
    
    # Discover regions within max jumps of the reference system
    region_ids = discover_regions_within_jumps(
        solar_systems, 
        str(reference_system_id), 
        config.MAX_JUMPS
    )
    
    # Convert region IDs to integers
    region_ids_int = [int(region_id) for region_id in region_ids]
    
    if not region_ids_int:
        logger.warning("No regions discovered, falling back to predefined regions")
        return config.FALLBACK_REGION_IDS
    
    return region_ids_int