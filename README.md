# IP Checker

A Python script to monitor your external IP address and send an email notification if it changes.

## Features
- Automatically checks your external IP using [ipify.org](https://www.ipify.org/).
- Sends an email notification via SMTP if the IP address changes.
- Creates a default `config.txt` file with placeholders for email configuration.
- Installs required Python modules automatically if missing.

## Requirements
- Python 3.x
- Required modules: `requests`, `configparser` (installed automatically if missing).

## Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/IP-Checker.git
   cd IP-Checker
   ```
2. Edit `config.txt` with your SMTP server details and email addresses.
3. Run the script:
   ```bash
   python3 IPchecker.py
   ```

## Configuration
Edit `config.txt` with the following details:
```
[Email]
smtp_server = your_smtp_server_address
smtp_port = your_smtp_port_number
smtp_username = your_email_username
smtp_password = your_email_password
sender_email = your_email_address
recipient_email = recipient1@example.com, recipient2@example.com
```

## Usage
Run the script manually or schedule it as a cron job to check for IP changes periodically.
