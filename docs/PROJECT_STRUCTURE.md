# Project Structure

## 📁 Root Directory
```
craw_data_ytb/
├── config.json              # Main configuration file
├── requirements.txt         # Python dependencies
├── run.sh                   # Launcher script
├── README.md               # Main documentation
├── HOW_TO_RUN.md           # Running instructions
├── QUICK_START.md          # Quick start guide
├── profile/                # User cookies storage
├── docs/                   # Documentation
│   ├── archive/           # Old documentation (archived)
│   ├── BUG_FIXES.md
│   ├── DEVELOPMENT.md
│   └── QUICK_START.md
└── src/                    # Source code
    ├── main.py            # Entry point
    ├── gui/               # GUI components
    ├── scraper/           # Scraping logic
    └── utils/             # Utility functions
```

## 📝 Key Files

### Root Level
- **config.json** - Stores accounts, channels, and video IDs
- **requirements.txt** - Python package dependencies
- **run.sh** - Convenient launcher script
- **README.md** - Complete project documentation
- **HOW_TO_RUN.md** - How to run the application
- **QUICK_START.md** - Quick start guide

### Source Code (`src/`)
- **main.py** - Application entry point
- **gui/app.py** - Main GUI application
- **scraper/youtube.py** - YouTube analytics scraper
- **scraper/channel.py** - Channel video fetching
- **utils/config_manager.py** - Configuration management
- **utils/cookie_manager.py** - Cookie handling
- **utils/chrome_driver.py** - WebDriver setup

### Data Storage
- **profile/** - Stores user cookies (youtube_cookies_*.json)
- **Output files** - Analytics results (analytics_results_*.json)

## 🗂️ Documentation Structure

### Active Documentation (Root)
- README.md - Main documentation
- HOW_TO_RUN.md - Running instructions
- QUICK_START.md - Quick start guide

### Additional Documentation (docs/)
- BUG_FIXES.md - Bug fix history
- DEVELOPMENT.md - Development guide
- QUICK_START.md - Alternative quick start

### Archived Documentation (docs/archive/)
All old implementation plans, fix summaries, and analysis documents have been moved here for reference.

## 🧹 Cleaned Up

### Removed:
- ✅ Duplicate config.json in src/
- ✅ Old analytics results in src/
- ✅ Duplicate profile/ in src/
- ✅ chrome_profile/ directory
- ✅ All __pycache__ directories
- ✅ 30+ old documentation files (moved to docs/archive/)

### Kept:
- ✅ Essential documentation (README, HOW_TO_RUN, QUICK_START)
- ✅ Source code (src/)
- ✅ Configuration (config.json)
- ✅ User data (profile/)
- ✅ Dependencies (requirements.txt)
- ✅ Launcher (run.sh)

## 📊 Clean Structure Benefits

1. **Clear organization** - Easy to find what you need
2. **No duplicates** - Single source of truth
3. **Archived docs** - Old files preserved but out of the way
4. **Professional** - Clean, maintainable structure
5. **Developer-friendly** - Easy to navigate and understand
