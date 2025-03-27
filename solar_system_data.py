"""
Solar system data loader and region discovery functionality.
"""
import pickle
import logging
from typing import Dict, List, Set, TypedDict, Optional, Union
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
    solar_system_name: str
    solar_system_id: str
    region_name: str
    region_id: str
    constellation_name: str
    constellation_id: str
    adjacent: List[str]  # list of all adjacent Solar Systems in the network

def load_solar_systems(filepath: str) -> Dict[int, SolarSystem]:
    """
    Load solar system data from a pickle file.
    
    Args:
        filepath: Path to the pickle file containing solar system data
        
    Returns:
        Dictionary mapping solar system IDs to solar system data
    """
    try:
        logger.info(f"Attempting to load solar system data from {filepath}")
        with open(filepath, 'rb') as f:
            solar_systems = pickle.load(f)
        
        # Log some sample data to verify structure
        if solar_systems:
            sample_key = next(iter(solar_systems))
            logger.info(f"Sample solar system key type: {type(sample_key).__name__}")
            logger.info(f"Sample solar system data structure: {list(solar_systems[sample_key].keys())}")
            logger.info(f"Total number of solar systems loaded: {len(solar_systems)}")
            
        logger.info(f"Successfully loaded {len(solar_systems)} solar systems from {filepath}")
        return solar_systems
    except FileNotFoundError:
        logger.error(f"Solar system data file not found at {filepath}")
        return {}
    except pickle.UnpicklingError:
        logger.error(f"Error unpickling solar system data from {filepath}. File may be corrupted.")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error loading solar system data from {filepath}: {e}")
        return {}

def discover_regions_within_jumps(
    solar_systems: Dict[int, SolarSystem], 
    start_system_id: Union[str, int], 
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
    # Convert start_system_id to int if it's a string
    if isinstance(start_system_id, str):
        try:
            start_system_id = int(start_system_id)
            logger.info(f"Converted string system ID '{start_system_id}' to integer")
        except ValueError:
            logger.error(f"Invalid system ID format: {start_system_id}")
            return set()
    
    logger.info(f"Starting region discovery from system ID: {start_system_id}")
    
    if start_system_id not in solar_systems:
        logger.error(f"Starting system ID {start_system_id} not found in solar system data")
        logger.debug(f"Available system IDs: {list(solar_systems.keys())[:10]}...")
        return set()
    
    start_system_name = solar_systems[start_system_id]['solar_system_name']
    logger.info(f"Discovering regions within {max_jumps} jumps of {start_system_name} (ID: {start_system_id})...")
    
    # Set to store discovered region IDs
    region_ids = set()
    
    # Set to track visited systems
    visited = set()
    
    # Queue for BFS, storing (system_id, distance) pairs
    queue = deque([(start_system_id, 0)])
    visited.add(start_system_id)
    
    # Add the region of the starting system
    start_region_id = solar_systems[start_system_id]['region_id']
    start_region_name = solar_systems[start_system_id]['region_name']
    region_ids.add(start_region_id)
    logger.info(f"Added starting region: {start_region_name} (ID: {start_region_id})")
    
    # Track statistics for logging
    systems_visited = 0
    systems_by_distance = {0: 1}  # Distance -> count
    regions_by_distance = {0: {start_region_id: start_region_name}}  # Distance -> {region_id: region_name}
    
    # BFS to discover regions
    while queue:
        system_id, distance = queue.popleft()
        systems_visited += 1
        
        # If we've reached the maximum distance, don't explore further
        if distance >= max_jumps:
            continue
        
        # Get the current system
        system = solar_systems.get(system_id)
        if not system:
            logger.warning(f"System ID {system_id} not found in solar system data")
            continue
        
        # Add the region ID to our set if not already added
        region_id = system['region_id']
        region_name = system['region_name']
        if region_id not in region_ids:
            region_ids.add(region_id)
            logger.info(f"Discovered new region: {region_name} (ID: {region_id}) at distance {distance}")
            
            # Track regions by distance for statistics
            if distance not in regions_by_distance:
                regions_by_distance[distance] = {}
            regions_by_distance[distance][region_id] = region_name
        
        # Explore adjacent systems
        adjacent_count = 0
        for adjacent_id_str in system['adjacent']:
            try:
                adjacent_id = int(adjacent_id_str)
                if adjacent_id not in visited:
                    visited.add(adjacent_id)
                    queue.append((adjacent_id, distance + 1))
                    adjacent_count += 1
                    
                    # Track systems by distance for statistics
                    next_distance = distance + 1
                    if next_distance not in systems_by_distance:
                        systems_by_distance[next_distance] = 0
                    systems_by_distance[next_distance] += 1
            except ValueError:
                logger.warning(f"Invalid adjacent system ID format: {adjacent_id_str}")
        
        if adjacent_count > 0:
            logger.debug(f"Added {adjacent_count} adjacent systems from {system['solar_system_name']} (ID: {system_id})")
    
    # Log detailed statistics
    logger.info(f"BFS traversal complete: visited {systems_visited} systems across {len(region_ids)} regions")
    for distance in sorted(systems_by_distance.keys()):
        if distance <= max_jumps:
            logger.info(f"Systems at distance {distance}: {systems_by_distance[distance]}")
    
    for distance in sorted(regions_by_distance.keys()):
        regions_at_distance = regions_by_distance[distance]
        logger.info(f"Regions at distance {distance}: {', '.join([f'{name} ({rid})' for rid, name in regions_at_distance.items()])}")
    
    logger.info(f"Final result: Discovered {len(region_ids)} regions within {max_jumps} jumps of {start_system_name}")
    return region_ids

def find_system_id_by_name(solar_systems: Dict[int, SolarSystem], system_name: str) -> Optional[int]:
    """
    Find a system ID by its name using the solar system data.
    
    Args:
        solar_systems: Dictionary mapping solar system IDs to solar system data
        system_name: The name of the system to find
        
    Returns:
        The system ID if found, or None if not found
    """
    logger.info(f"Looking up system ID for name: {system_name}")
    
    if not solar_systems:
        logger.warning("No solar system data available, cannot look up system by name")
        return None
    
    # Search for the system by name (case-insensitive)
    system_name_lower = system_name.lower()
    for system_id, system_data in solar_systems.items():
        if system_data['solar_system_name'].lower() == system_name_lower:
            logger.info(f"Found system ID {system_id} for name {system_name}")
            return system_id
    
    # Log some available system names for debugging
    sample_systems = [(system_id, system_data['solar_system_name']) 
                      for system_id, system_data in list(solar_systems.items())[:10]]
    logger.debug(f"Sample available systems: {sample_systems}")
    logger.warning(f"No system found with name: {system_name}")
    return None

def get_regions_to_search(solar_system_data_path: str = None, reference_system_id: int = None, max_jumps: int = None) -> List[int]:
    """
    Get the list of region IDs to search based on the configured max jumps from the reference system.
    
    Args:
        solar_system_data_path: Path to the pickle file containing solar system data
        reference_system_id: ID of the reference system (defaults to config.REFERENCE_SYSTEM_ID)
        max_jumps: Maximum number of jumps to consider (defaults to config.MAX_JUMPS)
        
    Returns:
        List of region IDs to search
    """
    # Use the provided paths or fall back to configured values
    solar_system_data_path = solar_system_data_path or config.SOLAR_SYSTEM_DATA_PATH
    reference_system_id = reference_system_id or config.REFERENCE_SYSTEM_ID
    max_jumps = max_jumps if max_jumps is not None else config.MAX_JUMPS
    
    logger.info(f"Getting regions to search around system ID {reference_system_id} with max jumps {max_jumps}")
    logger.info(f"Using solar system data from: {solar_system_data_path}")
    
    # Load solar system data
    solar_systems = load_solar_systems(solar_system_data_path)
    
    if not solar_systems:
        logger.warning("No solar system data loaded, falling back to predefined regions")
        logger.info(f"Using fallback regions: {config.FALLBACK_REGION_IDS}")
        return config.FALLBACK_REGION_IDS
    
    # Discover regions within max jumps of the reference system
    logger.info(f"Starting region discovery from reference system ID: {reference_system_id}")
    region_ids = discover_regions_within_jumps(
        solar_systems, 
        reference_system_id, 
        max_jumps
    )
    
    # Convert region IDs to integers
    region_ids_int = [int(region_id) for region_id in region_ids]
    
    if not region_ids_int:
        logger.warning("No regions discovered, falling back to predefined regions")
        logger.info(f"Using fallback regions: {config.FALLBACK_REGION_IDS}")
        return config.FALLBACK_REGION_IDS
    
    logger.info(f"Final regions to search: {region_ids_int}")
    return region_ids_int