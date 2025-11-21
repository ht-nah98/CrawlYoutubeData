# 📺 YouTube Analytics Scraper & API

A professional tool to scrape, store, and analyze YouTube video analytics.

## 🚀 Features

- **Automated Scraping**: Collects detailed analytics from YouTube Studio
- **Data Storage**: Saves data to PostgreSQL database and JSON backups
- **REST API**: Full API to query videos, channels, and analytics
- **Multi-Account**: Support for multiple YouTube accounts and channels
- **Historical Tracking**: Tracks performance over time
- **Traffic Sources**: Detailed breakdown of how viewers find your videos

## 📂 Project Structure

```
youtube-analytics/
├── 📁 src/                          # Source code
│   ├── api/                         # FastAPI backend
│   ├── database/                    # Database models & utilities
│   ├── gui/                         # GUI application
│   └── scraper/                     # YouTube scraper
│
├── 📁 scripts/                      # Utility scripts
│   ├── setup/                       # Setup scripts
│   └── migration/                   # Data migration scripts
│
├── 📁 data/                         # Data storage
│   ├── analytics/                   # Analytics JSON backups
│   └── cookies/                     # Browser cookies
│
└── 📁 docs/                         # Documentation
```

## 🏁 Quick Start

1. **Setup Environment**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   # Edit .env with your database credentials
   ```

2. **Initialize Database**
   ```bash
   python3 scripts/setup/init_db.py
   ```

3. **Start the System**
   ```bash
   # Start API Server
   ./run.sh
   
   # Start GUI Scraper (in new terminal)
   python3 src/main.py
   ```

## 📚 Documentation

- [Quick Start Guide](docs/QUICK_START.md)
- [API Documentation](docs/API_GUIDE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)

## 🔧 Tools

- **Migrate JSON Data**: `python3 scripts/migration/migrate_json_to_db.py`
- **Migrate Channels**: `python3 scripts/migration/migrate_channels_to_db.py`