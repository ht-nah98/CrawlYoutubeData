# 🚀 Quick Start Guide

## 1. Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Chrome Browser (for scraping)

## 2. Installation

```bash
# Clone repository
git clone <repo-url>
cd youtube-analytics

# Install dependencies
pip install -r requirements.txt
```

## 3. Configuration

1. **Environment Variables**
   ```bash
   cp .env.example .env
   nano .env
   ```
   Set your database credentials:
   ```ini
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_NAME=youtube_analytics
   ```

2. **YouTube Configuration**
   Edit `config.json` to add your accounts and channels:
   ```json
   {
     "accounts": [
       {
         "name": "MyChannel",
         "cookies_file": "data/cookies/profile/youtube_cookies_MyChannel.json",
         "channels": [
           {
             "url": "https://www.youtube.com/channel/UC...",
             "video_ids": ["video1", "video2"]
           }
         ]
       }
     ]
   }
   ```

## 4. Database Setup

```bash
# Initialize tables
python3 scripts/setup/init_db.py
```

## 5. Running the System

### Start API Server
```bash
./run.sh
# API will be available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Start Scraper GUI
```bash
python3 src/main.py
```

## 6. Data Migration (Optional)

If you have existing data:

```bash
# Migrate JSON files to database
python3 scripts/migration/migrate_json_to_db.py

# Migrate channels from config to database
python3 scripts/migration/migrate_channels_to_db.py
```
