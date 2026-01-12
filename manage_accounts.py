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
