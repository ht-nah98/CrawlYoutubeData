"""
Constants for YouTube Analytics Scraper
"""
import os

# File paths
CONFIG_FILE = 'config.json'
PROFILE_DIR = 'profile'
COOKIES_FILE_PREFIX = 'youtube_cookies_'
DEFAULT_COOKIES_FILE = os.path.join(PROFILE_DIR, 'youtube_cookies.json')

# Timeouts (seconds)
DEFAULT_TIMEOUT = 30
HEADLESS_TIMEOUT = 45
PAGE_LOAD_TIMEOUT = 30
ELEMENT_WAIT_TIMEOUT = 10
COOKIE_LOAD_TIMEOUT = 5

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 3  # seconds
SCROLL_RETRIES = 3
SCROLL_ATTEMPTS = 2

# Sleep delays (seconds)
DEFAULT_SLEEP = 2
AFTER_LOGIN_SLEEP = 5
AFTER_PAGE_LOAD_SLEEP = 3
BETWEEN_VIDEOS_SLEEP = 2
AFTER_COOKIE_LOAD_SLEEP = 2

# Chrome options
CHROME_WINDOW_SIZE = '1920,1080'
CHROME_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# YouTube URLs
YOUTUBE_BASE_URL = 'https://www.youtube.com'
YOUTUBE_STUDIO_URL = 'https://studio.youtube.com'
YOUTUBE_ANALYTICS_URL = 'https://studio.youtube.com/channel/{channel_id}/analytics'
GOOGLE_LOGIN_URL = 'https://accounts.google.com'

# Default settings
DEFAULT_AUTO_CONTINUE = True
DEFAULT_WAIT_TIME = 30
DEFAULT_AUTO_SCRAPING_INTERVAL = 30  # minutes
DEFAULT_HEADLESS = False
DEFAULT_AUTO_SCRAPING_ENABLED = False
DEFAULT_AUTO_SCRAPING_HEADLESS = True

# Logging
LOG_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'
LOG_DATE_FORMAT = '%H:%M:%S'
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# Video ID validation
VIDEO_ID_LENGTH = 11
CHANNEL_ID_PREFIX = 'UC'

# Date formats
DATE_FORMAT_VI = '%d/%m/%Y'
DATE_FORMAT_ISO = '%Y-%m-%d'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'



