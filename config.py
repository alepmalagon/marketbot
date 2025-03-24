"""
Configuration settings for the EVE Online Market Bot.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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

# List of regions to search for orders
SEARCH_REGION_IDS = [
    LONETREK_REGION_ID,
    BLEAK_LANDS_REGION_ID,
    DOMAIN_REGION_ID,
    HEIMATAR_REGION_ID,
    DEVOID_REGION_ID
]

# System IDs
JITA_SYSTEM_ID = 30000142
SOSALA_SYSTEM_ID = 30002558

# T1 Battleship type IDs
# This is a list of all T1 battleship hull type IDs
T1_BATTLESHIP_TYPE_IDS = [
    # Amarr
    24692,  # Abaddon
    643,    # Apocalypse
    642,    # Armageddon
    
    # Caldari
    24688,  # Raven
    638,    # Rokh
    24690,  # Scorpion
    
    # Gallente
    641,    # Dominix
    24694,  # Hyperion
    645,    # Megathron
    
    # Minmatar
    24696,  # Maelstrom
    4302,   # Tempest
    639,    # Typhoon
]

# Maximum number of jumps from Sosala to consider
MAX_JUMPS = 4

# Minimum price to consider (to filter out low-value orders)
MIN_PRICE = 100000000  # 100 million ISK