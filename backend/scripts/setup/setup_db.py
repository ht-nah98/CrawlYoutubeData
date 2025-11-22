#!/usr/bin/env python3
"""
Database Setup Script for YouTube Analytics Backend

This script helps set up the PostgreSQL database and initialize the schema.
It can work with existing PostgreSQL installations.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.database.connection import db
from src.database.config import DatabaseConfig


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_success(text):
    """Print success message."""
    print(f"✓ {text}")


def print_error(text):
    """Print error message."""
    print(f"✗ {text}")


def print_info(text):
    """Print info message."""
    print(f"ℹ {text}")


def check_database_connection():
    """Check if we can connect to PostgreSQL."""
    print_info("Checking PostgreSQL connection...")

    try:
        if db.health_check():
            print_success("PostgreSQL is accessible")
            return True
        else:
            print_error("Cannot connect to PostgreSQL")
            return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False


def create_tables():
    """Create all database tables."""
    print_info("Creating database tables...")

    try:
        db.create_tables()
        print_success("Database tables created successfully")
        return True
    except Exception as e:
        print_error(f"Error creating tables: {e}")
        return False


def main():
    """Main setup function."""
    print_header("YouTube Analytics - Database Setup")

    # Display current configuration
    config = db.config
    print("📋 Current Database Configuration:")
    print(f"   Host:     {config.host}")
    print(f"   Port:     {config.port}")
    print(f"   User:     {config.user}")
    print(f"   Database: {config.database}")
    print("")

    # Check .env file
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        print_success(".env file found")
    else:
        print_error(".env file not found")
        print_info("Creating .env from .env.example...")
        try:
            env_example = PROJECT_ROOT / ".env.example"
            if env_example.exists():
                with open(env_example) as f:
                    env_content = f.read()
                with open(env_file, "w") as f:
                    f.write(env_content)
                print_success(".env file created from example")
            else:
                print_error("Cannot find .env.example")
                return False
        except Exception as e:
            print_error(f"Error creating .env: {e}")
            return False

    print("")

    # Check PostgreSQL connection
    if not check_database_connection():
        print_error("Cannot establish database connection")
        print_info("Make sure PostgreSQL is running and credentials in .env are correct")
        print_info("Connection string: {db.config.url}")
        return False

    print("")

    # Create tables
    if not create_tables():
        return False

    print("")
    print_header("Setup Complete!")

    print("✓ Database is ready for use")
    print("")
    print("Next steps:")
    print("  1. Install dependencies: pip install -r requirements.txt")
    print("  2. Start API server: python -m uvicorn src.api.main:app --reload --port 8000")
    print("  3. Open in browser: http://localhost:8000/docs")
    print("  4. (Optional) Migrate JSON data: python -m src.database.migrate_json_to_db")
    print("")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
