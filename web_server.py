"""
Web server for the EVE Online Market Bot.

This module provides a web interface for the market bot, allowing users to:
1. Select a reference system
2. Choose which battleship hulls to search for
3. Set the maximum number of jumps
4. Run the market scanner and view the results
"""
import json
import logging
import os
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS

from enhanced_market_scanner import EnhancedMarketScanner
import config
from esi_client import ESIClient
from solar_system_data import load_solar_systems
from main import resolve_reference_system, parse_hull_ids
from ship_hulls import get_all_battleships, get_all_cruisers, get_all_command_ships, get_ship_info

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for all routes

# Create static and templates directories if they don't exist
os.makedirs('static', exist_ok=True)
os.makedirs('templates', exist_ok=True)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)

@app.route('/api/battleships', methods=['GET'])
def get_battleships():
    """Get the list of all battleship hulls."""
    # Use the static data instead of making API calls
    battleships = get_all_battleships()
    return jsonify(battleships)

@app.route('/api/cruisers', methods=['GET'])
def get_cruisers():
    """Get the list of all advanced cruiser hulls."""
    # Use the static data instead of making API calls
    cruisers = get_all_cruisers()
    return jsonify(cruisers)

@app.route('/api/command_ships', methods=['GET'])
def get_command_ships():
    """Get the list of all command battlecruiser hulls."""
    # Use the static data instead of making API calls
    command_ships = get_all_command_ships()
    return jsonify(command_ships)

@app.route('/api/systems', methods=['GET'])
def get_systems():
    """Get a list of solar systems for the autocomplete."""
    solar_systems = load_solar_systems(config.SOLAR_SYSTEM_DATA_PATH)
    
    if not solar_systems:
        return jsonify([])
    
    # Convert to a list of system names and IDs
    systems_list = [
        {
            'id': system_id,
            'name': system_data['solar_system_name']
        }
        for system_id, system_data in solar_systems.items()
    ]
    
    # Sort by name
    systems_list.sort(key=lambda x: x['name'])
    
    return jsonify(systems_list)

@app.route('/api/scan', methods=['POST'])
def run_scan():
    """Run a market scan with the provided parameters."""
    data = request.json
    
    # Get parameters from request
    system_input = data.get('system')
    max_jumps = data.get('jumps')
    hull_ids_str = data.get('hulls')
    ship_type = data.get('shipType', 'battleship')  # Default to battleship
    
    # Resolve the reference system (could be ID or name)
    reference_system_id = resolve_reference_system(system_input)
    
    # If we couldn't resolve the system, use the default
    if reference_system_id is None and system_input is not None:
        return jsonify({
            'error': f"Could not resolve system: {system_input}"
        }), 400
    
    # If a reference system ID is provided, update the config
    if reference_system_id:
        config.REFERENCE_SYSTEM_ID = reference_system_id
        # Get the system name from the ESI API
        esi_client = ESIClient()
        system_info = esi_client.get_system_info(reference_system_id)
        config.REFERENCE_SYSTEM_NAME = system_info.get('name', f'System {reference_system_id}')
    
    # If max_jumps is provided, update the config
    if max_jumps is not None:
        config.MAX_JUMPS = int(max_jumps)
        logger.info(f"Maximum jumps set to {config.MAX_JUMPS}")
    
    # Parse hull IDs if specified
    hull_ids = None
    if hull_ids_str:
        hull_ids = parse_hull_ids(hull_ids_str)
        if hull_ids is None:
            return jsonify({
                'error': f"Invalid hull IDs format: {hull_ids_str}"
            }), 400
        
        # Update the config with the selected hull IDs
        if ship_type == 'battleship':
            config.T1_BATTLESHIP_TYPE_IDS = hull_ids
            config.ALL_BATTLESHIP_TYPE_IDS = hull_ids
            logger.info(f"Using custom battleship hull type IDs: {hull_ids}")
        elif ship_type == 'cruiser':
            config.ALL_CRUISER_TYPE_IDS = hull_ids
            logger.info(f"Using custom cruiser hull type IDs: {hull_ids}")
        elif ship_type == 'command_ship':
            config.ALL_COMMAND_SHIP_TYPE_IDS = hull_ids
            logger.info(f"Using custom command ship hull type IDs: {hull_ids}")
    
    logger.info(f"Starting market scan for {config.REFERENCE_SYSTEM_NAME}...")
    
    # Create an enhanced market scanner with the reference system
    scanner = EnhancedMarketScanner(
        reference_system_id=config.REFERENCE_SYSTEM_ID,
        reference_system_name=config.REFERENCE_SYSTEM_NAME,
        use_everef=True  # Use EVERef market data for faster retrieval
    )
    
    # Find good deals
    good_deals = scanner.find_good_deals(ship_type=ship_type)
    
    # Save the deals to a JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"deals_{config.REFERENCE_SYSTEM_NAME.lower()}_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(good_deals, f, indent=2)
    
    logger.info(f"Saved deals to {filename}")
    
    return jsonify({
        'deals': good_deals,
        'reference_system': config.REFERENCE_SYSTEM_NAME,
        'max_jumps': config.MAX_JUMPS,
        'hull_ids': hull_ids,
        'ship_type': ship_type
    })

def run_web_server(host='0.0.0.0', port=5000, debug=False):
    """Run the web server."""
    logger.info(f"Starting EVE Online Market Bot web server on {host}:{port}...")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    run_web_server(debug=True)