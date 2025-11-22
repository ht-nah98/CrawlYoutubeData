# 📺 YouTube Analytics - Professional Edition

A professional-grade YouTube analytics scraper and management system with clean architecture, RESTful API, and modern GUI client.

## 🏗️ Project Structure

```
youtube-analytics/
│
├── backend/                    # Backend Server (Deployable)
│   ├── src/
│   │   ├── api/               # REST API (FastAPI)
│   │   ├── database/          # Database layer (PostgreSQL)
│   │   ├── scraper/           # Web scraping engine (Selenium)
│   │   ├── core/              # Business logic
│   │   └── utils/             # Utilities
│   ├── scripts/               # Setup & migration scripts
│   ├── server.py              # Server entry point
│   ├── test_backend.py        # Backend tests
│   ├── start_server.bat       # Windows startup script
│   ├── requirements.txt       # Backend dependencies
│   └── README.md              # Backend documentation
│
├── gui/                        # GUI Client (Windows Desktop App)
│   ├── src/
│   │   ├── ui/                # User interface components
│   │   ├── api_client/        # Backend API client
│   │   ├── storage/           # Configuration & cache
│   │   └── utils/             # GUI utilities
│   ├── assets/                # Icons & images
│   ├── main.py                # GUI entry point
│   ├── start_gui.bat          # Windows startup script
│   ├── config.json            # GUI configuration
│   ├── requirements.txt       # GUI dependencies
│   └── README.md              # GUI documentation
│
├── src/                        # Original Source (Legacy)
│   ├── api/                   # Original API
│   ├── database/              # Original database
│   ├── scraper/               # Original scraper
│   ├── gui/                   # Original monolithic GUI
│   └── main.py                # Original entry point
│
├── data/                       # Data Storage
│   ├── cookies/               # YouTube session cookies
│   └── *.json                 # Analytics results
│
├── docs/                       # Documentation
│   ├── refactoring/           # Refactoring documentation
│   ├── setup/                 # Setup guides
│   └── api/                   # API documentation
│
├── scripts/                    # Setup & Migration Scripts
│   ├── setup/                 # Database setup
│   └── migration/             # Data migration
│
├── tests/                      # Test Files
│   └── test_*.py              # Test scripts
│
├── tools/                      # Utility Tools
│   ├── find_pg_password.py    # PostgreSQL password finder
│   ├── fix_chromedriver_windows.bat
│   └── *.sh                   # Shell scripts
│
├── venv/                       # Virtual Environment
│
├── .env                        # Environment configuration
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── config.json                 # Application configuration
├── requirements.txt            # Root dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 12+
- Google Chrome
- Windows 10/11 (for GUI)

### 1. Setup Environment

```bash
# Clone repository
git clone https://gitlab.com/hg-media/crawl-data.git
cd crawl-data

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Database

Edit `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=youtube_analytics
```

Initialize database:
```bash
python scripts/setup/init_db.py
```

### 3. Start Backend Server

```bash
cd backend
start_server.bat
```

Access at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

### 4. Start GUI Client

```bash
cd gui
start_gui.bat
```

## � Documentation

### For Users
- [Quick Start Guide](docs/setup/QUICK_START.md)
- [Windows Setup](docs/setup/WINDOWS_SETUP.md)
- [API Quick Start](docs/api/API_QUICKSTART.md)

### For Developers
- [Architecture Review](docs/refactoring/ARCHITECTURE_REVIEW.md)
- [Refactoring Plan](docs/refactoring/REFACTORING_PLAN.md)
- [Backend README](backend/README.md)
- [GUI README](gui/README.md)

## 🏛️ Architecture

### Backend Server
- **Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **Scraper**: Selenium + Chrome
- **API**: RESTful with auto-documentation
- **Deployment**: Independent, scalable

### GUI Client
- **Framework**: CustomTkinter
- **Communication**: HTTP/REST API
- **Configuration**: JSON-based
- **Build**: PyInstaller for .exe
- **Deployment**: Standalone Windows app

### Communication Flow
```
GUI Client ←→ HTTP/REST API ←→ Backend Server ←→ PostgreSQL
```

## � Development

### Backend Development
```bash
cd backend
python server.py
```

### GUI Development
```bash
cd gui
python main.py
```

### Running Tests
```bash
cd tests
python test_db_connection.py
python test_pg_configs.py
```

## 📦 Deployment

### Backend Deployment
1. Copy `backend/` to server
2. Configure `.env`
3. Install dependencies
4. Run `python server.py`

### GUI Distribution
1. Build executable:
   ```bash
   cd gui
   pyinstaller --onefile --windowed main.py
   ```
2. Distribute `dist/YouTubeAnalytics.exe`

## 🛠️ Tools

- `tools/find_pg_password.py` - Find PostgreSQL password
- `tools/fix_chromedriver_windows.bat` - Fix ChromeDriver issues
- `tools/run.sh` - Unix startup script
- `tools/START_API_SERVER.sh` - API server startup

## 📊 Features

### Current Features
- ✅ Multi-account management
- ✅ Channel tracking
- ✅ Video analytics scraping
- ✅ Traffic source analysis
- ✅ Historical data tracking
- ✅ REST API access
- ✅ Modern GUI interface

### API Endpoints
- `/accounts` - Account management
- `/channels` - Channel management
- `/videos` - Video management
- `/analytics` - Analytics data
- `/health` - Health check

## 🔒 Security

- Environment-based configuration
- Database connection pooling
- SQL injection prevention (ORM)
- Input validation (Pydantic)
- CORS configuration

## 📝 License

Proprietary - All rights reserved

## � Support

For issues or questions:
1. Check documentation in `docs/`
2. Review setup guides
3. Verify configuration
4. Check logs

## 🎯 Roadmap

- [ ] Web-based GUI
- [ ] Mobile app
- [ ] Real-time analytics
- [ ] Advanced visualizations
- [ ] Export to Excel/CSV
- [ ] Scheduled scraping
- [ ] Email notifications

---

**Version**: 2.0.0  
**Last Updated**: 2025-11-22  
**Status**: Production Ready