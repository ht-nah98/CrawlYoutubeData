#!/usr/bin/env python3
"""Test different PostgreSQL connection methods"""

import psycopg2

# Test different ports and passwords
test_configs = [
    {'host': 'localhost', 'port': 5432, 'user': 'postgres', 'password': 'admin', 'desc': 'Port 5432 with admin'},
    {'host': 'localhost', 'port': 5432, 'user': 'postgres', 'password': 'postgres', 'desc': 'Port 5432 with postgres'},
    {'host': 'localhost', 'port': 5432, 'user': 'postgres', 'password': '', 'desc': 'Port 5432 no password'},
    {'host': '127.0.0.1', 'port': 5432, 'user': 'postgres', 'password': 'admin', 'desc': '127.0.0.1 with admin'},
    {'host': 'localhost', 'port': 5433, 'user': 'postgres', 'password': 'admin', 'desc': 'Port 5433 with admin'},
    {'host': 'localhost', 'port': 5434, 'user': 'postgres', 'password': 'admin', 'desc': 'Port 5434 with admin'},
]

print("=" * 70)
print("Testing PostgreSQL Connections")
print("=" * 70)

for config in test_configs:
    try:
        print(f"\nTrying: {config['desc']}...")
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database='postgres',
            connect_timeout=3
        )
        print(f"✓ SUCCESS! Connected with: {config['desc']}")
        print(f"  Host: {config['host']}")
        print(f"  Port: {config['port']}")
        print(f"  User: {config['user']}")
        print(f"  Password: {'(empty)' if not config['password'] else config['password']}")
        conn.close()
        break
    except Exception as e:
        print(f"✗ Failed: {str(e)[:100]}")

print("\n" + "=" * 70)
