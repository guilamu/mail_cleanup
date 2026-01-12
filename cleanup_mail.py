#!/usr/bin/env python3
import poplib
import json
import logging
import socket
import os
import sys
from pathlib import Path

# Setup logging - cross-platform: log file in script directory
SCRIPT_DIR = Path(__file__).parent
LOG_FILE = SCRIPT_DIR / 'mail_cleanup.log'

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# Connection timeout in seconds
CONNECTION_TIMEOUT = 60

def get_password(account):
    """Get password from account config or environment variable fallback.
    
    Environment variable format: MAIL_PASS_USER_DOMAIN_COM
    (email with @ and . replaced by _)
    """
    # Try environment variable first for security
    env_key = f"MAIL_PASS_{account['email'].replace('@', '_').replace('.', '_').upper()}"
    env_password = os.environ.get(env_key)
    if env_password:
        return env_password
    
    # Fall back to config file password
    return account.get('password')

def cleanup_account(account):
    """Delete all emails from a single POP3 account"""
    M = None
    try:
        logging.info(f"Processing account: {account['email']}")
        
        # Get password (env var or config)
        password = get_password(account)
        if not password:
            logging.error(f"{account['email']}: No password configured")
            return False, 0

        # Set socket timeout to prevent hanging
        socket.setdefaulttimeout(CONNECTION_TIMEOUT)
        
        # Connect to POP3 server
        logging.info(f"{account['email']}: Connecting to {account['server']}...")
        M = poplib.POP3_SSL(account['server'], account.get('port', 995))
        
        logging.info(f"{account['email']}: Connected. Authenticating...")
        M.user(account['email'])
        M.pass_(password)

        # Get message count
        logging.info(f"{account['email']}: Logged in. Listing messages...")
        numMessages = len(M.list()[1])
        logging.info(f"{account['email']}: Found {numMessages} messages")

        if numMessages > 0:
            # Delete all messages
            for i in range(numMessages):
                M.dele(i+1)
            logging.info(f"{account['email']}: Deleted {numMessages} messages")
        else:
            logging.info(f"{account['email']}: No messages to delete")

        # Quit to commit deletions
        M.quit()
        M = None  # Mark as properly closed
        return True, numMessages

    except socket.timeout:
        logging.error(f"{account['email']}: Connection timed out after {CONNECTION_TIMEOUT}s")
        return False, 0
    except Exception as e:
        logging.error(f"{account['email']}: Error - {e}")
        return False, 0
    finally:
        # Ensure connection is closed even on error
        if M is not None:
            try:
                M.quit()
            except Exception:
                pass  # Ignore errors during cleanup

def main():
    """Process all accounts from config file"""
    config_file = Path(__file__).parent / 'accounts.json'

    if not config_file.exists():
        logging.error(f"Config file not found: {config_file}")
        return

    # Load accounts
    with open(config_file, 'r') as f:
        config = json.load(f)

    accounts = config.get('accounts', [])

    if not accounts:
        logging.warning("No accounts configured")
        return

    logging.info(f"Starting cleanup for {len(accounts)} account(s)")

    # Process each account
    total_deleted = 0
    success_count = 0

    for account in accounts:
        if not account.get('enabled', True):
            logging.info(f"Skipping disabled account: {account['email']}")
            continue

        success, deleted = cleanup_account(account)
        if success:
            success_count += 1
            total_deleted += deleted

    logging.info(f"Cleanup completed: {success_count}/{len(accounts)} accounts processed, {total_deleted} total messages deleted")

if __name__ == '__main__':
    main()
