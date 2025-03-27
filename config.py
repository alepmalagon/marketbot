"""
Configuration settings for the EVE Online Market Bot.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Scheduler settings
# How often to check for deals (in hours)
CHECK_INTERVAL_HOURS = int(os.getenv('CHECK_INTERVAL_HOURS', '4'))

# Notification settings
# Whether to show desktop notifications
ENABLE_NOTIFICATIONS = os.getenv('ENABLE_NOTIFICATIONS', 'true').lower() == 'true'
# Minimum savings percentage to trigger a notification
MIN_SAVINGS_PERCENT_FOR_NOTIFICATION = float(os.getenv('MIN_SAVINGS_PERCENT_FOR_NOTIFICATION', '5.0'))
# Maximum number of notifications to show at once
MAX_NOTIFICATIONS = int(os.getenv('MAX_NOTIFICATIONS', '5'))

# EVE ESI API endpoints
ESI_BASE_URL = "https://esi.evetech.net/latest"
MARKET_ORDERS_ENDPOINT = f"{ESI_BASE_URL}/markets/{{region_id}}/orders/"
UNIVERSE_TYPES_ENDPOINT = f"{ESI_BASE_URL}/universe/types/{{type_id}}/"
UNIVERSE_SYSTEMS_ENDPOINT = f"{ESI_BASE_URL}/universe/systems/{{system_id}}/"
UNIVERSE_REGIONS_ENDPOINT = f"{ESI_BASE_URL}/universe/regions/{{region_id}}/"
ROUTE_ENDPOINT = f"{ESI_BASE_URL}/route/{{origin}}/{{destination}}/"

# Region IDs
# The Forge (contains Jita)
FORGE_REGION_ID = 10000002
# Regions around Sosala
LONETREK_REGION_ID = 10000016
BLEAK_LANDS_REGION_ID = 10000038  # The Bleak Lands
DOMAIN_REGION_ID = 10000043       # Domain
HEIMATAR_REGION_ID = 10000030     # Heimatar
DEVOID_REGION_ID = 10000036       # Devoid

# Path to the solar system data file
SOLAR_SYSTEM_DATA_PATH = os.getenv('SOLAR_SYSTEM_DATA_PATH', 'solar_systems.pickle')

# Fallback list of regions to search for orders if solar system data is not available
FALLBACK_REGION_IDS = [
    LONETREK_REGION_ID,
    BLEAK_LANDS_REGION_ID,
    DOMAIN_REGION_ID,
    HEIMATAR_REGION_ID,
    DEVOID_REGION_ID
]

# System IDs
JITA_SYSTEM_ID = 30000142
# Default reference system (Sosala)
REFERENCE_SYSTEM_ID = int(os.getenv('REFERENCE_SYSTEM_ID', '30003070'))  # Default to Sosala
REFERENCE_SYSTEM_NAME = os.getenv('REFERENCE_SYSTEM_NAME', 'Sosala')  # Default to Sosala

# T1 Battleship type IDs
# This is a list of all T1 battleship hull type IDs
T1_BATTLESHIP_TYPE_IDS = [
    # Amarr
    24692,  # Abaddon
    642,    # Apocalypse
    643,    # Armageddon
    
    # Caldari
    638,  # Raven
    24688,    # Rokh
    640,  # Scorpion
    
    # Gallente
    645,    # Dominix
    24690,  # Hyperion
    641,    # Megathron
    
    # Minmatar
    24694,  # Maelstrom
    639,   # Tempest
    644,    # Typhoon
]

# Black Ops Battleship type IDs
BLACK_OPS_TYPE_IDS = [
    22436,  # Widow (Caldari)
    22428,  # Redeemer (Amarr)
    22440,  # Panther (Minmatar)
    22430,  # Sin (Gallente)
]

# Marauder Battleship type IDs
MARAUDER_TYPE_IDS = [
    28665,  # Vargur (Minmatar)
    28710,  # Golem (Caldari)
    28659,  # Paladin (Amarr)
    28661,  # Kronos (Gallente)
]

# Faction Battleship type IDs
FACTION_BATTLESHIP_TYPE_IDS = [
    32305,  # Armageddon Navy Issue (Amarr)
    17726,  # Apocalypse Navy Issue (Amarr)
    47466,  # Praxis (SoCT)
    17636,  # Raven Navy Issue (Caldari)
    32309,  # Scorpion Navy Issue (Caldari)
    32307,  # Dominix Navy Issue (Gallente)
    17728,  # Megathron Navy Issue (Gallente)
    32311,  # Typhoon Fleet Issue (Minmatar)
    17732,  # Tempest Fleet Issue (Minmatar)
]

# Pirate Faction Battleship type IDs
PIRATE_BATTLESHIP_TYPE_IDS = [
    33820,  # Barghest (Guristas/Caldari)
    17920,  # Bhaalgorn (Blood Raiders/Amarr)
    17736,  # Nightmare (Sansha/Amarr)
    17918,  # Rattlesnake (Guristas/Caldari)
    17738,  # Machariel (Angel Cartel/Minmatar)
    17740,  # Vindicator (Serpentis/Gallente)
    33472,  # Nestor (Sisters of EVE)
]

# Command Ship type IDs
COMMAND_SHIP_TYPE_IDS = [
    22448,  # Absolution (Amarr)
    22474,  # Damnation (Amarr)
    22470,  # Nighthawk (Caldari)
    22446,  # Vulture (Caldari)
    22466,  # Astarte (Gallente)
    22442,  # Eos (Gallente)
    22468,  # Claymore (Minmatar)
    22444,  # Sleipnir (Minmatar)
]

# Strategic Cruiser type IDs
STRATEGIC_CRUISER_TYPE_IDS = [
    29986,  # Legion (Amarr)
    29984,  # Tengu (Caldari)
    29988,  # Proteus (Gallente)
    29990,  # Loki (Minmatar)
]

# Heavy Assault Cruiser type IDs
HAC_TYPE_IDS = [
    12003,  # Zealot (Amarr)
    12019,  # Sacrilege (Amarr)
    12011,  # Eagle (Caldari)
    11993,  # Cerberus (Caldari)
    12023,  # Deimos (Gallente)
    12005,  # Ishtar (Gallente)
    11999,  # Vagabond (Minmatar)
    12015,  # Muninn (Minmatar)
]

# Recon Ship type IDs
RECON_SHIP_TYPE_IDS = [
    11965,  # Pilgrim (Amarr)
    20125,  # Curse (Amarr)
    11957,  # Falcon (Caldari)
    11959,  # Rook (Caldari)
    11969,  # Arazu (Gallente)
    11971,  # Lachesis (Gallente)
    11961,  # Huginn (Minmatar)
    11963,  # Rapier (Minmatar)
]

# Combined list of all battleship type IDs
ALL_BATTLESHIP_TYPE_IDS = T1_BATTLESHIP_TYPE_IDS + BLACK_OPS_TYPE_IDS + MARAUDER_TYPE_IDS + FACTION_BATTLESHIP_TYPE_IDS + PIRATE_BATTLESHIP_TYPE_IDS

# Combined list of all advanced cruiser type IDs (excluding Command Ships)
ALL_CRUISER_TYPE_IDS = STRATEGIC_CRUISER_TYPE_IDS + HAC_TYPE_IDS + RECON_SHIP_TYPE_IDS

# Command Battlecruisers
ALL_COMMAND_SHIP_TYPE_IDS = COMMAND_SHIP_TYPE_IDS

# Maximum number of jumps from reference system to consider
MAX_JUMPS = 8

# Minimum price to consider (to filter out low-value orders)
MIN_PRICE = 150000000  # 150 million ISK