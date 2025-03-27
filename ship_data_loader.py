"""
Ship data loader for EVE Online Market Bot.

This module provides functionality to load ship data from the EVERef API
and update the configuration with the latest ship type IDs.
"""
import logging
import json
import os
from typing import Dict, List, Optional, Set

from everef_client import EVERefClient
import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ship category mapping
SHIP_CATEGORIES = {
    "Battleship": {
        "T1": [
            "Abaddon", "Apocalypse", "Armageddon",  # Amarr
            "Raven", "Rokh", "Scorpion",  # Caldari
            "Dominix", "Hyperion", "Megathron",  # Gallente
            "Maelstrom", "Tempest", "Typhoon"  # Minmatar
        ],
        "Black Ops": [
            "Widow", "Redeemer", "Panther", "Sin"
        ],
        "Marauder": [
            "Vargur", "Golem", "Paladin", "Kronos"
        ],
        "Faction": [
            "Armageddon Navy Issue", "Apocalypse Navy Issue", "Praxis",
            "Raven Navy Issue", "Scorpion Navy Issue",
            "Dominix Navy Issue", "Megathron Navy Issue",
            "Typhoon Fleet Issue", "Tempest Fleet Issue"
        ],
        "Pirate": [
            "Barghest", "Bhaalgorn", "Nightmare", "Rattlesnake",
            "Machariel", "Vindicator", "Nestor"
        ]
    },
    "Cruiser": {
        "Command Ship": [
            "Absolution", "Damnation", "Nighthawk", "Vulture",
            "Astarte", "Eos", "Claymore", "Sleipnir"
        ],
        "Strategic Cruiser": [
            "Legion", "Tengu", "Proteus", "Loki"
        ],
        "Heavy Assault Cruiser": [
            "Zealot", "Sacrilege", "Eagle", "Cerberus",
            "Deimos", "Ishtar", "Vagabond", "Muninn"
        ],
        "Recon Ship": [
            "Pilgrim", "Curse", "Falcon", "Rook",
            "Arazu", "Lachesis", "Huginn", "Rapier"
        ]
    }
}

# Cache file path
SHIP_DATA_CACHE_FILE = "ship_data_cache.json"

def load_ship_data_from_everef() -> Dict[str, Dict[str, List[Dict]]]:
    """
    Load ship data from the EVERef API.
    
    Returns:
        Dictionary mapping ship categories to ship data
    """
    logger.info("Loading ship data from EVERef API...")
    
    # Check if cache file exists and is recent
    if os.path.exists(SHIP_DATA_CACHE_FILE):
        try:
            with open(SHIP_DATA_CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                logger.info(f"Loaded ship data from cache file: {SHIP_DATA_CACHE_FILE}")
                return cache_data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading cache file: {e}")
    
    # Initialize EVERef client
    client = EVERefClient()
    
    # Initialize result dictionary
    ship_data = {}
    
    # Process each ship category
    for category, subcategories in SHIP_CATEGORIES.items():
        ship_data[category] = {}
        
        for subcategory, ship_names in subcategories.items():
            ship_data[category][subcategory] = []
            
            for ship_name in ship_names:
                # This is a simplified approach - in a real implementation,
                # we would need to search for the ship by name or use a more
                # sophisticated lookup method
                logger.info(f"Looking up data for {ship_name}...")
                
                # For now, we'll just create a placeholder entry
                # In a real implementation, this would be replaced with actual API calls
                ship_data[category][subcategory].append({
                    "name": ship_name,
                    "type_id": None,  # This would be filled with the actual type ID
                    "description": f"Description for {ship_name}"
                })
    
    # Save to cache file
    try:
        with open(SHIP_DATA_CACHE_FILE, 'w') as f:
            json.dump(ship_data, f, indent=2)
            logger.info(f"Saved ship data to cache file: {SHIP_DATA_CACHE_FILE}")
    except IOError as e:
        logger.warning(f"Error saving cache file: {e}")
    
    return ship_data

def update_config_with_ship_data():
    """
    Update the configuration with ship data from EVERef.
    """
    logger.info("Updating configuration with ship data from EVERef...")
    
    # Load ship data
    ship_data = load_ship_data_from_everef()
    
    # This is a placeholder implementation
    # In a real implementation, we would update the config with actual type IDs
    logger.info("Ship data loaded, but actual type ID update not implemented yet")
    logger.info("Using existing type IDs from configuration")

def get_ship_type_ids(category: str, subcategory: Optional[str] = None) -> List[int]:
    """
    Get ship type IDs for a specific category and optional subcategory.
    
    Args:
        category: Ship category (e.g., 'Battleship', 'Cruiser')
        subcategory: Optional subcategory (e.g., 'T1', 'Marauder')
        
    Returns:
        List of ship type IDs
    """
    if category == "Battleship":
        if subcategory == "T1":
            return config.T1_BATTLESHIP_TYPE_IDS
        elif subcategory == "Black Ops":
            return config.BLACK_OPS_TYPE_IDS
        elif subcategory == "Marauder":
            return config.MARAUDER_TYPE_IDS
        elif subcategory == "Faction":
            return config.FACTION_BATTLESHIP_TYPE_IDS
        elif subcategory == "Pirate":
            return config.PIRATE_BATTLESHIP_TYPE_IDS
        else:
            return config.ALL_BATTLESHIP_TYPE_IDS
    elif category == "Cruiser":
        if subcategory == "Command Ship":
            return config.COMMAND_SHIP_TYPE_IDS
        elif subcategory == "Strategic Cruiser":
            return config.STRATEGIC_CRUISER_TYPE_IDS
        elif subcategory == "Heavy Assault Cruiser":
            return config.HAC_TYPE_IDS
        elif subcategory == "Recon Ship":
            return config.RECON_SHIP_TYPE_IDS
        else:
            return config.ALL_CRUISER_TYPE_IDS
    else:
        logger.warning(f"Unknown ship category: {category}")
        return []

if __name__ == "__main__":
    # Test the module
    update_config_with_ship_data()
    
    # Print some ship type IDs
    print("T1 Battleship Type IDs:", get_ship_type_ids("Battleship", "T1"))
    print("All Battleship Type IDs:", get_ship_type_ids("Battleship"))
    print("All Cruiser Type IDs:", get_ship_type_ids("Cruiser"))