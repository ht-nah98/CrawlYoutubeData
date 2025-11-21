#!/bin/bash

# YouTube Analytics API Server Startup Script
# This script helps you start the API server step by step

echo "========================================="
echo "YouTube Analytics API Server Setup"
echo "========================================="
echo ""

# Check if PostgreSQL is running
echo "Step 1: Checking PostgreSQL status..."
if systemctl is-active --quiet postgresql; then
    echo "✓ PostgreSQL is running"
else
    echo "✗ PostgreSQL is not running"
    echo "  Please start it with: sudo systemctl start postgresql"
    exit 1
fi

echo ""
echo "Step 2: Testing database connection..."

# Test database connection
if psql -U postgres -d youtube_analytics -c "SELECT 1" > /dev/null 2>&1; then
    echo "✓ Database connection successful!"
else
    echo "✗ Database connection failed"
    echo ""
    echo "You need to configure PostgreSQL authentication first."
    echo ""
    echo "Choose one option:"
    echo ""
    echo "Option A - Trust Authentication (Easier):"
    echo "  1. sudo nano /etc/postgresql/14/main/pg_hba.conf"
    echo "  2. Find:     local   all             all                                     peer"
    echo "  3. Change to: local   all             all                                     trust"
    echo "  4. Save: Ctrl+X, Y, Enter"
    echo "  5. sudo systemctl restart postgresql"
    echo ""
    echo "Option B - Set Password:"
    echo "  1. sudo -u postgres psql"
    echo "  2. ALTER USER postgres WITH PASSWORD 'your_password';"
    echo "  3. \\q"
    echo "  4. Edit .env file and set: DB_PASSWORD=your_password"
    echo "  5. sudo systemctl restart postgresql"
    echo ""
    exit 1
fi

echo ""
echo "Step 3: Initializing database tables..."

# Initialize database
if python3 init_db.py; then
    echo "✓ Database tables created successfully!"
else
    echo "⚠ Database initialization had issues (tables may already exist)"
fi

echo ""
echo "Step 4: Starting API server..."
echo ""
echo "API will be available at:"
echo "  - Interactive Docs: http://localhost:8000/docs"
echo "  - API Base: http://localhost:8000"
echo "  - Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "========================================="
echo ""

# Start the API server
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
