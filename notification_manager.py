"""
Notification manager for the EVE Online Market Bot.
"""
import logging
import os
import platform
from typing import Dict, List

from plyer import notification

import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NotificationManager:
    """Manager for sending system notifications about good deals."""
    
    def __init__(self):
        """Initialize the notification manager."""
        self.enabled = config.ENABLE_NOTIFICATIONS
        self.min_savings_percent = config.MIN_SAVINGS_PERCENT_FOR_NOTIFICATION
        self.max_notifications = config.MAX_NOTIFICATIONS
        self.sent_notifications = set()  # Keep track of notifications we've already sent
    
    def send_deal_notifications(self, deals: List[Dict]) -> None:
        """
        Send system notifications for good deals.
        
        Args:
            deals: List of good deals to potentially notify about
        """
        if not self.enabled:
            logger.info("Notifications are disabled. Skipping...")
            return
        
        if not deals:
            logger.info("No deals to notify about.")
            return
        
        # Filter deals by minimum savings percentage
        notable_deals = [
            deal for deal in deals 
            if deal.get('savings_percent', 0) >= self.min_savings_percent
        ]
        
        if not notable_deals:
            logger.info(f"No deals with savings percentage >= {self.min_savings_percent}%")
            return
        
        # Limit the number of notifications
        notable_deals = notable_deals[:self.max_notifications]
        
        # Send a notification for each deal
        for deal in notable_deals:
            # Create a unique identifier for this deal
            deal_id = f"{deal['type_id']}_{deal['system_id']}_{deal['price']}"
            
            # Skip if we've already notified about this deal
            if deal_id in self.sent_notifications:
                continue
            
            # Add to sent notifications
            self.sent_notifications.add(deal_id)
            
            # Format the notification
            title = f"EVE Market Deal: {deal['type_name']}"
            message = (
                f"Location: {deal['system_name']} ({deal['distance_to_sosala']} jumps from Sosala)\n"
                f"Price: {deal['price']:,.2f} ISK\n"
                f"Jita Price: {deal['jita_price']:,.2f} ISK\n"
                f"Savings: {deal['savings']:,.2f} ISK ({deal['savings_percent']:.2f}%)"
            )
            
            try:
                # Send the notification
                self._send_notification(title, message)
                logger.info(f"Sent notification for {deal['type_name']} in {deal['system_name']}")
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
    
    def _send_notification(self, title: str, message: str) -> None:
        """
        Send a system notification.
        
        Args:
            title: The notification title
            message: The notification message
        """
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="EVE Market Bot",
                timeout=10  # seconds
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            
            # Fallback for some platforms where plyer might not work
            if platform.system() == "Windows":
                try:
                    # Windows-specific fallback using PowerShell
                    os.system(f'powershell -command "New-BurntToastNotification -Text \'{title}\', \'{message}\'"')
                except Exception as e2:
                    logger.error(f"Windows fallback notification failed: {e2}")
            elif platform.system() == "Darwin":  # macOS
                try:
                    # macOS-specific fallback
                    os.system(f'osascript -e \'display notification "{message}" with title "{title}"\'')
                except Exception as e2:
                    logger.error(f"macOS fallback notification failed: {e2}")
            elif platform.system() == "Linux":
                try:
                    # Linux-specific fallback
                    os.system(f'notify-send "{title}" "{message}"')
                except Exception as e2:
                    logger.error(f"Linux fallback notification failed: {e2}")