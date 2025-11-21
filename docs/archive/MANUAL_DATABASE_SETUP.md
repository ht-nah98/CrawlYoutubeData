# Manual PostgreSQL Database Setup Guide

Your PostgreSQL installation requires authentication configuration. This guide will help you set it up.

## Status Check

PostgreSQL is installed and running on your system:
```
✓ PostgreSQL 14.19 is installed
✓ PostgreSQL service is running
✓ Port 5432 is accessible
```

## The Issue

PostgreSQL on this system is configured with **peer authentication**, which means:
- It requires trust authentication or a password
- The database `youtube_analytics` needs to be created
- User authentication needs to be configured

## Solution: Configure PostgreSQL

### Option 1: Enable Trust Authentication (Recommended - Easier)

This allows local connections without password:

```bash
# 1. Edit PostgreSQL configuration
sudo nano /etc/postgresql/14/main/pg_hba.conf

# 2. Find this line:
#    local   all             all                                     peer

# 3. Change 'peer' to 'trust':
#    local   all             all                                     trust

# 4. Save (Ctrl+X, Y, Enter)

# 5. Restart PostgreSQL
sudo systemctl restart postgresql

# 6. Verify
pg_isready -h localhost
# Should show: localhost:5432 - accepting connections
```

### Option 2: Set PostgreSQL Password

If you prefer using a password:

```bash
# 1. Start PostgreSQL shell (you may need to use sudo)
sudo -u postgres psql

# 2. Set password for postgres user
ALTER USER postgres WITH PASSWORD 'your_secure_password';

# 3. Exit
\q

# 4. Update .env file with password
nano .env
# Change DB_PASSWORD=your_secure_password

# 5. Restart PostgreSQL
sudo systemctl restart postgresql
```

## After Configuration

Once you've enabled trust authentication or set a password, create the database:

```bash
# Create the database
python3 init_db.py

# Expected output:
# ✓ Connected to PostgreSQL via TCP (localhost:5432)
# ✓ Database tables created successfully!
#
# Created tables:
#    • accounts
#    • channels
#    • scraping_history
#    • traffic_sources
#    • video_analytics
#    • videos
```

## Verify Database Connection

Test the connection:

```bash
# With trust authentication (no password):
psql -h localhost -U postgres -d youtube_analytics -c "SELECT 1"

# Or with password:
PGPASSWORD=your_password psql -h localhost -U postgres -d youtube_analytics -c "SELECT 1"
```

## Then Start the API

Once the database is set up:

```bash
# Start the API server
python -m uvicorn src.api.main:app --reload --port 8000

# Open in browser
http://localhost:8000/docs
```

## Database Details

After setup, you'll have:
- **Database**: youtube_analytics
- **User**: postgres
- **Host**: localhost
- **Port**: 5432

## Troubleshooting

### "Peer authentication failed"
→ Need to enable trust authentication (Option 1 above)

### "Password authentication failed"
→ Wrong password in .env or PostgreSQL not restarted
→ Check password with: `sudo -u postgres psql`

### "Cannot connect"
→ PostgreSQL not running
→ Start it: `sudo systemctl start postgresql`

### "Database doesn't exist"
→ Run: `python3 init_db.py`

## Manual Database Creation (Alternative)

If you can't run Python scripts, create database manually:

```bash
# With trust authentication enabled:
psql -h localhost -U postgres -c "CREATE DATABASE youtube_analytics;"

# Verify:
psql -h localhost -U postgres -l | grep youtube_analytics
```

## Next Steps

1. Follow Option 1 or 2 above
2. Verify with: `python3 init_db.py`
3. Start API: `python -m uvicorn src.api.main:app --reload --port 8000`
4. Open: http://localhost:8000/docs

Need more help? Check `docs/BACKEND_SETUP.md` for complete documentation.
