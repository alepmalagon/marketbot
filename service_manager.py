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

class ServiceManager:
    """Manager for running the market bot as a background service."""
    
    def __init__(self):
        """Initialize the service manager."""
        self.scanner = MarketScanner()
        self.notification_manager = NotificationManager()
        self.running = False
        self.stop_event = threading.Event()
    
    def scan_for_deals(self):
        """Run a single scan for good deals."""
        try:
            logger.info("Starting market scan...")
            
            # Find good deals
            good_deals = self.scanner.find_good_deals()
            
            # Log the results
            if good_deals:
                logger.info(f"Found {len(good_deals)} good deals!")
                
                # Save the deals to a JSON file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"deals_{timestamp}.json"
                
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
        
        logger.info("Starting EVE Online Market Bot service...")
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


def run_as_daemon():
    """Run the service as a daemon process."""
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
    service = ServiceManager()
    service.start()


def run_in_foreground():
    """Run the service in the foreground."""
    service = ServiceManager()
    service.start()