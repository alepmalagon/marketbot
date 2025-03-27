"""
Static dictionary of EVE Online ship hull data.

This module provides static dictionaries of ship hull names and IDs to avoid
making API calls to the EVE Online ESI API, which improves performance.
"""

# T1 Battleships
T1_BATTLESHIPS = {
    # Amarr
    24692: "Abaddon",
    642: "Apocalypse",
    643: "Armageddon",
    
    # Caldari
    638: "Raven",
    24688: "Rokh",
    640: "Scorpion",
    
    # Gallente
    645: "Dominix",
    24690: "Hyperion",
    641: "Megathron",
    
    # Minmatar
    24694: "Maelstrom",
    639: "Tempest",
    644: "Typhoon",
}

# Black Ops Battleships
BLACK_OPS = {
    22436: "Widow",        # Caldari
    22428: "Redeemer",     # Amarr
    22440: "Panther",      # Minmatar
    22430: "Sin",          # Gallente
}

# Marauder Battleships
MARAUDERS = {
    28665: "Vargur",       # Minmatar
    28710: "Golem",        # Caldari
    28659: "Paladin",      # Amarr
    28661: "Kronos",       # Gallente
}

# Faction Battleships
FACTION_BATTLESHIPS = {
    32305: "Armageddon Navy Issue",    # Amarr
    17726: "Apocalypse Navy Issue",    # Amarr
    47466: "Praxis",                   # SoCT
    17636: "Raven Navy Issue",         # Caldari
    32309: "Scorpion Navy Issue",      # Caldari
    32307: "Dominix Navy Issue",       # Gallente
    17728: "Megathron Navy Issue",     # Gallente
    32311: "Typhoon Fleet Issue",      # Minmatar
    17732: "Tempest Fleet Issue",      # Minmatar
}

# Pirate Faction Battleships
PIRATE_BATTLESHIPS = {
    33820: "Barghest",      # Guristas/Caldari
    17920: "Bhaalgorn",     # Blood Raiders/Amarr
    17736: "Nightmare",     # Sansha/Amarr
    17918: "Rattlesnake",   # Guristas/Caldari
    17738: "Machariel",     # Angel Cartel/Minmatar
    17740: "Vindicator",    # Serpentis/Gallente
    33472: "Nestor",        # Sisters of EVE
}

# Command Ships (Command Battlecruisers)
COMMAND_SHIPS = {
    22448: "Absolution",    # Amarr
    22474: "Damnation",     # Amarr
    22470: "Nighthawk",     # Caldari
    22446: "Vulture",       # Caldari
    22466: "Astarte",       # Gallente
    22442: "Eos",           # Gallente
    22468: "Claymore",      # Minmatar
    22444: "Sleipnir",      # Minmatar
}

# Strategic Cruisers
STRATEGIC_CRUISERS = {
    29986: "Legion",        # Amarr
    29984: "Tengu",         # Caldari
    29988: "Proteus",       # Gallente
    29990: "Loki",          # Minmatar
}

# Heavy Assault Cruisers
HEAVY_ASSAULT_CRUISERS = {
    12003: "Zealot",        # Amarr
    12019: "Sacrilege",     # Amarr
    12011: "Eagle",         # Caldari
    11993: "Cerberus",      # Caldari
    12023: "Deimos",        # Gallente
    12005: "Ishtar",        # Gallente
    11999: "Vagabond",      # Minmatar
    12015: "Muninn",        # Minmatar
}

# Recon Ships
RECON_SHIPS = {
    11965: "Pilgrim",       # Amarr
    20125: "Curse",         # Amarr
    11957: "Falcon",        # Caldari
    11959: "Rook",          # Caldari
    11969: "Arazu",         # Gallente
    11971: "Lachesis",      # Gallente
    11961: "Huginn",        # Minmatar
    11963: "Rapier",        # Minmatar
}

# Ship categories for UI display
SHIP_CATEGORIES = {
    # Battleships
    **{id: {"name": name, "category": "T1 Battleship"} for id, name in T1_BATTLESHIPS.items()},
    **{id: {"name": name, "category": "Black Ops"} for id, name in BLACK_OPS.items()},
    **{id: {"name": name, "category": "Marauder"} for id, name in MARAUDERS.items()},
    **{id: {"name": name, "category": "Faction Battleship"} for id, name in FACTION_BATTLESHIPS.items()},
    **{id: {"name": name, "category": "Pirate Battleship"} for id, name in PIRATE_BATTLESHIPS.items()},
    
    # Advanced Cruisers
    **{id: {"name": name, "category": "Strategic Cruiser"} for id, name in STRATEGIC_CRUISERS.items()},
    **{id: {"name": name, "category": "Heavy Assault Cruiser"} for id, name in HEAVY_ASSAULT_CRUISERS.items()},
    **{id: {"name": name, "category": "Recon Ship"} for id, name in RECON_SHIPS.items()},
    
    # Command Battlecruisers
    **{id: {"name": name, "category": "Command Ship"} for id, name in COMMAND_SHIPS.items()},
}

# Helper function to get ship info by ID
def get_ship_info(type_id):
    """
    Get information about a ship by its type ID.
    
    Args:
        type_id: The type ID of the ship
        
    Returns:
        A dictionary with the ship's name and category, or a default value if not found
    """
    if type_id in SHIP_CATEGORIES:
        return {
            "name": SHIP_CATEGORIES[type_id]["name"],
            "category": SHIP_CATEGORIES[type_id]["category"]
        }
    return {
        "name": f"Unknown Type {type_id}",
        "category": "Unknown"
    }

# Helper function to get all battleships
def get_all_battleships():
    """
    Get all battleship hulls.
    
    Returns:
        A list of dictionaries with battleship information
    """
    battleships = []
    
    # Add all battleship types
    for type_id, info in SHIP_CATEGORIES.items():
        if "Battleship" in info["category"] or info["category"] == "Black Ops" or info["category"] == "Marauder":
            battleships.append({
                "id": type_id,
                "name": info["name"],
                "category": info["category"]
            })
    
    return battleships

# Helper function to get all advanced cruisers
def get_all_cruisers():
    """
    Get all advanced cruiser hulls.
    
    Returns:
        A list of dictionaries with advanced cruiser information
    """
    cruisers = []
    
    # Add all cruiser types
    for type_id, info in SHIP_CATEGORIES.items():
        if "Cruiser" in info["category"] or info["category"] == "Recon Ship":
            cruisers.append({
                "id": type_id,
                "name": info["name"],
                "category": info["category"]
            })
    
    return cruisers

# Helper function to get all command battlecruisers
def get_all_command_ships():
    """
    Get all command battlecruiser hulls.
    
    Returns:
        A list of dictionaries with command battlecruiser information
    """
    command_ships = []
    
    # Add all command ship types
    for type_id, info in SHIP_CATEGORIES.items():
        if info["category"] == "Command Ship":
            command_ships.append({
                "id": type_id,
                "name": info["name"],
                "category": info["category"]
            })
    
    return command_ships