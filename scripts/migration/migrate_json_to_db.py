#!/usr/bin/env python3
"""
Migrate existing JSON analytics data to PostgreSQL database.

This script:
1. Finds all analytics_results_*.json files
2. Imports them into the database
3. Creates accounts if they don't exist
4. Preserves all historical data
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path (2 levels up from scripts/migration/)
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from src.database.writers import db_writer
from src.database.models import Account
from src.database.connection import db


def find_analytics_json_files() -> List[Path]:
    """Find all analytics_results_*.json files in the data/archive directory."""
    # Use project_root defined at module level
    archive_dir = project_root / "data" / "archive"
    if not archive_dir.exists():
        print(f"⚠ Archive directory not found: {archive_dir}")
        return []
        
    json_files = list(archive_dir.glob("analytics_results_*.json"))
    return sorted(json_files)


def extract_account_name_from_filename(filename: str) -> str:
    """Extract account name from filename like 'analytics_results_Beau.json'."""
    # Remove 'analytics_results_' prefix and '.json' suffix
    name = filename.replace("analytics_results_", "").replace(".json", "")
    return name


def ensure_account_exists(account_name: str, cookies_file: str = None) -> None:
    """Ensure account exists in database, create if not."""
    with db.session_scope() as session:
        account = session.query(Account).filter(Account.name == account_name).first()
        if not account:
            # Try to find cookies file
            if not cookies_file:
                cookies_file = f"data/cookies/profile/youtube_cookies_{account_name}.json"
                if not os.path.exists(cookies_file):
                    cookies_file = f"data/cookies/profile/youtube_cookies_{account_name.replace(' ', '_')}.json"
            
            account = Account(
                name=account_name,
                cookies_file=cookies_file if os.path.exists(cookies_file) else None
            )
            session.add(account)
            session.commit()
            print(f"  ✓ Created account: {account_name}")
        else:
            print(f"  ✓ Account exists: {account_name}")


def import_json_file(json_file: Path) -> Dict[str, int]:
    """Import a single JSON file into the database."""
    print(f"\n📄 Processing: {json_file.name}")
    
    # Extract account name from filename
    account_name = extract_account_name_from_filename(json_file.name)
    print(f"  Account: {account_name}")
    
    # Load JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  ✗ Error reading file: {e}")
        return {"success": 0, "errors": 0, "skipped": 0}
    
    if not isinstance(data, list):
        print(f"  ✗ Invalid format: expected list, got {type(data)}")
        return {"success": 0, "errors": 0, "skipped": 0}
    
    print(f"  Found {len(data)} video records")
    
    # Ensure account exists
    ensure_account_exists(account_name)
    
    # Import each video's analytics
    stats = {"success": 0, "errors": 0, "skipped": 0}
    
    for idx, video_data in enumerate(data, 1):
        video_id = video_data.get('video_id')
        
        if not video_id:
            print(f"    [{idx}/{len(data)}] ⚠ Skipped: no video_id")
            stats["skipped"] += 1
            continue
        
        # Skip if there's an error in the data
        if 'error' in video_data:
            print(f"    [{idx}/{len(data)}] ⚠ Skipped {video_id}: has error")
            stats["skipped"] += 1
            continue
        
        try:
            # Save to database
            db_writer.save_analytics(
                video_id=video_id,
                account_name=account_name,
                analytics_data=video_data
            )
            print(f"    [{idx}/{len(data)}] ✓ Imported {video_id}")
            stats["success"] += 1
            
        except Exception as e:
            print(f"    [{idx}/{len(data)}] ✗ Error importing {video_id}: {e}")
            stats["errors"] += 1
    
    return stats


def main():
    """Main migration function."""
    print("=" * 70)
    print("📊 YouTube Analytics JSON to Database Migration")
    print("=" * 70)
    
    # Find all JSON files
    json_files = find_analytics_json_files()
    
    if not json_files:
        print("\n⚠ No analytics_results_*.json files found in current directory")
        print("   Make sure you're running this from the project root directory")
        return
    
    print(f"\n✓ Found {len(json_files)} JSON file(s):")
    for f in json_files:
        print(f"  - {f.name}")
    
    # Check database connection
    print("\n🔌 Checking database connection...")
    try:
        if db.health_check():
            print("  ✓ Database connection OK")
        else:
            print("  ✗ Database connection failed")
            print("\n💡 Make sure:")
            print("  1. PostgreSQL is running")
            print("  2. Database 'youtube_analytics' exists")
            print("  3. .env file has correct credentials")
            print("  4. API server is running (or database is accessible)")
            return
    except Exception as e:
        print(f"  ✗ Database error: {e}")
        return
    
    # Import each file
    total_stats = {"success": 0, "errors": 0, "skipped": 0}
    
    for json_file in json_files:
        stats = import_json_file(json_file)
        total_stats["success"] += stats["success"]
        total_stats["errors"] += stats["errors"]
        total_stats["skipped"] += stats["skipped"]
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 MIGRATION SUMMARY")
    print("=" * 70)
    print(f"Files processed:    {len(json_files)}")
    print(f"✓ Successfully imported: {total_stats['success']} video(s)")
    print(f"⚠ Skipped:              {total_stats['skipped']} video(s)")
    print(f"✗ Errors:               {total_stats['errors']} video(s)")
    print("=" * 70)
    
    if total_stats["success"] > 0:
        print("\n✅ Migration completed successfully!")
        print("\n💡 Next steps:")
        print("  1. Verify data: curl http://localhost:8000/analytics")
        print("  2. Check accounts: curl http://localhost:8000/accounts")
        print("  3. View API docs: http://localhost:8000/docs")
        print("\n  From now on, new scrapes will automatically save to the database!")
    else:
        print("\n⚠ No data was imported. Please check the errors above.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Migration cancelled by user")
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
