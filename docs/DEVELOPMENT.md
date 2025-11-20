# Development Guide

**For developers who want to extend or modify the YouTube Analytics Scraper**

---

## Project Structure

```
youtube-analytics-scraper/
├── src/
│   ├── main.py                    # GUI entry point
│   ├── gui/
│   │   └── app.py                 # YouTubeScraperGUI class
│   ├── scraper/
│   │   ├── youtube.py             # YouTubeAnalyticsScraper class
│   │   └── channel.py             # Channel operations
│   └── utils/
│       ├── config.py              # Configuration management
│       ├── logger.py              # Logging utilities
│       ├── chrome.py              # Chrome WebDriver
│       ├── cookies.py             # Cookie management
│       ├── validators.py          # Input validation
│       ├── tracker.py             # Scraping history
│       └── constants.py           # Constants
├── docs/
│   ├── QUICK_START.md             # User guide
│   ├── DEVELOPMENT.md             # This file
│   ├── ARCHITECTURE.md            # System design
│   ├── BUG_FIXES.md               # Bug documentation
│   └── TROUBLESHOOTING.md         # Troubleshooting
├── profile/                       # User data (cookies, etc.)
└── config.json                    # Configuration file
```

---

## Key Modules

### src/gui/app.py
**YouTubeScraperGUI Class**

Main GUI application. Handles:
- Window creation and layout
- Account selection and management
- Channel configuration
- Scraping control and monitoring
- Progress tracking
- Activity logging

**Key Methods:**
- `__init__()` - Initialize GUI
- `create_widgets()` - Build UI
- `start_batch_scraping()` - Start scraping job
- `batch_scraping_worker()` - Background scraping thread
- `update_progress()` - Update progress bar
- `log_message()` - Add log entry

**To extend:**
Add new methods for additional features. Keep UI logic in this module.

---

### src/scraper/youtube.py
**YouTubeAnalyticsScraper Class**

Core scraping engine. Handles:
- Chrome WebDriver initialization
- Google login/authentication
- Cookie management
- Analytics data extraction
- Error handling and retries

**Key Methods:**
- `__init__()` - Initialize scraper
- `init_driver()` - Setup Chrome WebDriver
- `login_google()` - Authenticate user
- `get_video_analytics()` - Scrape single video
- `scrape_multiple_videos()` - Batch scrape videos
- `save_results()` - Export to JSON

**To extend:**
Add new scraping methods here. Each method should focus on extracting specific data.

---

### src/scraper/channel.py
**Channel Video ID Extraction**

Handles:
- YouTube channel URL validation
- Video ID extraction using yt-dlp
- Account switching
- Config updates

**Key Functions:**
- `get_channel_video_ids()` - Extract video IDs
- `login_and_save_cookies()` - Google OAuth
- `save_to_config()` - Update config.json

**To extend:**
Add functions for additional channel operations (e.g., playlist extraction, video filtering).

---

### src/utils/config.py
**Configuration Management**

Handles:
- config.json reading/writing
- Account management
- Channel configuration
- Settings validation

**Key Class: ConfigManager**
- `load()` - Read config
- `save()` - Write config
- `get()` / `set()` - Get/set values
- `get_accounts()` - Get all accounts
- `add_account()` - Add new account

**To extend:**
Add new config keys for additional features.

---

## Development Workflow

### Adding a New Feature

1. **Identify the module** - Where does this feature belong?
   - GUI → `src/gui/app.py`
   - Scraping → `src/scraper/youtube.py`
   - Utilities → `src/utils/`

2. **Write the code** - Add method/function to appropriate module

3. **Add error handling** - Use try/except/finally pattern

4. **Test locally** - Verify functionality

5. **Update docs** - Document new feature in `docs/`

6. **Update CHANGELOG** - Add entry to version history

---

## Example: Adding CSV Export Feature

### 1. Create export method in src/scraper/youtube.py

```python
def export_to_csv(self, results, filename):
    """Export results to CSV format"""
    import csv

    try:
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'video_id', 'views', 'impressions', 'ctr', 'crawl_datetime'
            ])
            writer.writeheader()

            for result in results:
                writer.writerow({
                    'video_id': result.get('video_id'),
                    'views': result.get('top_metrics', {}).get('Views'),
                    'impressions': result.get('top_metrics', {}).get('Impressions'),
                    'ctr': result.get('top_metrics', {}).get('Click-through rate'),
                    'crawl_datetime': result.get('crawl_datetime')
                })

        return filename
    except Exception as e:
        logger.error(f"Failed to export CSV: {str(e)}")
        raise
```

### 2. Add GUI button in src/gui/app.py

```python
# In create_control_section()
export_csv_btn = create_button(
    button_frame,
    "📊 Export CSV",
    self.export_to_csv,
    ModernColors.INFO,
    "#1E90FF",
    150
)
export_csv_btn.pack(side="left", padx=8)

# Add method
def export_to_csv(self):
    """Export latest results to CSV"""
    if not self.current_results:
        messagebox.showwarning("No Data", "No scraping results to export")
        return

    try:
        filename = f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        scraper = YouTubeAnalyticsScraper()
        scraper.export_to_csv(self.current_results, filename)
        self.log_message(f"✓ Exported to {filename}", "SUCCESS")
    except Exception as e:
        messagebox.showerror("Export Error", str(e))
        self.log_message(f"✗ Export failed: {str(e)}", "ERROR")
```

### 3. Update config for CSV settings

In `src/utils/config.py`, add:
```python
def get_export_format(self):
    return self.get('export_format', 'json')  # Default to JSON

def set_export_format(self, format):
    self.set('export_format', format)
```

### 4. Test and document

- Test CSV export with sample data
- Update `docs/QUICK_START.md` with CSV export instructions
- Add entry to CHANGELOG

---

## Testing Guidelines

### Unit Testing

Test individual functions in isolation:

```python
def test_export_to_csv():
    """Test CSV export functionality"""
    scraper = YouTubeAnalyticsScraper()

    test_data = [
        {
            'video_id': 'test123',
            'top_metrics': {'Views': '100', 'Impressions': '200'},
            'crawl_datetime': '20/11/2025'
        }
    ]

    filename = scraper.export_to_csv(test_data, 'test_export.csv')

    assert os.path.exists(filename)
    # Verify CSV content...
```

### Integration Testing

Test features working together:

```python
def test_full_workflow():
    """Test complete scraping workflow"""
    # 1. Load config
    config = ConfigManager()
    accounts = config.get_accounts()

    # 2. Start scraping
    scraper = YouTubeAnalyticsScraper()
    results = scraper.scrape_multiple_videos(['vid1', 'vid2'])

    # 3. Export results
    filename = scraper.save_results(results)

    assert os.path.exists(filename)
```

### Error Path Testing

Always test error scenarios:

```python
def test_invalid_video_id():
    """Test handling of invalid video ID"""
    scraper = YouTubeAnalyticsScraper()

    with pytest.raises(ValueError):
        scraper.get_video_analytics('invalid!!!id')
```

---

## Code Style Guidelines

### Naming Conventions

```python
# Classes: PascalCase
class YouTubeAnalyticsScraper:
    pass

# Functions/methods: snake_case
def get_video_analytics(self, video_id):
    pass

# Constants: UPPER_CASE
TIMEOUT_SECONDS = 30
MAX_RETRIES = 3

# Private methods: _leading_underscore
def _validate_cookies(self):
    pass
```

### Documentation

```python
def get_video_analytics(self, video_id, headless=False):
    """
    Extract analytics data for a single video

    Args:
        video_id (str): YouTube video ID
        headless (bool): Run browser in headless mode

    Returns:
        dict: Analytics data including views, impressions, etc.

    Raises:
        ValueError: If video_id is invalid
        SeleniumException: If scraping fails
    """
    pass
```

### Error Handling

```python
# Use try/finally for resource cleanup
driver = None
try:
    driver = webdriver.Chrome()
    # ... do something ...
except Exception as e:
    logger.error(f"Error: {str(e)}")
    raise
finally:
    if driver:
        driver.quit()  # Always cleanup
```

---

## Debugging Tips

### Enable Logging

```python
import logging
from src.utils.logger import setup_logger

logger = setup_logger("module_name")
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

### Add Print Debugging

```python
print(f"DEBUG: video_id={video_id}, headless={headless}")
```

### Use Breakpoints (with debugger)

```python
import pdb; pdb.set_trace()  # Will pause execution here
```

---

## Performance Considerations

### Batch Processing

Use ThreadPoolExecutor for parallel tasks:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(scraper.get_video_analytics, vid)
        for vid in video_ids
    ]
    results = [f.result() for f in futures]
```

### Memory Management

```python
# Clear large datasets when done
results = []
for video_id in video_ids:
    result = scraper.get_video_analytics(video_id)
    results.append(result)

# Process and clear
save_results(results)
del results  # Free memory
```

### Resource Limits

```python
# Set timeouts to prevent hanging
driver.set_page_load_timeout(30)
driver.set_script_timeout(30)
```

---

## Common Tasks

### Adding a New Setting

1. Add to `config.json` default
2. Update `src/utils/config.py` with getter/setter
3. Add GUI control in `src/gui/app.py`
4. Use the setting in relevant module

### Fixing a Bug

1. Create test that reproduces bug
2. Identify root cause
3. Implement fix
4. Verify test passes
5. Check for similar issues
6. Document fix in `docs/BUG_FIXES.md`

### Optimizing Performance

1. Profile code with `cProfile`
2. Identify bottlenecks
3. Optimize hot paths (use generators, cache, etc.)
4. Benchmark improvements
5. Update documentation

---

## Resources

- **Selenium Documentation:** https://www.selenium.dev/documentation/
- **tkinter Guide:** https://docs.python.org/3/library/tkinter.html
- **yt-dlp Docs:** https://github.com/yt-dlp/yt-dlp/tree/master/yt_dlp
- **Python Best Practices:** https://pep8.org/

---

## Getting Help

- **Check existing bugs:** `docs/BUG_FIXES.md`
- **Read architecture:** `docs/ARCHITECTURE.md`
- **See examples:** Look at similar methods in codebase
- **Debug output:** Enable logging, check logs

---

**Happy coding! Feel free to extend and improve the scraper!**
