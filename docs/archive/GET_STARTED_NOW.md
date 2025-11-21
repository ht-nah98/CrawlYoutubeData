# Get Started Now! 🚀

Your backend is ready. Just 3 steps to open the database and start using the API.

## Step 1: Configure PostgreSQL (One-Time Setup)

PostgreSQL requires authentication configuration. Choose one:

### ✨ Option A: Trust Authentication (Recommended - 2 minutes)

```bash
# Edit PostgreSQL configuration
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Find:     local   all             all                                     peer
# Change to: local   all             all                                     trust

# Save: Ctrl+X, then Y, then Enter

# Restart PostgreSQL
sudo systemctl restart postgresql

# Verify it works
pg_isready -h localhost
```

**Output should be:** `localhost:5432 - accepting connections`

### 🔐 Option B: Set PostgreSQL Password (If you prefer passwords)

```bash
# Set password
sudo -u postgres psql

# In psql, type:
ALTER USER postgres WITH PASSWORD 'secure_password_123';
\q

# Edit .env file
nano .env
# Change: DB_PASSWORD=secure_password_123

# Restart
sudo systemctl restart postgresql
```

## Step 2: Create Database Tables

```bash
cd /home/user/Downloads/craw_data_ytb

# Create the database and tables
python3 init_db.py
```

**You should see:**
```
✓ Connected to PostgreSQL via TCP (localhost:5432)
✓ Database tables created successfully!

Created tables:
   • accounts
   • channels
   • scraping_history
   • traffic_sources
   • video_analytics
   • videos
```

## Step 3: Start the API Server

```bash
# Start the API
python -m uvicorn src.api.main:app --reload --port 8000
```

**You should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

## Step 4: Open in Your Browser

Click one of these links or open in browser:

- **Interactive API Docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc
- **API Health Check**: http://localhost:8000/health

## What You Can Do Now

### In the Swagger UI (http://localhost:8000/docs):

1. **Create an Account**
   - Click `POST /accounts`
   - Click "Try it out"
   - Enter: `{"name": "MyAccount"}`
   - Click "Execute"

2. **Create Videos**
   - Click `POST /videos/bulk`
   - Enter video IDs: `["dQw4w9WgXcQ", "9bZkp7q19f0"]`
   - Click "Execute"

3. **Add Analytics Data**
   - Click `POST /analytics`
   - Enter: analytics data
   - Click "Execute"

4. **Query Your Data**
   - Click `GET /analytics`
   - Click "Execute"
   - See all your analytics!

5. **Get Statistics**
   - Click `GET /analytics/account/1/stats`
   - Click "Execute"
   - See total views, average CTR, etc.

## Optional: Migrate Your Existing Data

If you have existing `analytics_results_*.json` files:

```bash
# Migrate all JSON data to database
python -m src.database.migrate_json_to_db

# You'll see:
# Found 2 analytics files
# Processing analytics_results_Beau.json (33 videos)
# ✓ Migrated 33 analytics records
# ✓ Migration complete!
```

## Troubleshooting

### Error: "fe_sendauth: no password supplied"
→ You're still on step 1. Enable trust authentication or set password first.

### Error: "Cannot connect to server"
→ PostgreSQL not running. Try: `sudo systemctl restart postgresql`

### Error: "Module not found"
→ Dependencies not installed: `pip install -r requirements.txt`

### Error: "Port 8000 already in use"
→ Another app using it: `python -m uvicorn src.api.main:app --reload --port 8001`

## File Locations

| What | File |
|------|------|
| Database setup instructions | `MANUAL_DATABASE_SETUP.md` |
| This quick start | `GET_STARTED_NOW.md` |
| API Quick Start | `API_QUICKSTART.md` |
| Full documentation | `docs/BACKEND_SETUP.md` |
| Developer guide | `docs/DEVELOPER_GUIDE.md` |
| Database init script | `init_db.py` |
| Configuration | `.env` |

## Your System Status

```
✓ Python 3 installed
✓ PostgreSQL 14 installed
✓ Docker available (optional)
✓ All dependencies installed
✓ Backend code ready
✓ API configured
✓ Just need: Database authentication setup!
```

## How the System Works

```
Your Browser
    ↓
http://localhost:8000/docs (Swagger UI)
    ↓
FastAPI Server (Python)
    ↓
SQLAlchemy ORM
    ↓
PostgreSQL Database
```

## Next: Integrate with Your Scraper

Once everything is working, update your scraper:

```python
from src.database.writers import db_writer

# In your scraper
analytics = db_writer.save_analytics(
    video_id="dQw4w9WgXcQ",
    account_name="MyAccount",
    analytics_data={...}
)
```

## Common API Endpoints

```bash
# Get all analytics
curl http://localhost:8000/analytics

# Create account
curl -X POST http://localhost:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Beau"}'

# Get account stats
curl http://localhost:8000/analytics/account/1/stats

# Query analytics with filter
curl "http://localhost:8000/analytics?account_id=1&limit=10"
```

---

## Summary

1. ✓ PostgreSQL is already installed and running
2. ✓ Backend code is ready
3. ⚠ Need to: Configure PostgreSQL authentication
4. Then: Run `python3 init_db.py`
5. Then: Run `python -m uvicorn src.api.main:app --reload --port 8000`
6. Then: Open http://localhost:8000/docs

**Estimated time to get running: 5-10 minutes**

Let's go! 🚀

---

Questions? See `MANUAL_DATABASE_SETUP.md` for detailed help.
