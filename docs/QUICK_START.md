# Quick Start Guide

**YouTube Analytics Scraper** - Extract analytics data from YouTube Studio for multiple accounts and channels

---

## Installation

### Requirements
- Python 3.8+
- Chrome/Chromium browser

### Setup

1. **Clone or download the project**
```bash
cd /path/to/craw_data_ytb
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

---

## Running the Application

### GUI Mode (Recommended for Users)

```bash
python3 src/main.py
```

Or simply:
```bash
python3 gui.py  # Uses old location (still works)
```

The GUI application will launch with:
- Account management
- Channel selection
- Batch scraping control
- Real-time progress tracking
- Activity logging

---

## Basic Workflow

### Step 1: Add an Account

1. Click **👤 Tài khoản Google** (Google Account)
2. A browser window will open
3. Log in to your YouTube account
4. Close the browser when done
5. Account is now saved with cookies

### Step 2: Add a Channel

1. Enter YouTube channel URL in the **Kênh YouTube** (YouTube Channel) section
2. Click **📹 Lấy danh sách video** (Get Video List)
3. System extracts all video IDs from the channel
4. Videos are displayed and saved to config.json

### Step 3: Select Accounts to Scrape

1. In **📋 Chọn tài khoản cần cào hôm nay** section, check the accounts you want to scrape
2. Click **✓ Chọn tất cả** to select all
3. Click **✗ Bỏ chọn tất cả** to deselect all

### Step 4: Start Scraping

1. Click **🚀 Cào tài khoản đã chọn** (Scrape Selected Accounts)
2. Progress bar shows: 1/33, 2/33, etc.
3. Activity log shows detailed updates
4. Results saved to `analytics_results_{AccountName}.json`

### Step 5: Monitor & Stop

- **Watch progress** in real-time
- **Stop anytime** with **⏹️ Dừng** (Stop) button
- **Clear logs** with **🗑️ Xóa log** (Clear Log) button

---

## Configuration

### config.json Structure

```json
{
  "accounts": [
    {
      "name": "My Account",
      "cookies_file": "profile/youtube_cookies_My_Account.json",
      "channels": [
        {
          "url": "https://www.youtube.com/channel/XXXXX",
          "video_ids": ["vid1", "vid2", ...]
        }
      ]
    }
  ],
  "headless": false,
  "auto_continue": true,
  "wait_time": 30
}
```

### Settings Explanation

| Setting | Purpose | Default |
|---------|---------|---------|
| `accounts` | List of all user accounts | Required |
| `headless` | Run browser hidden (no window) | false |
| `auto_continue` | Auto-proceed after login (30s timeout) | true |
| `wait_time` | Seconds to wait for manual login | 30 |

---

## Output Files

After scraping, you'll get:

### Analytics Results
```
analytics_results_{AccountName}.json
```

Contains for each video:
- Video ID
- Views, Impressions, Click-through rate
- Traffic sources breakdown
- Publication date
- Scrape timestamp

### Example Output
```json
[
  {
    "video_id": "dQw4w9WgXcQ",
    "crawl_datetime": "20/11/2025",
    "publish_start_date": "2025-08-13",
    "top_metrics": {
      "Impressions": "15,234",
      "Views": "1,234",
      "Click-through rate": "8.1%"
    },
    "how_viewers_find": {
      "Direct or unknown": "1,234 (45.2%)",
      "Channel pages": "567 (20.8%)"
    }
  }
]
```

---

## Common Tasks

### Add Another Account

1. Click **👤 Tài khoản Google**
2. Log in with different YouTube account
3. New account is automatically saved

### Scrape Specific Accounts Only

1. Uncheck accounts you don't want to scrape
2. Click **🚀 Cào tài khoản đã chọn**
3. Only selected accounts are scraped

### Re-scrape Videos

1. Select the account
2. Click **🚀 Cào tài khoản đã chọn** again
3. New data will overwrite old data in output file

### View Scraping History

Log messages show:
- Which account is being processed
- Current video progress (1/33, 2/33, etc.)
- Any errors encountered
- Final summary with success/error counts

---

## Troubleshooting

### "Cannot find Chrome driver"
- Ensure Chrome/Chromium is installed
- On Linux: `sudo apt-get install chromium-browser`

### "Login timeout"
- Increase `wait_time` in config.json
- Manually proceed faster if auto_continue is ON

### "Connection closed without response"
- YouTube closed the connection (normal)
- Scraper will retry automatically
- Click **⏹️ Dừng** to stop if taking too long

### "No accounts available"
- Add an account first using **👤 Tài khoản Google**
- Ensure config.json has accounts listed

### Scrolling doesn't work
- Use mouse wheel to scroll
- Drag the scrollbar on right side

---

## Tips & Best Practices

### ✅ Do
- Select multiple accounts for batch scraping
- Monitor the progress bar and logs
- Check output files after scraping
- Use Stop button to pause long jobs

### ❌ Don't
- Edit config.json manually unless you know what you're doing
- Delete profile/ folder (contains saved cookies)
- Log out from YouTube while scraping
- Close Chrome window during scraping (let the app handle it)

---

## Advanced Usage

### Command-line Options (Future)

Currently, the GUI is the primary interface. CLI support is coming soon.

### Extending the Code

The code is organized in modules:
- `src/scraper/` - Scraping logic
- `src/gui/` - User interface
- `src/utils/` - Helper utilities

See `docs/DEVELOPMENT.md` for extending functionality.

---

## Getting Help

- **See bug fixes:** `docs/BUG_FIXES.md`
- **Architecture details:** `docs/ARCHITECTURE.md`
- **Development guide:** `docs/DEVELOPMENT.md`
- **Troubleshooting:** `docs/TROUBLESHOOTING.md`

---

## Version Info

- **Current Version:** 2.0
- **Last Updated:** 2025-11-20
- **Python:** 3.8+
- **License:** MIT

---

## What's New

### Version 2.0 (November 2025)
- ✅ Multi-account batch scraping
- ✅ Sequential processing (one account at a time)
- ✅ Account selection panel
- ✅ Fixed progress bar accuracy
- ✅ Made text boxes read-only
- ✅ Enabled mouse wheel scrolling
- ✅ Fixed stop button functionality
- ✅ Refactored code structure

### Next Version (Planned)
- CLI support
- Export to CSV/Excel
- Scheduled scraping
- Data visualization

---

**Ready to get started? Run:**
```bash
python3 src/main.py
```
