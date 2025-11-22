#!/usr/bin/env python3
"""
Migrate channel data from config.json to PostgreSQL database.

This script:
1. Reads config.json
2. For each account and its channels:
   - Ensures account exists in database
   - Creates channel records
   - Links channels to accounts
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path (2 levels up from scripts/migration/)
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from src.database.models import Account, Channel
from src.database.connection import db


def extract_channel_id_from_url(url: str) -> Optional[str]:
    """Extract channel ID from YouTube channel URL."""
    if not url:
        return None
    
    # Extract channel ID from /channel/UCxxxxxx format
    match = re.search(r'/channel/([^/?]+)', url)
    if match:
        return match.group(1)
    
    # For @username or /c/ format, return the identifier
    match = re.search(r'/@([^/?]+)', url)
    if match:
        return match.group(1)
    
    match = re.search(r'/c/([^/?]+)', url)
    if match:
        return match.group(1)
    
    return None


def load_config() -> Dict[str, Any]:
    """Load config.json file."""
    config_path = Path.cwd() / "config.json"
    
    if not config_path.exists():
        print(f"❌ Error: config.json not found at {config_path}")
        print("   Make sure you're running this from the project root directory")
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error reading config.json: {e}")
        sys.exit(1)


def ensure_account_exists(account_name: str, cookies_file: str, session) -> Account:
    """Ensure account exists in database, create if not."""
    account = session.query(Account).filter(Account.name == account_name).first()
    
    if not account:
        account = Account(
            name=account_name,
            cookies_file=cookies_file
        )
        session.add(account)
        session.flush()
        print(f"  ✓ Created account: {account_name}")
    else:
        print(f"  ✓ Account exists: {account_name}")
    
    return account


def import_channels_for_account(account: Account, channels_data: List[Dict], session) -> int:
    """Import channels for an account."""
    imported_count = 0
    
    for channel_data in channels_data:
        channel_url = channel_data.get('url')
        if not channel_url:
            print(f"    ⚠ Skipped channel with no URL")
            continue
        
        # Check if channel already exists
        existing_channel = session.query(Channel).filter(
            Channel.account_id == account.id,
            Channel.url == channel_url
        ).first()
        
        if existing_channel:
            print(f"    ℹ Channel already exists: {channel_url}")
            continue
        
        # Extract channel ID
        channel_id = extract_channel_id_from_url(channel_url)
        
        # Create new channel
        channel = Channel(
            account_id=account.id,
            url=channel_url,
            channel_id=channel_id
        )
        session.add(channel)
        imported_count += 1
        print(f"    ✓ Imported channel: {channel_url}")
        print(f"      - Channel ID: {channel_id}")
        print(f"      - Videos: {len(channel_data.get('video_ids', []))}")
    
    return imported_count


def main():
    """Main migration function."""
    print("=" * 70)
    print("📺 Channel Data Migration: config.json → PostgreSQL")
    print("=" * 70)
    
    # Load config.json
    print("\n📄 Loading config.json...")
    config = load_config()
    
    accounts = config.get('accounts', [])
    if not accounts:
        print("⚠ No accounts found in config.json")
        return
    
    print(f"✓ Found {len(accounts)} account(s) in config.json")
    
    # Check database connection
    print("\n🔌 Checking database connection...")
    try:
        if db.health_check():
            print("  ✓ Database connection OK")
        else:
            print("  ❌ Database connection failed")
            print("\n💡 Make sure:")
            print("  1. PostgreSQL is running")
            print("  2. Database 'youtube_analytics' exists")
            print("  3. .env file has correct credentials")
            return
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return
    
    # Import channels
    print("\n📊 Importing channels...")
    total_channels_imported = 0
    total_channels_existing = 0
    
    with db.session_scope() as session:
        for account_data in accounts:
            account_name = account_data.get('name')
            cookies_file = account_data.get('cookies_file')
            channels_data = account_data.get('channels', [])
            
            print(f"\n👤 Account: {account_name}")
            print(f"   Cookies: {cookies_file}")
            print(f"   Channels in config: {len(channels_data)}")
            
            # Ensure account exists
            account = ensure_account_exists(account_name, cookies_file, session)
            
            # Import channels
            if channels_data:
                imported = import_channels_for_account(account, channels_data, session)
                total_channels_imported += imported
                total_channels_existing += (len(channels_data) - imported)
            else:
                print("    ⚠ No channels to import")
        
        # Commit all changes
        session.commit()
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 MIGRATION SUMMARY")
    print("=" * 70)
    print(f"Accounts processed:     {len(accounts)}")
    print(f"✓ Channels imported:    {total_channels_imported}")
    print(f"ℹ Channels existing:    {total_channels_existing}")
    print(f"Total channels in DB:   {total_channels_imported + total_channels_existing}")
    print("=" * 70)
    
    if total_channels_imported > 0:
        print("\n✅ Migration completed successfully!")
        print("\n💡 Next steps:")
        print("  1. Verify channels: curl http://localhost:8000/channels")
        print("  2. Check by account: curl 'http://localhost:8000/channels?account_id=1'")
        print("  3. View in API docs: http://localhost:8000/docs")
    else:
        print("\n✅ All channels already exist in database!")
        print("   No new channels were imported.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Migration cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
