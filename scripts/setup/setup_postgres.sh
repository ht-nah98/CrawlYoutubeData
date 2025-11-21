#!/bin/bash

# Automated PostgreSQL Setup for YouTube Analytics API
# This script sets up PostgreSQL with password authentication

echo "========================================="
echo "PostgreSQL Setup for YouTube Analytics"
echo "========================================="
echo ""

# Set password
PASSWORD="youtube_analytics_2024"

echo "Setting PostgreSQL password..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '${PASSWORD}';" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ PostgreSQL password set successfully"
else
    echo "⚠ Could not set password (may require manual setup)"
    echo ""
    echo "Please run manually:"
    echo "  sudo -u postgres psql"
    echo "  ALTER USER postgres WITH PASSWORD 'youtube_analytics_2024';"
    echo "  \\q"
    exit 1
fi

echo ""
echo "Updating .env file..."

# Update .env file
cd /home/user/Downloads/craw_data_ytb

# Backup original .env
cp .env .env.backup

# Update password in .env
sed -i 's/^DB_PASSWORD=$/DB_PASSWORD=youtube_analytics_2024/' .env

echo "✓ .env file updated"

echo ""
echo "Restarting PostgreSQL..."
sudo systemctl restart postgresql

if [ $? -eq 0 ]; then
    echo "✓ PostgreSQL restarted successfully"
else
    echo "⚠ Could not restart PostgreSQL"
    echo "Please run: sudo systemctl restart postgresql"
    exit 1
fi

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. python3 init_db.py"
echo "  2. python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
