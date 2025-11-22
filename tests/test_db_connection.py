#!/usr/bin/env python3
"""Test database connection"""

import os
from dotenv import load_dotenv
import psycopg2

# Load .env file
load_dotenv()

# Get credentials
host = os.getenv('DB_HOST', 'localhost')
port = os.getenv('DB_PORT', '5432')
user = os.getenv('DB_USER', 'postgres')
password = os.getenv('DB_PASSWORD', '')
database = os.getenv('DB_NAME', 'youtube_analytics')

print("=" * 70)
print("Testing PostgreSQL Connection")
print("=" * 70)
print(f"Host: {host}")
print(f"Port: {port}")
print(f"User: {user}")
print(f"Password: {'*' * len(password) if password else '(empty)'}")
print(f"Database: {database}")
print()

# Try to connect to postgres database first (to create our database)
try:
    print("Attempting to connect to 'postgres' database...")
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database='postgres'
    )
    print("✓ Connected successfully to postgres database!")
    
    # Create our database if it doesn't exist
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{database}'")
    exists = cursor.fetchone()
    
    if not exists:
        print(f"Creating database '{database}'...")
        cursor.execute(f'CREATE DATABASE {database}')
        print(f"✓ Database '{database}' created successfully!")
    else:
        print(f"✓ Database '{database}' already exists!")
    
    cursor.close()
    conn.close()
    
    # Now connect to our database
    print(f"\nConnecting to '{database}' database...")
    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    print(f"✓ Connected successfully to '{database}' database!")
    conn.close()
    
    print("\n" + "=" * 70)
    print("✓ Database connection test PASSED!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n✗ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure PostgreSQL service is running")
    print("2. Check if password in .env file is correct")
    print("3. Verify PostgreSQL is listening on the correct port")
    import traceback
    traceback.print_exc()
