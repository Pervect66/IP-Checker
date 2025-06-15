#!/usr/bin/env python3
"""
IP Checker - Monitor external IP address changes and send notifications

This script checks for changes in the external IP address and sends email
notifications when changes are detected.
"""

import os
import subprocess
import importlib.util
import sys
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_CONFIG_FILE = 'config.txt'
DEFAULT_IP_FILE = 'external_ip.txt'
IP_SERVICE_URL = 'https://api.ipify.org?format=json'
REQUIRED_MODULES = {'requests': 'requests'}


def check_install_modules() -> None:
    """Check and install required modules if missing."""
    for package, module in REQUIRED_MODULES.items():
        if importlib.util.find_spec(module) is None:
            logger.info(f"{package} not found. Installing...")
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                logger.info(f"{package} installed successfully.")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {package}: {e}")
                sys.exit(1)


check_install_modules()

import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser

class ConfigManager:
    """Handles configuration file operations."""
    
    def __init__(self, config_file: str = DEFAULT_CONFIG_FILE):
        self.config_file = Path(config_file)
        self.config = configparser.ConfigParser()
    
    def read_config(self) -> Dict[str, Any]:
        """Read configuration from file or create it with defaults."""
        if not self.config_file.exists():
            self._create_default_config()
        
        self.config.read(self.config_file)
        if 'Email' not in self.config:
            raise ValueError("Invalid config file: 'Email' section missing")
        
        return dict(self.config['Email'])
    
    def _create_default_config(self) -> None:
        """Create configuration file with default placeholders."""
        self.config['Email'] = {
            'smtp_server': 'your_smtp_server_address',
            'smtp_port': '587',
            'smtp_username': 'your_email_username',
            'smtp_password': 'your_email_password',
            'sender_email': 'your_email_address',
            'recipient_email': 'recipient1@example.com, recipient2@example.com'
        }
        
        with open(self.config_file, 'w') as config_file:
            self.config.write(config_file)
        
        logger.info(f"{self.config_file} created with default placeholders.")

class IPChecker:
    """Handles IP address checking and storage operations."""
    
    def __init__(self, ip_file: str = DEFAULT_IP_FILE):
        self.ip_file = Path(ip_file)
    
    def get_external_ip(self) -> Optional[str]:
        """Fetch external IP address from API service."""
        try:
            response = requests.get(IP_SERVICE_URL, timeout=10)
            response.raise_for_status()
            ip_data = response.json()
            return ip_data.get('ip')
        except requests.RequestException as e:
            logger.error(f"Failed to retrieve IP: {e}")
            return None
    
    def read_stored_ip(self) -> Optional[str]:
        """Read the stored IP address from file."""
        if self.ip_file.exists():
            try:
                return self.ip_file.read_text().strip()
            except IOError as e:
                logger.error(f"Failed to read stored IP: {e}")
        return None
    
    def write_ip_to_file(self, ip_address: str) -> None:
        """Write IP address to storage file."""
        try:
            self.ip_file.write_text(ip_address)
        except IOError as e:
            logger.error(f"Failed to write IP to file: {e}")


class EmailNotifier:
    """Handles email notifications for IP changes."""
    
    def __init__(self, config: Dict[str, Any]):
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = self._parse_port(config.get('smtp_port'))
        self.smtp_username = config.get('smtp_username')
        self.smtp_password = config.get('smtp_password')
        self.sender_email = config.get('sender_email')
        self.recipient_emails = self._parse_recipients(config.get('recipient_email', ''))
    
    def _parse_port(self, port_str: str) -> Optional[int]:
        """Parse SMTP port from string to integer."""
        try:
            return int(port_str) if port_str else None
        except ValueError:
            logger.error(f"Invalid SMTP port: {port_str}")
            return None
    
    def _parse_recipients(self, recipients_str: str) -> List[str]:
        """Parse recipient emails from comma-separated string."""
        return [email.strip() for email in recipients_str.split(',') if email.strip()]
    
    def is_valid_config(self) -> bool:
        """Check if email configuration is valid."""
        return all([
            self.smtp_server,
            self.smtp_port,
            self.smtp_username,
            self.smtp_password,
            self.sender_email,
            self.recipient_emails
        ])
    
    def send_notification(self, old_ip: str, new_ip: str) -> bool:
        """Send email notification about IP change."""
        if not self.is_valid_config():
            logger.warning("Invalid email configuration, skipping email notification")
            return False
        
        subject = 'IP Address Change Notification'
        body = f"The external IP address has changed from {old_ip} to {new_ip}"
        
        try:
            message = MIMEMultipart()
            message['From'] = self.sender_email
            message['To'] = ', '.join(self.recipient_emails)
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, self.recipient_emails, message.as_string())
            
            logger.info("Email notification sent successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

def main() -> None:
    """Main function to check and compare IP addresses."""
    try:
        # Initialize components
        config_manager = ConfigManager()
        ip_checker = IPChecker()
        
        # Read configuration
        try:
            config = config_manager.read_config()
        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Configuration error: {e}")
            logger.info("Please configure config.txt with your email settings.")
            return
        
        email_notifier = EmailNotifier(config)
        
        # Get current external IP
        current_ip = ip_checker.get_external_ip()
        if not current_ip:
            logger.error("Failed to retrieve current IP address")
            return
        
        # Compare with stored IP
        stored_ip = ip_checker.read_stored_ip()
        
        if stored_ip is None:
            # First run - store IP without notification
            ip_checker.write_ip_to_file(current_ip)
            logger.info(f"Initial IP address stored: {current_ip}")
        elif current_ip != stored_ip:
            # IP has changed - update storage and send notification
            ip_checker.write_ip_to_file(current_ip)
            logger.info(f"IP address changed from {stored_ip} to {current_ip}")
            
            # Send notification
            if email_notifier.is_valid_config():
                email_notifier.send_notification(stored_ip, current_ip)
            else:
                logger.warning(f"IP Address Change: {stored_ip} -> {current_ip}")
        else:
            logger.info(f"IP address unchanged: {current_ip}")
    
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
