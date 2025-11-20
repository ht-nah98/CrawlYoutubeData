# Quick Structure Guide - After Refactoring

**Last Updated:** November 20, 2025

## Project Organization

Your YouTube Analytics Scraper is now organized in a professional, easy-to-navigate structure.

### File Locations Reference

| What I Want to Do | Where to Go |
|---|---|
| **Start the app** | Run: `python3 src/main.py` |
| **Modify GUI / UI** | Edit: `src/gui/app.py` |
| **Change scraping logic** | Edit: `src/scraper/youtube.py` |
| **Extract channel video IDs** | Edit: `src/scraper/channel.py` |
| **Edit config handling** | Edit: `src/utils/config_manager.py` |
| **Change logging** | Edit: `src/utils/logger.py` |
| **Modify Chrome setup** | Edit: `src/utils/chrome_driver.py` |
| **Update cookies handling** | Edit: `src/utils/cookie_manager.py` |
| **Learn how to use it** | Read: `docs/QUICK_START.md` |
| **See all bug fixes** | Read: `docs/BUG_FIXES.md` |
| **Learn how to extend it** | Read: `docs/DEVELOPMENT.md` |
| **Add new accounts** | Use GUI: Click "👤 Tài khoản Google" button |
| **Add new channels** | Use GUI: Enter URL in "Kênh YouTube" section |
| **Check results** | Look for: `analytics_results_{AccountName}.json` |
| **View configuration** | Edit: `config.json` (for power users only) |
| **View scraping history** | Check: `profile/scraping_tracker.json` |
| **View saved cookies** | Check: `profile/youtube_cookies_*.json` |

### Directory Tree

```
craw_data_ytb/
│
├── src/                          ← ALL APPLICATION CODE
│   ├── main.py                   ← START HERE (entry point)
│   │
│   ├── gui/
│   │   ├── __init__.py
│   │   └── app.py                ← GUI/UI code
│   │
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── youtube.py            ← Core scraping logic
│   │   └── channel.py            ← Channel video extraction
│   │
│   └── utils/
│       ├── __init__.py
│       ├── config_manager.py     ← Configuration file handling
│       ├── logger.py             ← Logging utilities
│       ├── chrome_driver.py      ← Selenium Chrome driver
│       ├── cookies.py            ← Cookie management
│       ├── validators.py         ← Input validation
│       ├── tracker.py            ← Scraping history
│       └── constants.py          ← Configuration constants
│
├── docs/                         ← DOCUMENTATION
│   ├── QUICK_START.md            ← User guide & setup
│   ├── BUG_FIXES.md              ← Bug documentation
│   ├── DEVELOPMENT.md            ← Developer guide
│   └── FILES_TO_DELETE.txt       ← Cleanup reference
│
├── profile/                      ← USER DATA
│   ├── youtube_cookies_*.json    ← Saved cookies
│   └── scraping_tracker.json     ← Scraping history
│
├── chrome_profile/               ← Browser profile cache
│
├── README.md                     ← Main documentation
├── config.json                   ← User configuration
├── requirements.txt              ← Python dependencies
├── REFACTORING_PLAN.md           ← What we planned
├── REFACTORING_COMPLETE.md       ← What we did
└── REFACTORING_FINAL_SUMMARY.md  ← Final summary
```

## Quick Navigation

### For Users
- **First time?** → Read `docs/QUICK_START.md`
- **Having issues?** → Check `docs/BUG_FIXES.md`
- **Want to understand the app?** → Read `README.md`

### For Developers
- **Want to add a feature?** → Follow `docs/DEVELOPMENT.md`
- **Want to modify GUI?** → Edit `src/gui/app.py`
- **Want to change scraping?** → Edit `src/scraper/youtube.py`
- **Want to see code examples?** → Check `docs/DEVELOPMENT.md`

### For Maintenance
- **Configuration?** → `config.json` or `src/utils/config_manager.py`
- **Logging setup?** → `src/utils/logger.py`
- **Browser automation?** → `src/utils/chrome_driver.py`
- **Cookie handling?** → `src/utils/cookies.py`

## Key Files Explained

### src/main.py
**Purpose:** Entry point for the GUI application
**Run it with:** `python3 src/main.py`
**What it does:** Initializes the GUI and starts the application

### src/gui/app.py
**Purpose:** All graphical user interface code
**Size:** 3,380 lines
**Contains:** 
- Window layout and design
- Button and widget creation
- Event handling (user interactions)
- Progress tracking display
- Log message display

### src/scraper/youtube.py
**Purpose:** Core scraping engine
**Size:** 2,581 lines
**Contains:**
- Chrome WebDriver initialization
- Google login automation
- Analytics data extraction
- Cookie management
- Error handling and retries

### src/scraper/channel.py
**Purpose:** YouTube channel operations
**Size:** 818 lines
**Contains:**
- Video ID extraction
- Google OAuth authentication
- Account configuration

### src/utils/config_manager.py
**Purpose:** Configuration file handling
**Contains:**
- Read/write config.json
- Account management
- Settings management

### docs/QUICK_START.md
**For:** Users who want to use the application
**Contains:** Installation, setup, basic workflow

### docs/BUG_FIXES.md
**For:** Understanding what issues were fixed
**Contains:** 6 major bug fixes with details

### docs/DEVELOPMENT.md
**For:** Developers who want to extend the code
**Contains:** Architecture, examples, best practices

## Common Tasks

### Run the application
```bash
cd /path/to/craw_data_ytb
python3 src/main.py
```

### View scraping results
```bash
# Results saved as:
cat analytics_results_YourAccountName.json
```

### Check configuration
```bash
# View configuration:
cat config.json

# Edit configuration (for power users):
# Edit with your text editor
```

### View application logs
```bash
# Check scraping history:
cat profile/scraping_tracker.json
```

## File Organization Benefits

✅ **Easy to find code** - Organized by function (gui/, scraper/, utils/)
✅ **Easy to understand** - Clear separation of concerns
✅ **Easy to extend** - Add features without affecting other modules
✅ **Easy to debug** - Know exactly where to look
✅ **Easy to maintain** - Professional Python structure

## What Changed from Old Structure

| Aspect | Old | New |
|---|---|---|
| **Entry point** | `python3 gui.py` | `python3 src/main.py` |
| **GUI code location** | `gui.py` (3,380 lines) | `src/gui/app.py` |
| **Scraper location** | `craw.py` (2,581 lines) | `src/scraper/youtube.py` |
| **Channel code** | `get_channel_videos.py` | `src/scraper/channel.py` |
| **Utilities** | `utils/` (7 files) | `src/utils/` |
| **Documentation** | 28 scattered files | 4 files in `docs/` |
| **Root directory** | Cluttered (28+ files) | Clean (minimal files) |

## Backwards Compatibility

The old entry point still works:
```bash
python3 gui.py  # Still works! (shows deprecation message)
```

But the recommended way is now:
```bash
python3 src/main.py  # Preferred
```

## Questions?

1. **"How do I use this?"** → `docs/QUICK_START.md`
2. **"Where is the GUI code?"** → `src/gui/app.py`
3. **"Where is the scraper?"** → `src/scraper/youtube.py`
4. **"How do I add features?"** → `docs/DEVELOPMENT.md`
5. **"What bugs were fixed?"** → `docs/BUG_FIXES.md`

---

**Your project is now organized professionally and ready for development!**

