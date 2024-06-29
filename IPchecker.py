import os
import subprocess
import importlib.util
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import configparser

# Function to check and install required modules
def check_install_modules():
    required_modules = ['requests', 'configparser']
    installed_modules = []

    for module in required_modules:
        try:
            __import__(module)
            installed_modules.append(module)
        except ImportError:
            print(f"{module} not found. Installing...")
            subprocess.check_call(['pip', 'install', module])
            installed_modules.append(module)
            print(f"{module} installed successfully.")

    return installed_modules

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

# Function to create IP_check_servers.txt with default servers if it doesn't exist
def create_default_servers(file_name):
    default_servers = [
        'https://api64.ipify.org?format=json',
        'https://ipinfo.io/json',
        'https://ifconfig.co/json',
        'https://api.ipify.org?format=json',
        'https://checkip.amazonaws.com/',
        'https://api.myip.com/',
        'https://api.ipify.org/?format=json',
        'https://ifconfig.me/all.json',
        'https://bot.whatismyipaddress.com/',
        'https://api6.ipify.org?format=json',
        'https://icanhazip.com/json',
        'https://ipapi.co/json',
        'https://myexternalip.com/json',
        'https://ip.seeip.org/json',
        'https://ifconfig.io/json',
        'https://api.ident.me/json',
        'https://ip-api.com/json'
    ]
    
    with open(file_name, 'w') as file:
        file.write('\n'.join(default_servers))
    
    print(f"{file_name} created with default servers.")
    
    return default_servers

# Function to read the list of servers from file
def read_servers_from_file(file_name):
    if not os.path.exists(file_name):
        return create_default_servers(file_name)
    
    with open(file_name, 'r') as file:
        servers = [server.strip() for server in file if server.strip()]
    return servers

# Function to write the list of servers to file
def write_servers_to_file(file_name, servers):
    with open(file_name, 'w') as file:
        file.write('\n'.join(servers))

# Function to fetch external IP address using a server
def get_external_ip(server):
    try:
        response = requests.get(server)
        response.raise_for_status()
        return response.json().get('ip')
    except requests.RequestException as e:
        print(f"Error fetching IP address from {server}: {e}")
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
        
        print("Email notification sent successfully.")
    except Exception as e:
        print(f"Failed to send email notification: {e}")

# Main function to check and compare IPs
def main():
    # Check and install required modules
    check_install_modules()

    # Read email configuration from config.txt
    config_file = 'config.txt'
    config = read_config(config_file)
    smtp_server = config['smtp_server']
    smtp_port = int(config['smtp_port'])
    smtp_username = config['smtp_username']
    smtp_password = config['smtp_password']
    sender_email = config['sender_email']
    recipient_emails = [email.strip() for email in config['recipient_email'].split(',')]
    
    # Read the list of servers from file or create with default servers if not exist
    servers_file = 'IP_check_servers.txt'
    servers = read_servers_from_file(servers_file)
    
    # Attempt to get external IP from the list of servers
    current_ip = None
    for server in servers:
        current_ip = get_external_ip(server)
        if current_ip:
            break
    
    if not current_ip:
        print("Failed to retrieve IP from all servers. Exiting...")
        return
    
    # Compare current IP with stored IP
    stored_ip_file = 'external_ip.txt'
    stored_ip = read_stored_ip(stored_ip_file)
    
    if stored_ip is None or current_ip != stored_ip:
        # Update the stored IP with the current one
        write_ip_to_file(stored_ip_file, current_ip)
        
        # Send email notification if IP has changed
        if stored_ip is not None:
            subject = 'IP Address Change Notification'
            body = f"The external IP address has changed from {stored_ip} to {current_ip}"
            send_email(smtp_server, smtp_port, smtp_username, smtp_password, sender_email, recipient_emails, subject, body)
    else:
        print(f"IP same from {server}")

if __name__ == "__main__":
    main()
