"""
Main script for running the EVE Online Market Bot.
"""
import logging
import json
from datetime import datetime

from market_scanner import MarketScanner

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the market scanner and output the results."""
    logger.info("Starting EVE Online Market Bot...")
    
    # Create a market scanner
    scanner = MarketScanner()
    
    # Find good deals
    good_deals = scanner.find_good_deals()
    
    # Print the results
    if good_deals:
        logger.info(f"Found {len(good_deals)} good deals!")
        
                # Print the deals in a table format
        print("\n=== GOOD DEALS ON T1 BATTLESHIP HULLS NEAR SOSALA ===")
        print(f"{'Type Name':<15} {'System':<10} {'Jumps':<6} {'Price (ISK)':<20} {'Jita Price':<20} {'Savings':<20} {'Savings %':<10}")
        print("-" * 115)

        for deal in good_deals:
            print(
                f"{deal['type_name']:<15} "
                f"{deal['system_name']:<10} "
                f"{deal['distance_to_sosala']:<6} "
                f"{deal['price']:<19,.2f} "
                f"{deal['jita_price']:<19,.2f} "
                f"{deal['savings']:<19,.2f} "
                f"{deal['savings_percent']:<9.2f}%"
            )

        # Save the deals to a JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"deals_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(good_deals, f, indent=2)
        
        logger.info(f"Saved deals to {filename}")
    else:
        logger.info("No good deals found.")
    
    logger.info("EVE Online Market Bot finished.")

if __name__ == "__main__":
    main()