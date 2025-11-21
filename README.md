# 📺 YouTube Analytics Scraper & API

A professional tool to scrape, store, and analyze YouTube video analytics with a graphical interface and REST API.

## 🚀 Features

- **GUI Scraper**: User-friendly graphical interface for managing YouTube accounts
- **Automated Scraping**: Collects detailed analytics from YouTube Studio
- **Data Storage**: Saves data to PostgreSQL database and JSON backups
- **REST API**: Full REST API to query videos, channels, and analytics
- **Multi-Account**: Support for multiple YouTube accounts and channels
- **Historical Tracking**: Tracks performance metrics over time
- **Traffic Sources**: Detailed breakdown of viewer sources

---

## 📋 System Requirements

### Windows Prerequisites
- **Windows 10/11** (64-bit recommended)
- **Python 3.8+** (Python 3.10+ recommended)
- **PostgreSQL 12+** (or local database)
- **Google Chrome** (for web scraping)
- **At least 2GB RAM** and **500MB disk space**

### Supported Components
- ✅ GUI Application (Tkinter-based)
- ✅ REST API Server (FastAPI)
- ✅ Database (PostgreSQL)
- ✅ Web Scraper (Selenium + Chrome)

---

## 📂 Project Structure

```
craw_data_ytb/
├── src/
│   ├── main.py                      # GUI app entry point
│   ├── api/
│   │   ├── main.py                 # FastAPI server
│   │   ├── routes/                 # API endpoints
│   │   └── schemas.py              # Data models
│   ├── database/
│   │   ├── models.py               # Database schema
│   │   ├── connection.py           # Database connection
│   │   └── config.py               # DB configuration
│   ├── scraper/
│   │   ├── youtube.py              # YouTube scraper
│   │   └── channel.py              # Channel operations
│   ├── gui/
│   │   └── app.py                  # Tkinter GUI
│   └── utils/                      # Helper utilities
│
├── scripts/
│   ├── setup/
│   │   ├── setup_db.py             # Database setup
│   │   └── init_db.py              # Initialize tables
│   └── migration/
│       ├── migrate_json_to_db.py
│       └── migrate_channels_to_db.py
│
├── docs/                           # Documentation
├── profile/                        # YouTube cookies storage
├── config.json                     # Configuration file
├── .env                            # Environment variables
└── requirements.txt                # Python dependencies
```

---

## 🏁 Getting Started on Windows

### Step 1: Install Python

1. Download Python from [python.org](https://www.python.org/downloads/)
   - Make sure to download **Python 3.10+**
   - ✅ **Important**: Check "Add Python to PATH" during installation

2. Verify installation - Open **Command Prompt** and run:
   ```cmd
   python --version
   pip --version
   ```

### Step 2: Install PostgreSQL (Database)

1. Download PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)
   - Recommend version **PostgreSQL 14+**

2. Run the installer:
   - Set a password for the `postgres` user (remember this!)
   - Use default port `5432`
   - Check "Add PostgreSQL to PATH"

3. Verify installation - Open **Command Prompt** and run:
   ```cmd
   psql --version
   ```

### Step 3: Clone/Download the Project

```cmd
git clone https://gitlab.com/hg-media/crawl-data.git
cd crawl-data
```

Or if you don't have Git, download the ZIP and extract it.

### Step 4: Create Virtual Environment

In **Command Prompt**, from the project folder:

```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` at the start of the command line.

### Step 5: Install Dependencies

```cmd
pip install -r requirements.txt
```

This may take a few minutes. Wait for it to complete.

### Step 6: Configure Environment

1. Create `.env` file in the project root (copy from `.env.example`):
   ```cmd
   copy .env.example .env
   ```

2. Edit `.env` with your PostgreSQL credentials:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   DB_NAME=youtube_analytics
   ```

### Step 7: Initialize Database

```cmd
python scripts/setup/init_db.py
```

You should see:
```
✓ Database tables created successfully
```

---

## ▶️ Running the Application

You have two options:

### Option A: GUI Application (Recommended for Users)

```cmd
python src/main.py
```

This opens the graphical interface where you can:
- Add YouTube accounts
- Manage multiple channels
- Scrape analytics data
- View results

### Option B: REST API Server

```cmd
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### Option C: Run Both Simultaneously

Open **two Command Prompt windows**:

**Window 1 - Start API:**
```cmd
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Window 2 - Start GUI:**
```cmd
python src/main.py
```

---

## 🔧 Troubleshooting

### Python not found
- Make sure Python is added to PATH
- Restart Command Prompt after installing Python
- Try `py --version` instead of `python --version`

### PostgreSQL Connection Error
- Verify PostgreSQL is running (check Services in Windows)
- Check credentials in `.env` file
- Make sure PostgreSQL server is listening on port 5432

### pip install fails
- Upgrade pip: `python -m pip install --upgrade pip`
- Try: `pip install -r requirements.txt --no-cache-dir`

### GUI won't start
- Make sure you activated the virtual environment: `venv\Scripts\activate`
- Check that tkinter is installed: `python -m tkinter`
- Restart the application

### Chrome/Selenium issues
- Make sure Google Chrome is installed
- webdriver-manager should auto-download the correct chromedriver

### Virtual Environment Issues
- To deactivate: `deactivate`
- To reactivate: `venv\Scripts\activate`
- To delete and restart: `rmdir /s venv` then repeat Step 4

---

## 📚 Common Tasks

### Add a YouTube Account

1. Run the GUI: `python src/main.py`
2. Click "Add Account"
3. Enter account name and log in to YouTube
4. Cookies are saved automatically in `profile/`

### Export Data

```cmd
python scripts/migration/migrate_json_to_db.py
```

### Check API Status

Open browser and go to: `http://localhost:8000/docs`

This shows all available API endpoints with documentation.

### View Database

```cmd
psql -U postgres -d youtube_analytics
```

---

## 🔐 Security Notes

⚠️ **Important:**
- Never commit `.env` file to Git (already in `.gitignore`)
- YouTube cookies in `profile/` are automatically ignored
- Change default database password in production
- Keep your PostgreSQL password secure

---

## 📖 Additional Documentation

- [API Guide](docs/BACKEND_SETUP.md) - Complete API documentation
- [Developer Guide](docs/DEVELOPER_GUIDE.md) - For developers
- [Database Setup](docs/BACKEND_SETUP.md) - Database details

---

## ❓ FAQ

**Q: Can I use SQLite instead of PostgreSQL?**
- Currently the application uses PostgreSQL. SQLite support can be added if needed.

**Q: Can I run this on Mac/Linux?**
- Yes! Follow the same steps but use `python3` and `venv/bin/activate` instead of the Windows commands.

**Q: How do I update the application?**
- Pull the latest changes: `git pull`
- Update dependencies: `pip install -r requirements.txt --upgrade`

**Q: Where is my data stored?**
- PostgreSQL database: Configured in `.env`
- JSON backups: `data/` folder
- Browser cookies: `profile/` folder

---

## 📞 Support

For issues or questions:
1. Check the [docs/](docs/) folder for detailed guides
2. Review troubleshooting section above
3. Check PostgreSQL and Python are correctly installed
4. Make sure `.env` file is properly configured

---

## 📝 License

This project is proprietary. All rights reserved.