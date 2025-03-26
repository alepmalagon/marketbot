"""
Main script for running the EVE Online Market Bot.

This script can run the bot in different modes:
1. Single scan mode (default): Run a single scan and exit
2. Foreground service mode: Run as a continuous service in the foreground
3. Background service mode: Run as a daemon process in the background
4. Windows service mode: Install and run as a Windows service
5. Web UI mode: Run a web server with a user interface
"""
import argparse
import logging
import json
import os
import platform
import sys
from datetime import datetime

from market_scanner import MarketScanner
from service_manager import ServiceManager, run_as_daemon, run_in_foreground
import config
from esi_client import ESIClient
from solar_system_data import load_solar_systems
from web_server import run_web_server

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_system_id_by_name(system_name: str) -> int:
    """
    Find a system ID by its name using the solar system data.
    
    Args:
        system_name: The name of the system to find
        
    Returns:
        The system ID if found, or None if not found
    """
    logger.info(f"Looking up system ID for name: {system_name}")
    
    # Load solar system data
    solar_systems = load_solar_systems(config.SOLAR_SYSTEM_DATA_PATH)
    
    if not solar_systems:
        logger.warning("No solar system data available, cannot look up system by name")
        return None
    
    # Search for the system by name (case-insensitive)
    system_name_lower = system_name.lower()
    for system_id, system_data in solar_systems.items():
        if system_data['solar_system_name'].lower() == system_name_lower:
            logger.info(f"Found system ID {system_id} for name {system_name}")
            return system_id
    
    logger.warning(f"No system found with name: {system_name}")
    return None

def resolve_reference_system(system_input):
    """
    Resolve the reference system from user input, which could be an ID or name.
    
    Args:
        system_input: The system ID or name provided by the user
        
    Returns:
        The resolved system ID or None if not resolved
    """
    if system_input is None:
        return None
    
    # Check if the input is already a numeric ID
    if isinstance(system_input, int) or (isinstance(system_input, str) and system_input.isdigit()):
        return int(system_input)
    
    # Otherwise, treat it as a system name and look up the ID
    return find_system_id_by_name(system_input)

def parse_hull_ids(hull_ids_str):
    """
    Parse a comma-separated string of hull IDs into a list of integers.
    
    Args:
        hull_ids_str: A comma-separated string of hull IDs
        
    Returns:
        A list of hull IDs as integers, or None if the input is invalid
    """
    if not hull_ids_str:
        return None
        
    try:
        # Split the string by commas and convert each part to an integer
        hull_ids = [int(id_str.strip()) for id_str in hull_ids_str.split(',')]
        logger.info(f"Parsed hull IDs: {hull_ids}")
        return hull_ids
    except ValueError:
        logger.error(f"Invalid hull IDs format: {hull_ids_str}. Expected comma-separated integers.")
        return None

def run_single_scan(reference_system=None, max_jumps=None, hull_ids=None):
    """
    Run a single market scan and output the results.
    
    Args:
        reference_system: Optional system ID or name to use as reference
        max_jumps: Optional maximum number of jumps from reference system
        hull_ids: Optional list of hull type IDs to search for
    """
    # Resolve the reference system (could be ID or name)
    reference_system_id = resolve_reference_system(reference_system)
    
    # If we couldn't resolve the system, use the default
    if reference_system_id is None and reference_system is not None:
        logger.warning(f"Could not resolve system: {reference_system}, using default system")
        return
    
    # If a reference system ID is provided, update the config
    if reference_system_id:
        config.REFERENCE_SYSTEM_ID = reference_system_id
        # Get the system name from the ESI API
        esi_client = ESIClient()
        system_info = esi_client.get_system_info(reference_system_id)
        config.REFERENCE_SYSTEM_NAME = system_info.get('name', f'System {reference_system_id}')
    
    # If max_jumps is provided, update the config
    if max_jumps is not None:
        config.MAX_JUMPS = max_jumps
        logger.info(f"Maximum jumps set to {config.MAX_JUMPS}")
    
    # If hull_ids is provided, update the config
    if hull_ids is not None:
        config.T1_BATTLESHIP_TYPE_IDS = hull_ids
        logger.info(f"Using custom hull type IDs: {config.T1_BATTLESHIP_TYPE_IDS}")
    
    logger.info(f"Starting EVE Online Market Bot (single scan mode) for {config.REFERENCE_SYSTEM_NAME}...")
    
    # Create a market scanner with the reference system
    scanner = MarketScanner(
        reference_system_id=config.REFERENCE_SYSTEM_ID,
        reference_system_name=config.REFERENCE_SYSTEM_NAME
    )
    
    # Find good deals
    good_deals = scanner.find_good_deals()
    
    # Print the results
    if good_deals:
        logger.info(f"Found {len(good_deals)} good deals!")
        
        # Print the deals in a table format
        print(f"\n=== GOOD DEALS ON T1 BATTLESHIP HULLS NEAR {config.REFERENCE_SYSTEM_NAME.upper()} ===")
        print(f"{'Type Name':<15} {'System':<10} {'Jumps':<6} {'Price (ISK)':<20} {'Jita Price':<20} {'Savings':<20} {'Savings %':<10}")
        print("-" * 115)

        for deal in good_deals:
            print(
                f"{deal['type_name']:<15} "
                f"{deal['system_name']:<10} "
                f"{deal['distance_to_reference']:<6} "
                f"{deal['price']:<19,.2f} "
                f"{deal['jita_price']:<19,.2f} "
                f"{deal['savings']:<19,.2f} "
                f"{deal['savings_percent']:<9.2f}%"
            )

        # Save the deals to a JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"deals_{config.REFERENCE_SYSTEM_NAME.lower()}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(good_deals, f, indent=2)
        
        logger.info(f"Saved deals to {filename}")
    else:
        logger.info("No good deals found.")
    
    logger.info("EVE Online Market Bot finished.")

def install_windows_service():
    """Install the bot as a Windows service."""
    if platform.system() != "Windows":
        logger.error("Windows service installation is only available on Windows.")
        return
    
    try:
        import win32serviceutil
        import windows_service
        
        win32serviceutil.HandleCommandLine(windows_service.MarketBotService)
        logger.info("Windows service command processed.")
    except ImportError:
        logger.error("Required packages for Windows service not installed.")
        logger.error("Please install pywin32: pip install pywin32")
    except Exception as e:
        logger.error(f"Error installing Windows service: {e}")

def main():
    """Parse command line arguments and run the bot in the appropriate mode."""
    parser = argparse.ArgumentParser(description="EVE Online Market Bot")
    
    # Add command line arguments
    parser.add_argument(
        "--mode", 
        choices=["scan", "foreground", "background", "windows-service", "web-ui"],
        default="scan",
        help="Operating mode: single scan, foreground service, background service, Windows service, or Web UI"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        help="Override the check interval (in hours) from config"
    )
    
    parser.add_argument(
        "--system",
        type=str,
        help="System ID or name to use as reference (defaults to Sosala if not provided)"
    )
    
    parser.add_argument(
        "--jumps",
        type=int,
        help="Maximum number of jumps from reference system to consider (defaults to 8)"
    )
    
    parser.add_argument(
        "--hulls",
        type=str,
        help="Comma-separated list of hull type IDs to search for (defaults to all T1 battleships)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Override config if interval is specified
    if args.interval:
        config.CHECK_INTERVAL_HOURS = args.interval
        logger.info(f"Check interval set to {config.CHECK_INTERVAL_HOURS} hours")
    
    # Parse hull IDs if specified
    hull_ids = None
    if args.hulls:
        hull_ids = parse_hull_ids(args.hulls)
    
    # Run in the appropriate mode
    if args.mode == "scan":
        run_single_scan(args.system, args.jumps, hull_ids)
    elif args.mode == "foreground":
        logger.info("Starting in foreground service mode...")
        run_in_foreground(args.system, args.jumps, hull_ids)
    elif args.mode == "background":
        if platform.system() == "Windows":
            logger.error("Background daemon mode is not supported on Windows.")
            logger.error("Please use --mode=windows-service instead.")
            return
        
        logger.info("Starting in background service mode...")
        run_as_daemon(args.system, args.jumps, hull_ids)
    elif args.mode == "windows-service":
        install_windows_service()
    elif args.mode == "web-ui":
        run_web_server()

if __name__ == "__main__":
    main()