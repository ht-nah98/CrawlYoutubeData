#!/usr/bin/env python3
"""
Simple database initialization script
"""

import sys
import os
from pathlib import Path

# Add project root to path
# Add project root to path (2 levels up from scripts/setup/)
sys.path.insert(0, str(Path(__file__).parents[2]))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

try:
    from sqlalchemy import create_engine, text
    from src.database.models import Base
    from src.database.config import DatabaseConfig

    print("=" * 70)
    print("  YouTube Analytics - Database Initialization")
    print("=" * 70)
    print()

    # Create connection to PostgreSQL using config
    config = DatabaseConfig()
    print("📋 Attempting to connect to PostgreSQL...")
    print(f"   Connection: {config.url.replace(config.password, '***') if config.password else config.url}")
    print()

    # Try connection
    try:
        engine = create_engine(
            config.url,
            echo=False
        )

        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            print(f"✓ Connected to PostgreSQL at {config.host}:{config.port}")
    except Exception as e:
        print(f"✗ TCP connection failed: {e}")
        print()
        print("Note: PostgreSQL requires trust authentication or password")
        print()
        print("To set up PostgreSQL without password:")
        print("  1. Edit /etc/postgresql/14/main/pg_hba.conf")
        print("  2. Change 'peer' to 'trust' for local connections")
        print("  3. Restart PostgreSQL: sudo systemctl restart postgresql")
        sys.exit(1)

    print()
    print("🗄️  Creating database tables...")

    # Create tables
    Base.metadata.create_all(bind=engine)

    print("✓ Database tables created successfully!")
    print()

    # Verify tables
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]

    print("📊 Created tables:")
    for table in tables:
        print(f"   • {table}")

    print()
    print("=" * 70)
    print("  Database Setup Complete! ✓")
    print("=" * 70)
    print()
    print("🎯 Next steps:")
    print("  1. Start the API server:")
    print("     python -m uvicorn src.api.main:app --reload --port 8000")
    print()
    print("  2. Open in your browser:")
    print("     http://localhost:8000/docs")
    print()
    print("  3. (Optional) Migrate existing JSON data:")
    print("     python -m src.database.migrate_json_to_db")
    print()

except ImportError as e:
    print(f"✗ Import error: {e}")
    print()
    print("Make sure to install dependencies first:")
    print("  pip install -r requirements.txt")
    sys.exit(1)

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
