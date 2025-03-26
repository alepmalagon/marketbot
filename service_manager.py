"""
Service manager for running the EVE Online Market Bot as a background process.
"""
import logging
import os
import signal
import sys
import time
from datetime import datetime
import json
import threading
import schedule

from market_scanner import MarketScanner
from notification_manager import NotificationManager
import config
from esi_client import ESIClient
from solar_system_data import load_solar_systems

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("marketbot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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

class ServiceManager:
    """Manager for running the market bot as a background service."""
    
    def __init__(self, reference_system=None):
        """
        Initialize the service manager.
        
        Args:
            reference_system: Optional system ID or name to use as reference
        """
        # Resolve the reference system (could be ID or name)
        reference_system_id = resolve_reference_system(reference_system)
        
        # If we couldn't resolve the system, use the default
        if reference_system_id is None and reference_system is not None:
            logger.warning(f"Could not resolve system: {reference_system}, using default system")
        
        # If a reference system ID is provided, update the config
        if reference_system_id:
            config.REFERENCE_SYSTEM_ID = reference_system_id
            # Get the system name from the ESI API
            esi_client = ESIClient()
            system_info = esi_client.get_system_info(reference_system_id)
            config.REFERENCE_SYSTEM_NAME = system_info.get('name', f'System {reference_system_id}')
        
        self.scanner = MarketScanner(
            reference_system_id=config.REFERENCE_SYSTEM_ID,
            reference_system_name=config.REFERENCE_SYSTEM_NAME
        )
        self.notification_manager = NotificationManager()
        self.running = False
        self.stop_event = threading.Event()
    
    def scan_for_deals(self):
        """Run a single scan for good deals."""
        try:
            logger.info(f"Starting market scan for {config.REFERENCE_SYSTEM_NAME}...")
            
            # Find good deals
            good_deals = self.scanner.find_good_deals()
            
            # Log the results
            if good_deals:
                logger.info(f"Found {len(good_deals)} good deals!")
                
                # Save the deals to a JSON file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"deals_{config.REFERENCE_SYSTEM_NAME.lower()}_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(good_deals, f, indent=2)
                
                logger.info(f"Saved deals to {filename}")
                
                # Send notifications
                self.notification_manager.send_deal_notifications(good_deals)
            else:
                logger.info("No good deals found.")
            
            logger.info("Market scan completed.")
        except Exception as e:
            logger.error(f"Error during market scan: {e}", exc_info=True)
    
    def start(self):
        """Start the service."""
        if self.running:
            logger.warning("Service is already running.")
            return
        
        logger.info(f"Starting EVE Online Market Bot service for {config.REFERENCE_SYSTEM_NAME}...")
        self.running = True
        
        # Run an initial scan
        self.scan_for_deals()
        
        # Schedule regular scans
        schedule.every(config.CHECK_INTERVAL_HOURS).hours.do(self.scan_for_deals)
        
        logger.info(f"Service scheduled to run every {config.CHECK_INTERVAL_HOURS} hours.")
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Main loop
        try:
            while self.running and not self.stop_event.is_set():
                schedule.run_pending()
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in main service loop: {e}", exc_info=True)
        finally:
            self.stop()
    
    def stop(self):
        """Stop the service."""
        if not self.running:
            return
        
        logger.info("Stopping EVE Online Market Bot service...")
        self.running = False
        self.stop_event.set()
        
        # Clear the schedule
        schedule.clear()
        
        logger.info("Service stopped.")
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        logger.info(f"Received signal {signum}. Shutting down...")
        self.stop()
        sys.exit(0)


def run_as_daemon(reference_system=None):
    """
    Run the service as a daemon process.
    
    Args:
        reference_system: Optional system ID or name to use as reference
    """
    try:
        # Create a child process
        pid = os.fork()
        if pid > 0:
            # Exit the parent process
            sys.exit(0)
    except OSError as e:
        logger.error(f"Fork failed: {e}")
        sys.exit(1)
    
    # Decouple from parent environment
    os.chdir('/')
    os.setsid()
    os.umask(0)
    
    try:
        # Fork a second time
        pid = os.fork()
        if pid > 0:
            # Exit from the second parent
            sys.exit(0)
    except OSError as e:
        logger.error(f"Second fork failed: {e}")
        sys.exit(1)
    
    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    
    with open('/dev/null', 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    
    with open('marketbot.log', 'a+') as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())
    
    # Write the PID file
    with open('marketbot.pid', 'w') as f:
        f.write(str(os.getpid()))
    
    # Start the service
    service = ServiceManager(reference_system)
    service.start()


def run_in_foreground(reference_system=None):
    """
    Run the service in the foreground.
    
    Args:
        reference_system: Optional system ID or name to use as reference
    """
    service = ServiceManager(reference_system)
    service.start()