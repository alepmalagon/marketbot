"""
Main script for running the EVE Online Market Bot.

This script can run the bot in different modes:
1. Single scan mode (default): Run a single scan and exit
2. Foreground service mode: Run as a continuous service in the foreground
3. Background service mode: Run as a daemon process in the background
4. Windows service mode: Install and run as a Windows service
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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_single_scan(reference_system_id=None):
    """
    Run a single market scan and output the results.
    
    Args:
        reference_system_id: Optional system ID to use as reference
    """
    # If a reference system ID is provided, update the config
    if reference_system_id:
        config.REFERENCE_SYSTEM_ID = reference_system_id
        # Get the system name from the ESI API
        esi_client = ESIClient()
        system_info = esi_client.get_system_info(reference_system_id)
        config.REFERENCE_SYSTEM_NAME = system_info.get('name', f'System {reference_system_id}')
    
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
        choices=["scan", "foreground", "background", "windows-service"],
        default="scan",
        help="Operating mode: single scan, foreground service, background service, or Windows service"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        help="Override the check interval (in hours) from config"
    )
    
    parser.add_argument(
        "--system",
        type=int,
        help="System ID to use as reference (defaults to Sosala if not provided)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Override config if interval is specified
    if args.interval:
        config.CHECK_INTERVAL_HOURS = args.interval
        logger.info(f"Check interval set to {config.CHECK_INTERVAL_HOURS} hours")
    
    # Run in the appropriate mode
    if args.mode == "scan":
        run_single_scan(args.system)
    elif args.mode == "foreground":
        logger.info("Starting in foreground service mode...")
        run_in_foreground(args.system)
    elif args.mode == "background":
        if platform.system() == "Windows":
            logger.error("Background daemon mode is not supported on Windows.")
            logger.error("Please use --mode=windows-service instead.")
            return
        
        logger.info("Starting in background service mode...")
        run_as_daemon(args.system)
    elif args.mode == "windows-service":
        install_windows_service()

if __name__ == "__main__":
    main()