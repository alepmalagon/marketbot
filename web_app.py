#!/usr/bin/env python3
"""
Standalone Web Application for the EVE Online Market Bot.

This script runs a web server that provides a user interface for the market bot,
allowing users to:
1. Select a reference system
2. Choose which battleship hulls to search for
3. Set the maximum number of jumps
4. Run the market scanner and view the results

Run this script directly to start the web server:
    python web_app.py [--host HOST] [--port PORT] [--debug]
"""
import argparse
import logging
import os
import sys
from web_server_fixed import run_web_server

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Parse command line arguments and run the web server."""
    parser = argparse.ArgumentParser(description="EVE Online Market Bot Web Application")
    
    # Add command line arguments
    parser.add_argument(
        "--host", 
        type=str,
        default="0.0.0.0",
        help="Host address to bind the web server to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to run the web server on (default: 5000)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run the web server in debug mode"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create static and templates directories if they don't exist
    os.makedirs('static', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # Print startup message
    logger.info("Starting EVE Online Market Bot Web Application")
    logger.info(f"Web interface will be available at http://{args.host if args.host != '0.0.0.0' else 'localhost'}:{args.port}")
    logger.info("Press Ctrl+C to stop the server")
    
    # Run the web server
    run_web_server(host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)