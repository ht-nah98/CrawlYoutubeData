#!/bin/bash

# YouTube Analytics - Database Setup Script
# This script sets up PostgreSQL and creates the necessary database

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║     YouTube Analytics - Database Setup                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Database credentials
DB_USER="youtube_user"
DB_PASSWORD="youtube_secure_password_2025"
DB_NAME="youtube_analytics"
DB_HOST="localhost"
DB_PORT="5432"

echo "📋 Database Configuration:"
echo "   Host:     $DB_HOST"
echo "   Port:     $DB_PORT"
echo "   Database: $DB_NAME"
echo "   User:     $DB_USER"
echo ""

# Check if PostgreSQL is installed
echo "🔍 Checking PostgreSQL installation..."
if ! command -v psql &> /dev/null; then
    echo "✗ PostgreSQL is not installed"
    echo ""
    echo "📦 To install PostgreSQL:"
    echo "   Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib"
    echo "   macOS:         brew install postgresql"
    echo "   Windows:       Download from https://www.postgresql.org/download/windows/"
    exit 1
fi

echo "✓ PostgreSQL is installed"
echo ""

# Try to start PostgreSQL service
echo "🚀 Starting PostgreSQL service..."
if command -v systemctl &> /dev/null; then
    sudo systemctl start postgresql 2>/dev/null || true
    sleep 2
fi

echo "✓ PostgreSQL service started"
echo ""

# Check if we can connect
echo "🔐 Verifying PostgreSQL access..."

# Try to connect as default postgres user
if sudo -u postgres psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw postgres; then
    echo "✓ PostgreSQL is accessible"
    echo ""

    # Create user if doesn't exist
    echo "👤 Creating database user '$DB_USER'..."
    sudo -u postgres psql << EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Grant privileges
ALTER USER $DB_USER CREATEDB;
EOF

    if [ $? -eq 0 ]; then
        echo "✓ User created/verified"
    else
        echo "⚠ Error creating user (it may already exist)"
    fi
    echo ""

    # Create database if doesn't exist
    echo "🗄️  Creating database '$DB_NAME'..."
    sudo -u postgres createdb -U $DB_USER $DB_NAME 2>/dev/null || true

    echo "✓ Database created/verified"
    echo ""

    # Test connection
    echo "🔗 Testing database connection..."
    PGPASSWORD=$DB_PASSWORD psql -U $DB_USER -d $DB_NAME -h $DB_HOST -c "SELECT 1" > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        echo "✓ Connection successful!"
        echo ""
        echo "╔════════════════════════════════════════════════════════════════╗"
        echo "║                   Database Setup Complete! ✓                    ║"
        echo "╚════════════════════════════════════════════════════════════════╝"
        echo ""
        echo "📊 Database Details:"
        echo "   Host:     $DB_HOST"
        echo "   Port:     $DB_PORT"
        echo "   Database: $DB_NAME"
        echo "   User:     $DB_USER"
        echo "   Password: (check .env file)"
        echo ""
        echo "🎯 Next steps:"
        echo "   1. Verify .env file has correct credentials"
        echo "   2. Run: python -m uvicorn src.api.main:app --reload --port 8000"
        echo "   3. Open: http://localhost:8000/docs"
        echo ""
    else
        echo "✗ Could not connect to database"
        echo ""
        echo "Try connecting manually:"
        echo "   psql -U $DB_USER -d $DB_NAME -h $DB_HOST"
        exit 1
    fi
else
    echo "✗ Could not access PostgreSQL"
    echo ""
    echo "Try running with sudo:"
    echo "   sudo ./setup_database.sh"
    exit 1
fi
