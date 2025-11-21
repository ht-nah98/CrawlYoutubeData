# 🚀 Quick Setup and Start Guide

Your API server is ready! You just need to configure PostgreSQL authentication first.

## Current Status

✅ PostgreSQL 14 is installed and running  
✅ Database `youtube_analytics` exists  
✅ API code is ready at `src/api/main.py`  
✅ Configuration file `.env` is set up  
⚠️ **Need to configure PostgreSQL authentication**

## Quick Start (Choose One Method)

### Method 1: Trust Authentication (Easiest - Recommended)

Run these commands one by one:

```bash
# 1. Edit PostgreSQL configuration
sudo nano /etc/postgresql/14/main/pg_hba.conf

# In the editor:
#   Find the line:     local   all             all                                     peer
#   Change it to:      local   all             all                                     trust
#   Save: Ctrl+X, then Y, then Enter

# 2. Restart PostgreSQL
sudo systemctl restart postgresql

# 3. Initialize database tables
cd /home/user/Downloads/craw_data_ytb
python3 init_db.py

# 4. Start the API server
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Method 2: Password Authentication (More Secure)

Run these commands one by one:

```bash
# 1. Set PostgreSQL password
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'youtube_analytics_2024';"

# 2. Update .env file
cd /home/user/Downloads/craw_data_ytb
nano .env
# Change line 5 from:  DB_PASSWORD=
# To:                  DB_PASSWORD=youtube_analytics_2024
# Save: Ctrl+X, then Y, then Enter

# 3. Restart PostgreSQL
sudo systemctl restart postgresql

# 4. Initialize database tables
python3 init_db.py

# 5. Start the API server
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## After Starting the Server

Once the server is running, you'll see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
Starting YouTube Analytics API...
✓ Database connection healthy
```

Then open in your browser:

- **Interactive API Docs**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health
- **Alternative Docs**: http://localhost:8000/redoc

## Using the Startup Script

Alternatively, after configuring PostgreSQL authentication, you can use:

```bash
./START_API_SERVER.sh
```

This script will:
1. Check PostgreSQL status
2. Test database connection
3. Initialize database tables
4. Start the API server

## Troubleshooting

### "Database connection failed"
→ PostgreSQL authentication not configured yet. Follow Method 1 or Method 2 above.

### "Port 8000 already in use"
→ Another process is using port 8000. Use a different port:
```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8001
```

### "Module not found"
→ Install dependencies:
```bash
pip install -r requirements.txt
```

## Next Steps

After the API is running:

1. **Test the API**: Visit http://localhost:8000/docs
2. **Create an account**: Use the POST /accounts endpoint
3. **Import existing data**: Run `python -m src.database.migrate_json_to_db`
4. **Integrate with GUI**: Update your GUI to use the API

## API Endpoints Available

- `GET /health` - Check API status
- `POST /accounts` - Create account
- `GET /accounts` - List accounts
- `POST /videos` - Add videos
- `POST /analytics` - Add analytics data
- `GET /analytics` - Query analytics
- `GET /analytics/account/{id}/stats` - Get statistics

Enjoy! 🎉
