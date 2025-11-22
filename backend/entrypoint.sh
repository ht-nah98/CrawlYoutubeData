#!/bin/bash
set -e

echo "🚀 Starting YouTube Analytics Backend..."

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for database to be ready..."
until pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}"; do
  echo "Database is unavailable - sleeping"
  sleep 2
done

echo "✅ Database is ready!"

# Initialize database if needed
if [ -f "scripts/setup/init_db.py" ]; then
    echo "📊 Initializing database..."
    python scripts/setup/init_db.py || echo "⚠️  Database initialization skipped (may already exist)"
fi

# Start the server
echo "🌐 Starting API server..."
exec python server.py

