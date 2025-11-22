#!/usr/bin/env python3
"""Test common PostgreSQL passwords"""

import psycopg2

common_passwords = [
    'admin',
    'postgres',
    'password',
    '123456',
    'root',
    '',
    '1234',
    'admin123',
    'postgres123',
]

ports = [5432, 5433, 5434]

print("=" * 70)
print("Testing Common PostgreSQL Passwords")
print("=" * 70)

found = False
for port in ports:
    if found:
        break
    print(f"\n Testing port {port}...")
    for pwd in common_passwords:
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=port,
                user='postgres',
                password=pwd,
                database='postgres',
                connect_timeout=2
            )
            print(f"\n✓✓✓ SUCCESS! ✓✓✓")
            print(f"Port: {port}")
            print(f"Password: '{pwd}' {' (empty)' if not pwd else ''}")
            print("\nUpdate your .env file with:")
            print(f"DB_PORT={port}")
            print(f"DB_PASSWORD={pwd}")
            conn.close()
            found = True
            break
        except Exception as e:
            error_msg = str(e)
            if 'password authentication failed' in error_msg:
                print(f"  ✗ '{pwd}' - wrong password")
            elif 'Connection refused' in error_msg or 'could not connect' in error_msg:
                print(f"  ✗ Port {port} not responding")
                break
            else:
                print(f"  ✗ '{pwd}' - {error_msg[:50]}")

if not found:
    print("\n" + "=" * 70)
    print("No working password found!")
    print("=" * 70)
    print("\nOptions:")
    print("1. Try resetting PostgreSQL password")
    print("2. Use pgAdmin to check connection settings")
    print("3. Reinstall PostgreSQL with a known password")
