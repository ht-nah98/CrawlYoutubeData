# Backend Setup & API Documentation

This guide covers setting up the PostgreSQL backend and FastAPI REST API for the YouTube Analytics scraper.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Installation](#installation)
4. [API Startup](#api-startup)
5. [API Endpoints](#api-endpoints)
6. [Data Migration](#data-migration)
7. [Configuration](#configuration)
8. [Examples](#examples)

---

## Prerequisites

- **Python 3.8+** (3.10+ recommended)
- **PostgreSQL 12+** (or compatible database)
- **pip** or **conda** for package management

### PostgreSQL Installation

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### On macOS (using Homebrew):
```bash
brew install postgresql
brew services start postgresql
```

#### On Windows:
Download from https://www.postgresql.org/download/windows/

---

## Database Setup

### 1. Create Database and User

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database
CREATE DATABASE youtube_analytics;

# Create user with password
CREATE USER youtube_user WITH PASSWORD 'strong_password_here';

# Grant privileges
ALTER ROLE youtube_user SET client_encoding TO 'utf8';
ALTER ROLE youtube_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE youtube_user SET default_transaction_deferrable TO on;
ALTER ROLE youtube_user SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE youtube_analytics TO youtube_user;

# Exit psql
\q
```

### 2. Verify Connection

```bash
psql -U youtube_user -d youtube_analytics -h localhost
```

---

## Installation

### 1. Install Dependencies

```bash
cd /home/user/Downloads/craw_data_ytb

# Install all requirements including new backend dependencies
pip install -r requirements.txt
```

### 2. Setup Environment Variables

```bash
# Copy example .env file
cp .env.example .env

# Edit .env with your database credentials
nano .env  # or use your favorite editor
```

### .env Configuration

```
DB_HOST=localhost
DB_PORT=5432
DB_USER=youtube_user
DB_PASSWORD=strong_password_here
DB_NAME=youtube_analytics
DB_ECHO=false
```

---

## API Startup

### 1. Create Tables

The tables are automatically created on API startup, but you can manually create them:

```bash
python -c "from src.database.connection import db; db.create_tables()"
```

### 2. Start the API Server

```bash
# Development mode (with auto-reload)
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or use the Python entry point
python src/api/main.py
```

The API will be available at: `http://localhost:8000`

### 3. Access API Documentation

- **Swagger UI (Interactive)**: http://localhost:8000/docs
- **ReDoc (Visual)**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## API Endpoints

### Base URL
```
http://localhost:8000
```

### Health Check

```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### Accounts Management

#### List Accounts
```bash
GET /accounts?skip=0&limit=100
```

#### Create Account
```bash
POST /accounts
Content-Type: application/json

{
  "name": "Beau",
  "cookies_file": "profile/youtube_cookies_Beau.json"
}
```

#### Get Account
```bash
GET /accounts/{account_id}
```

#### Update Account
```bash
PUT /accounts/{account_id}
Content-Type: application/json

{
  "name": "Beau Updated",
  "cookies_file": "profile/youtube_cookies_Beau.json"
}
```

#### Delete Account
```bash
DELETE /accounts/{account_id}
```

---

### Channels Management

#### List Channels
```bash
GET /channels?account_id=1&skip=0&limit=100
```

#### Create Channel
```bash
POST /channels
Content-Type: application/json

{
  "account_id": 1,
  "url": "https://www.youtube.com/channel/UCxxxxx",
  "channel_id": "UCxxxxx",
  "channel_name": "My Channel"
}
```

#### Get Channel
```bash
GET /channels/{channel_id}
```

#### Update Channel
```bash
PUT /channels/{channel_id}
Content-Type: application/json

{
  "url": "https://www.youtube.com/channel/UCxxxxx",
  "channel_name": "Updated Channel Name"
}
```

#### Delete Channel
```bash
DELETE /channels/{channel_id}
```

---

### Videos Management

#### List Videos
```bash
GET /videos?channel_id=1&skip=0&limit=100
```

#### Create Video
```bash
POST /videos
Content-Type: application/json

{
  "video_id": "dQw4w9WgXcQ",
  "channel_id": 1,
  "title": "Video Title",
  "publish_date": "2025-01-01"
}
```

#### Bulk Create Videos
```bash
POST /videos/bulk
Content-Type: application/json

{
  "channel_id": 1,
  "video_ids": ["dQw4w9WgXcQ", "video_id_2", "video_id_3"]
}
```

#### Get Video
```bash
GET /videos/{video_id}
```

#### Update Video
```bash
PUT /videos/{video_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "publish_date": "2025-01-01"
}
```

#### Delete Video
```bash
DELETE /videos/{video_id}
```

---

### Analytics Data

#### List Analytics (with filtering)
```bash
GET /analytics?account_id=1&video_id=dQw4w9WgXcQ&date_from=2025-01-01&date_to=2025-12-31&skip=0&limit=100
```

#### Create Analytics
```bash
POST /analytics
Content-Type: application/json

{
  "video_id": "dQw4w9WgXcQ",
  "account_id": 1,
  "impressions": 1900,
  "views": 132,
  "unique_viewers": 120,
  "ctr_percentage": 4.3,
  "views_from_impressions": 79,
  "youtube_recommending_percentage": 89.3,
  "ctr_from_impressions_percentage": 4.3,
  "avg_view_duration_seconds": 1221,
  "watch_time_hours": 26.8,
  "publish_start_date": "2025-08-14",
  "top_metrics": {
    "Impressions": "1.9K",
    "Views": "132"
  },
  "traffic_sources": {
    "Browse features": "41.7%",
    "Suggested videos": "27.3%"
  },
  "impressions_data": {}
}
```

#### Bulk Create Analytics
```bash
POST /analytics/bulk
Content-Type: application/json

{
  "analytics": [
    {
      "video_id": "video_id_1",
      "account_id": 1,
      "impressions": 1000,
      "views": 100,
      ...
    },
    {
      "video_id": "video_id_2",
      "account_id": 1,
      "impressions": 2000,
      "views": 200,
      ...
    }
  ]
}
```

#### Get Video Analytics
```bash
GET /analytics/video/{video_id}
```

Response:
```json
[
  {
    "id": 1,
    "video_id": "dQw4w9WgXcQ",
    "account_id": 1,
    "impressions": 1900,
    "views": 132,
    "scraped_at": "2025-11-21T10:30:00",
    "traffic_sources_breakdown": [
      {
        "id": 1,
        "analytics_id": 1,
        "source_name": "Browse features",
        "percentage": 41.7,
        "created_at": "2025-11-21T10:30:00"
      }
    ]
  }
]
```

#### Get Account Statistics
```bash
GET /analytics/account/{account_id}/stats?date_from=2025-01-01&date_to=2025-12-31
```

Response:
```json
{
  "total_videos": 33,
  "total_impressions": 62700,
  "total_views": 4356,
  "total_watch_time_hours": 885.4,
  "average_ctr_percentage": 6.9,
  "average_views_per_video": 131.9,
  "date_from": "2025-01-01",
  "date_to": "2025-12-31"
}
```

#### Get Analytics by ID
```bash
GET /analytics/{analytics_id}
```

#### Update Analytics
```bash
PUT /analytics/{analytics_id}
Content-Type: application/json

{
  "impressions": 2000,
  "views": 150,
  "ctr_percentage": 5.0
}
```

#### Delete Analytics
```bash
DELETE /analytics/{analytics_id}
```

---

## Data Migration

### Migrate Existing JSON Data to Database

```bash
# Run migration script
python -m src.database.migrate_json_to_db

# Or from Python
from src.database.migrate_json_to_db import JsonToDbMigrator

migrator = JsonToDbMigrator()
stats = migrator.run()

print(f"Migrated {stats['analytics_created']} analytics records")
```

Migration handles:
- Creates accounts from JSON filenames
- Creates videos from video_ids
- Parses numeric metrics automatically
- Prevents duplicates
- Reports detailed statistics

---

## Configuration

### Database Configuration (config.py)

```python
from src.database.config import DatabaseConfig

# Custom configuration
config = DatabaseConfig(
    host='localhost',
    port=5432,
    user='youtube_user',
    password='password',
    database='youtube_analytics',
    echo=False,
    pool_size=20,
    max_overflow=10
)
```

### Environment Variables

```
DB_HOST        Database host (default: localhost)
DB_PORT        Database port (default: 5432)
DB_USER        Database user (default: postgres)
DB_PASSWORD    Database password
DB_NAME        Database name (default: youtube_analytics)
DB_ECHO        Enable SQL logging (default: false)
```

---

## Examples

### Example 1: Create Account and Import Analytics

```python
import requests

API_BASE = "http://localhost:8000"

# Create account
account_response = requests.post(
    f"{API_BASE}/accounts",
    json={
        "name": "Beau",
        "cookies_file": "profile/youtube_cookies_Beau.json"
    }
)
account_id = account_response.json()["id"]

# Create analytics
analytics_response = requests.post(
    f"{API_BASE}/analytics",
    json={
        "video_id": "dQw4w9WgXcQ",
        "account_id": account_id,
        "impressions": 1000,
        "views": 100,
        "ctr_percentage": 10.0
    }
)

print(analytics_response.json())
```

### Example 2: Get Account Statistics

```python
import requests
from datetime import date, timedelta

API_BASE = "http://localhost:8000"

# Get stats for last 30 days
date_to = date.today()
date_from = date_to - timedelta(days=30)

response = requests.get(
    f"{API_BASE}/analytics/account/1/stats",
    params={
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat()
    }
)

stats = response.json()
print(f"Total views: {stats['total_views']}")
print(f"Average views per video: {stats['average_views_per_video']:.1f}")
print(f"Total watch time: {stats['total_watch_time_hours']:.1f} hours")
```

### Example 3: Query Analytics with Filters

```python
import requests

API_BASE = "http://localhost:8000"

# Get analytics for specific video
response = requests.get(
    f"{API_BASE}/analytics/video/dQw4w9WgXcQ",
    params={"skip": 0, "limit": 10}
)

analytics_list = response.json()
for analytics in analytics_list:
    print(f"{analytics['video_id']}: {analytics['views']} views, {analytics['scraped_at']}")
```

---

## Troubleshooting

### Database Connection Failed

```
Error: could not connect to server: Connection refused
```

**Solution:**
- Ensure PostgreSQL is running: `sudo systemctl status postgresql`
- Check database credentials in `.env`
- Verify database exists: `psql -U youtube_user -d youtube_analytics`

### Import Errors

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
pip install -r requirements.txt
```

### Migration Issues

```
IntegrityError: duplicate key value violates unique constraint
```

**Solution:**
- Migration script handles duplicates automatically
- If manually inserting, ensure video_id + account_id combinations are unique

---

## Next Steps

1. [Start the scraper with database support](../README.md)
2. [Configure API authentication](./API_AUTHENTICATION.md)
3. [Setup automated backups](./BACKUP_STRATEGY.md)
4. [Monitor API performance](./MONITORING.md)
