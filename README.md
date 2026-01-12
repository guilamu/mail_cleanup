# Multi-Account Email Cleanup System

## Overview

This system automatically deletes emails from multiple POP3 accounts while preserving the ability to forward emails and send outbound mail. It's designed to work around Gmail disabling POP3 access by forwarding emails directly to Gmail, then cleaning up the source mailbox to prevent storage accumulation on MXroute servers.

## Problem Statement

- Gmail disabled POP3 access for email retrieval
- Solution: Forward emails directly to Gmail from MXroute
- Issue: Emails still accumulate on MXroute servers, consuming storage quota
- Requirement: Keep email accounts active for SMTP sending capabilities

## Solution Architecture

A Python-based cron job that:
1. Connects to multiple POP3 accounts via SSL
2. Deletes all messages from each enabled account
3. Logs all operations for monitoring
4. Runs automatically on a schedule (daily recommended)

## Files Structure

```
/opt/scripts/mail-cleanup/
├── cleanup_mail.py          # Main cleanup script
├── manage_accounts.py       # Interactive account management tool
├── accounts.json            # Configuration file (secured)
└── README.md               # This file
```

## Installation

### 1. Create Directory Structure

```bash
sudo mkdir -p /opt/scripts/mail-cleanup
cd /opt/scripts/mail-cleanup
```

### 2. Create Script Files

Create `cleanup_mail.py`:

```python
#!/usr/bin/env python3
import poplib
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    filename='/var/log/mail_cleanup.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def cleanup_account(account):
    """Delete all emails from a single POP3 account"""
    try:
        logging.info(f"Processing account: {account['email']}")

        # Connect to POP3 server
        M = poplib.POP3_SSL(account['server'], account.get('port', 995))
        M.user(account['email'])
        M.pass_(account['password'])

        # Get message count
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
        return True, numMessages

    except Exception as e:
        logging.error(f"{account['email']}: Error - {e}")
        return False, 0

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
```

Create `manage_accounts.py`:

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

CONFIG_FILE = Path(__file__).parent / 'accounts.json'

def load_config():
    """Load accounts configuration"""
    if not CONFIG_FILE.exists():
        return {"accounts": []}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """Save accounts configuration"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"✓ Configuration saved to {CONFIG_FILE}")

def list_accounts(config):
    """List all accounts"""
    accounts = config.get('accounts', [])
    if not accounts:
        print("No accounts configured.")
        return

    print(f"\n{'#':<3} {'Email':<35} {'Server':<25} {'Status':<10} Description")
    print("-" * 100)
    for i, acc in enumerate(accounts, 1):
        status = "✓ Enabled" if acc.get('enabled', True) else "✗ Disabled"
        desc = acc.get('description', '')
        print(f"{i:<3} {acc['email']:<35} {acc['server']:<25} {status:<10} {desc}")

def add_account():
    """Add a new account"""
    print("\n=== Add New Account ===")
    email = input("Email address: ").strip()
    password = input("Password: ").strip()
    server = input("POP3 server: ").strip()
    port = input("POP3 port [995]: ").strip() or "995"
    description = input("Description (optional): ").strip()

    config = load_config()
    config['accounts'].append({
        "email": email,
        "password": password,
        "server": server,
        "port": int(port),
        "enabled": True,
        "description": description
    })

    save_config(config)
    print(f"✓ Added account: {email}")

def remove_account():
    """Remove an account"""
    config = load_config()
    list_accounts(config)

    if not config.get('accounts'):
        return

    try:
        index = int(input("\nEnter account number to remove: ")) - 1
        if 0 <= index < len(config['accounts']):
            removed = config['accounts'].pop(index)
            save_config(config)
            print(f"✓ Removed account: {removed['email']}")
        else:
            print("✗ Invalid account number")
    except (ValueError, KeyError):
        print("✗ Invalid input")

def toggle_account():
    """Enable/disable an account"""
    config = load_config()
    list_accounts(config)

    if not config.get('accounts'):
        return

    try:
        index = int(input("\nEnter account number to enable/disable: ")) - 1
        if 0 <= index < len(config['accounts']):
            config['accounts'][index]['enabled'] = not config['accounts'][index].get('enabled', True)
            status = "enabled" if config['accounts'][index]['enabled'] else "disabled"
            save_config(config)
            print(f"✓ Account {config['accounts'][index]['email']} is now {status}")
        else:
            print("✗ Invalid account number")
    except (ValueError, KeyError):
        print("✗ Invalid input")

def main():
    """Main menu"""
    while True:
        print("\n=== Email Cleanup Account Manager ===")
        print("1. List accounts")
        print("2. Add account")
        print("3. Remove account")
        print("4. Enable/Disable account")
        print("5. Exit")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            config = load_config()
            list_accounts(config)
        elif choice == '2':
            add_account()
        elif choice == '3':
            remove_account()
        elif choice == '4':
            toggle_account()
        elif choice == '5':
            print("Goodbye!")
            break
        else:
            print("✗ Invalid option")

if __name__ == '__main__':
    main()
```

### 3. Set Permissions

```bash
chmod 700 cleanup_mail.py manage_accounts.py
chmod 600 accounts.json  # After creating it
```

### 4. Create Initial Configuration

Create `accounts.json` with initial structure:

```json
{
  "accounts": []
}
```

Or use the management tool to add your first account:

```bash
python3 manage_accounts.py
```

### 5. Setup Log File

```bash
sudo touch /var/log/mail_cleanup.log
sudo chown $USER:$USER /var/log/mail_cleanup.log
sudo chmod 644 /var/log/mail_cleanup.log
```

### 6. Configure Log Rotation

Create `/etc/logrotate.d/mail_cleanup`:

```bash
/var/log/mail_cleanup.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

## Account Management

### Adding an Account

```bash
python3 manage_accounts.py
# Select option 2 (Add account)
# Follow the prompts
```

Example input:
```
Email address: fnecfp@fo-fnecfp.fr
Password: your_secure_password
POP3 server: mail.yourdomain.com
POP3 port [995]: 995
Description (optional): Main union account
```

### Listing Accounts

```bash
python3 manage_accounts.py
# Select option 1 (List accounts)
```

Output example:
```
#   Email                               Server                    Status     Description
----------------------------------------------------------------------------------------------------
1   fnecfp@fo-fnecfp.fr                 mail.yourdomain.com       ✓ Enabled  Main union account
2   contact@example.com                 mail.example.com          ✗ Disabled Contact form
```

### Removing an Account

```bash
python3 manage_accounts.py
# Select option 3 (Remove account)
# Enter the account number to remove
```

### Temporarily Disabling an Account

```bash
python3 manage_accounts.py
# Select option 4 (Enable/Disable account)
# Enter the account number to toggle
```

This is useful for:
- Testing the system with specific accounts
- Temporarily preserving emails on one account
- Troubleshooting connection issues

## Scheduling with Cron

### Setup Cron Job

Edit your crontab:

```bash
crontab -e
```

Add this line to run daily at 2:00 AM:

```cron
0 2 * * * /usr/bin/python3 /opt/scripts/mail-cleanup/cleanup_mail.py >> /var/log/mail_cleanup.log 2>&1
```

### Cron Schedule Options

- **Daily at 2 AM**: `0 2 * * *`
- **Every 6 hours**: `0 */6 * * *`
- **Twice daily (2 AM and 2 PM)**: `0 2,14 * * *`
- **Every hour**: `0 * * * *`

### Verify Cron Job

```bash
# List current cron jobs
crontab -l

# Check cron logs
grep CRON /var/log/syslog | tail -20
```

## Manual Testing

Before setting up cron, test the script manually:

```bash
cd /opt/scripts/mail-cleanup
python3 cleanup_mail.py
```

Check the log output:

```bash
tail -f /var/log/mail_cleanup.log
```

## Configuration File Format

The `accounts.json` file structure:

```json
{
  "accounts": [
    {
      "email": "user@domain.com",
      "password": "secure_password",
      "server": "mail.domain.com",
      "port": 995,
      "enabled": true,
      "description": "Optional description"
    }
  ]
}
```

### Field Descriptions

- **email** (required): Full email address
- **password** (required): Email account password
- **server** (required): POP3 server hostname
- **port** (optional): POP3 SSL port, defaults to 995
- **enabled** (optional): Boolean flag, defaults to true
- **description** (optional): Human-readable description

## Security Considerations

### File Permissions

The `accounts.json` file contains plaintext passwords and MUST be secured:

```bash
chmod 600 accounts.json
```

This ensures only the owner can read/write the file.

### Alternative: Environment Variables

For enhanced security, modify the script to read from environment variables:

```python
import os

# In cleanup_account function, allow env var override:
password = account.get('password') or os.environ.get(f"MAIL_PASS_{account['email'].replace('@', '_').replace('.', '_').upper()}")
```

### Server Security

- Store scripts in `/opt/scripts/` with restricted permissions
- Use a dedicated user account for running the cron job
- Consider using a secrets manager (Vault, AWS Secrets Manager)
- Audit `/var/log/mail_cleanup.log` permissions

## Monitoring and Logs

### Log Format

Each log entry includes:
- Timestamp
- Log level (INFO, ERROR)
- Message content

Example log output:

```
2026-01-12 02:00:01 - INFO - Starting cleanup for 3 account(s)
2026-01-12 02:00:01 - INFO - Processing account: fnecfp@fo-fnecfp.fr
2026-01-12 02:00:02 - INFO - fnecfp@fo-fnecfp.fr: Found 15 messages
2026-01-12 02:00:03 - INFO - fnecfp@fo-fnecfp.fr: Deleted 15 messages
2026-01-12 02:00:03 - INFO - Skipping disabled account: test@example.com
2026-01-12 02:00:03 - INFO - Processing account: contact@domain.com
2026-01-12 02:00:04 - INFO - contact@domain.com: Found 0 messages
2026-01-12 02:00:04 - INFO - contact@domain.com: No messages to delete
2026-01-12 02:00:04 - INFO - Cleanup completed: 2/3 accounts processed, 15 total messages deleted
```

### Monitoring Commands

```bash
# View recent logs
tail -50 /var/log/mail_cleanup.log

# Follow logs in real-time
tail -f /var/log/mail_cleanup.log

# Search for errors
grep ERROR /var/log/mail_cleanup.log

# Count deleted messages today
grep "$(date +%Y-%m-%d)" /var/log/mail_cleanup.log | grep "Deleted"

# View last cleanup summary
grep "Cleanup completed" /var/log/mail_cleanup.log | tail -1
```

## Troubleshooting

### Connection Errors

**Error**: `poplib.error_proto: -ERR Authentication failed`

**Solutions**:
- Verify email and password in `accounts.json`
- Confirm POP3 is enabled on the mail server
- Check server hostname is correct
- Verify port 995 is open (POP3 SSL)

### Permission Errors

**Error**: `Permission denied: '/var/log/mail_cleanup.log'`

**Solution**:
```bash
sudo chown $USER:$USER /var/log/mail_cleanup.log
sudo chmod 644 /var/log/mail_cleanup.log
```

### Cron Not Running

**Issue**: Script doesn't run automatically

**Debug**:
```bash
# Check cron service status
sudo systemctl status cron

# Check user crontab
crontab -l

# Check cron logs
grep CRON /var/log/syslog

# Test with absolute paths
/usr/bin/python3 /opt/scripts/mail-cleanup/cleanup_mail.py
```

**Common cron issues**:
- Missing absolute paths to python or script
- Incorrect working directory
- Environment variables not set
- Script not executable

### SSL Certificate Errors

**Error**: `ssl.SSLError: certificate verify failed`

**Solution**: Update system certificates:
```bash
sudo apt-get update
sudo apt-get install --reinstall ca-certificates
```

### Config File Not Found

**Error**: `Config file not found: accounts.json`

**Solution**: Ensure `accounts.json` exists in the same directory as the script:
```bash
cd /opt/scripts/mail-cleanup
ls -la accounts.json
```

## Architecture Decisions

### Why POP3 Instead of IMAP?

- **Simplicity**: POP3 is straightforward for delete-all operations
- **Lightweight**: Minimal protocol overhead
- **Compatibility**: Universal support on email servers
- **No folder management**: IMAP requires folder navigation

### Why JSON for Configuration?

- **Human-readable**: Easy to edit manually if needed
- **Standard library**: No external dependencies
- **Flexible**: Easy to add new fields
- **Structured**: Better than .env for multiple accounts

### Why Not Use Email Filters?

MXroute/cPanel filters have limitations:
- Forwarding creates local copies before filtering
- Cannot selectively delete after forwarding
- Less flexible than scripting

## Alternative Implementations

### GitHub Actions Version

For teams without dedicated servers, see: [GitHub Actions Implementation](#github-actions-alternative)

### Docker Container Version

For containerized environments:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY cleanup_mail.py accounts.json ./
CMD ["python", "cleanup_mail.py"]
```

Run with cron or Kubernetes CronJob.

## System Requirements

- **Python**: 3.6 or higher (poplib is built-in)
- **OS**: Linux/Unix with cron (Debian, Ubuntu, CentOS, etc.)
- **Network**: Outbound access to POP3 servers on port 995
- **Permissions**: Write access to log directory

## Performance Considerations

- **Execution time**: ~1-2 seconds per account with 0 messages
- **Network**: ~5-10 seconds per account with 100+ messages
- **Batch size**: No built-in limit, processes all accounts sequentially
- **Memory**: Minimal (~10MB per account)

For large deployments (100+ accounts), consider:
- Parallel processing with multiprocessing
- Separate cron jobs per account group
- Rate limiting to avoid server throttling

## License

This system is provided as-is for personal/organizational use.

## Support and Maintenance

Created: January 2026
Last Updated: January 12, 2026

For issues or questions, review the Troubleshooting section above.

## Appendix: GitHub Actions Alternative

If you prefer cloud-based automation without managing servers:

### Workflow File (.github/workflows/cleanup.yml)

```yaml
name: Clean Email Mailbox

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  cleanup:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Run cleanup script
      env:
        ACCOUNTS_JSON: ${{ secrets.ACCOUNTS_JSON }}
      run: |
        echo "$ACCOUNTS_JSON" > accounts.json
        python cleanup_mail.py
```

Store the entire `accounts.json` content as a GitHub Secret named `ACCOUNTS_JSON`.

**Pros**: No server maintenance, free tier available
**Cons**: Credentials stored in GitHub, less control, scheduling delays

## Quick Start Summary

```bash
# 1. Create directory
sudo mkdir -p /opt/scripts/mail-cleanup
cd /opt/scripts/mail-cleanup

# 2. Create the three files (cleanup_mail.py, manage_accounts.py, accounts.json)

# 3. Set permissions
chmod 700 *.py
chmod 600 accounts.json

# 4. Add your first account
python3 manage_accounts.py

# 5. Test manually
python3 cleanup_mail.py

# 6. Check logs
tail /var/log/mail_cleanup.log

# 7. Setup cron
crontab -e
# Add: 0 2 * * * /usr/bin/python3 /opt/scripts/mail-cleanup/cleanup_mail.py >> /var/log/mail_cleanup.log 2>&1

# 8. Monitor
tail -f /var/log/mail_cleanup.log
```

---

**End of Documentation**
