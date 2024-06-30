#!/usr/bin/env python3
import os
import subprocess
import importlib.util
import sys

# List of required modules and their import names
required_modules = {
    'requests': 'requests',
    'configparser': 'configparser',
}

# Function to check and install required modules
def check_install_modules():
    for package, module in required_modules.items():
        if importlib.util.find_spec(module) is None:
            print(f"{package} not found. Installing...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"{package} installed successfully.")

check_install_modules()

import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser

# Function to read configuration from config.txt or create it with default values
def read_config(file_name='config.txt'):
    if not os.path.exists(file_name):
        create_config(file_name)
    
    config = configparser.ConfigParser()
    config.read(file_name)
    return config['Email']

# Function to create config.txt with default placeholders
def create_config(file_name):
    config = configparser.ConfigParser()
    config['Email'] = {
        'smtp_server': 'your_smtp_server_address',
        'smtp_port': 'your_smtp_port_number',
        'smtp_username': 'your_email_username',
        'smtp_password': 'your_email_password',
        'sender_email': 'your_email_address',
        'recipient_email': 'recipient1@example.com, recipient2@example.com'
    }
    
    with open(file_name, 'w') as config_file:
        config.write(config_file)
    
    print(f"{file_name} created with default placeholders.")

# Function to fetch external IP address using https://api.ipify.org
def get_external_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()
        ip_data = response.json()
        return ip_data['ip']
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None

# Function to read the stored IP from file if exists
def read_stored_ip(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            return file.read().strip()
    return None

# Function to write the current IP to file
def write_ip_to_file(file_name, ip_address):
    with open(file_name, 'w') as file:
        file.write(ip_address)

# Function to send email notification
def send_email(smtp_server, smtp_port, smtp_username, smtp_password, sender_email, recipient_emails, subject, body):
    try:
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = ', '.join(recipient_emails)
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_emails, message.as_string())
        
        print("Email sent.")
    except Exception as e:
        print(f"Error in email config: {e}")

# Main function to check and compare IPs
def main():
    # Check and install required modules
    check_install_modules()

    # Read email configuration from config.txt
    config_file = 'config.txt'
    config = read_config(config_file)
    smtp_server = config.get('smtp_server')
    smtp_port = config.get('smtp_port')
    smtp_username = config.get('smtp_username')
    smtp_password = config.get('smtp_password')
    sender_email = config.get('sender_email')
    recipient_emails = [email.strip() for email in config.get('recipient_email', '').split(',')]

    # Debugging statements for email configuration
    print(f"smtp_server: {smtp_server}")
    print(f"smtp_port: {smtp_port}")
    print(f"smtp_username: {smtp_username}")
    print(f"sender_email: {sender_email}")
    print(f"recipient_emails: {recipient_emails}")

    # Check if smtp_port is a valid integer
    try:
        smtp_port = int(smtp_port)
    except ValueError:
        smtp_port = None
        print("SMTP port is not a valid integer.")

    valid_email_config = all([smtp_server, smtp_port, smtp_username, smtp_password, sender_email, recipient_emails])
    
    # Attempt to get external IP from https://api.ipify.org
    current_ip = get_external_ip()
    
    if not current_ip:
        print("Failed to retrieve IP. Exiting...")
        return
    
    # Compare current IP with stored IP
    stored_ip_file = 'external_ip.txt'
    stored_ip = read_stored_ip(stored_ip_file)
    
    if stored_ip is None or current_ip != stored_ip:
        # Update the stored IP with the current one
        write_ip_to_file(stored_ip_file, current_ip)
        
        # Send email notification if IP has changed and email config is valid
        if stored_ip is not None:
            subject = 'IP Address Change Notification'
            body = f"The external IP address has changed from {stored_ip} to {current_ip}"
            if valid_email_config:
                send_email(smtp_server, smtp_port, smtp_username, smtp_password, sender_email, recipient_emails, subject, body)
            else:
                print(f"{subject}\n{body}")
        else:
            print("Stored IP is None, no email sent.")
    else:
        print(f"IP has not changed: {current_ip}")

if __name__ == "__main__":
    main()
