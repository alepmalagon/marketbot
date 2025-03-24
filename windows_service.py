"""
Windows service wrapper for the EVE Online Market Bot.
"""
import logging
import os
import sys
import time
import servicemanager
import socket
import win32event
import win32service
import win32serviceutil

from service_manager import ServiceManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("marketbot_service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MarketBotService(win32serviceutil.ServiceFramework):
    """Windows service for the EVE Online Market Bot."""
    
    _svc_name_ = "EVEMarketBot"
    _svc_display_name_ = "EVE Online Market Bot"
    _svc_description_ = "Monitors EVE Online markets for good deals on T1 battleship hulls."
    
    def __init__(self, args):
        """Initialize the service."""
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.service_manager = None
        self.is_alive = True
    
    def SvcStop(self):
        """Stop the service."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        
        if self.service_manager:
            self.service_manager.stop()
        
        self.is_alive = False
    
    def SvcDoRun(self):
        """Run the service."""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        # Start the service manager
        self.service_manager = ServiceManager()
        
        # Run the service in a separate thread
        import threading
        service_thread = threading.Thread(target=self.service_manager.start)
        service_thread.daemon = True
        service_thread.start()
        
        # Wait for the stop event
        while self.is_alive:
            rc = win32event.WaitForSingleObject(self.stop_event, 5000)
            if rc == win32event.WAIT_OBJECT_0:
                break
        
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(MarketBotService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(MarketBotService)