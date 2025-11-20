"""
Cookie Manager for YouTube Analytics Scraper
Handles cookie loading, saving, and validation
"""
import json
import os
import time
from typing import List, Dict, Optional, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .constants import (
    PROFILE_DIR, COOKIES_FILE_PREFIX, DEFAULT_COOKIES_FILE,
    YOUTUBE_BASE_URL, GOOGLE_LOGIN_URL, YOUTUBE_STUDIO_URL,
    AFTER_COOKIE_LOAD_SLEEP, ELEMENT_WAIT_TIMEOUT
)
from .logger import get_logger
from .validators import sanitize_account_name

logger = get_logger(__name__)


class CookieManager:
    """Manages YouTube/Google cookies"""
    
    def __init__(self, cookies_file: Optional[str] = None, account_name: Optional[str] = None):
        """
        Initialize CookieManager
        
        Args:
            cookies_file: Path to cookies file
            account_name: Account name (used to generate cookies_file if not provided)
        """
        if cookies_file:
            self.cookies_file = cookies_file
        elif account_name:
            safe_name = sanitize_account_name(account_name)
            self.cookies_file = os.path.join(PROFILE_DIR, f'{COOKIES_FILE_PREFIX}{safe_name}.json')
        else:
            self.cookies_file = DEFAULT_COOKIES_FILE
        
        # Ensure profile directory exists
        os.makedirs(PROFILE_DIR, exist_ok=True)
    
    def save_cookies(self, driver: webdriver.Chrome) -> bool:
        """
        Save cookies from driver to file
        
        Args:
            driver: Chrome WebDriver instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cookies = driver.get_cookies()
            
            # Ensure directory exists
            cookies_dir = os.path.dirname(self.cookies_file)
            if cookies_dir and not os.path.exists(cookies_dir):
                os.makedirs(cookies_dir, exist_ok=True)
            
            with open(self.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(cookies)} cookies to {self.cookies_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving cookies: {e}")
            return False
    
    def load_cookies(self, driver: webdriver.Chrome, auto_relogin: bool = True,
                    headless: bool = False) -> bool:
        """
        Load cookies from file to driver
        
        Args:
            driver: Chrome WebDriver instance
            auto_relogin: Automatically re-login if cookies are invalid
            headless: Running in headless mode
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.cookies_file):
                logger.warning(f"Cookies file not found: {self.cookies_file}")
                if auto_relogin:
                    return self._perform_login(driver, headless)
                return False
            
            # Read cookies from file
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                file_text = f.read().strip()
                cookies = None
                
                # Try JSON first
                try:
                    cookies = json.loads(file_text)
                except json.JSONDecodeError:
                    # Fallback: parse as cookie header format
                    cookies = self._parse_cookie_header(file_text)
            
            if not cookies:
                logger.warning("Cookies file is empty")
                if auto_relogin:
                    return self._perform_login(driver, headless)
                return False
            
            logger.info(f"Loading {len(cookies)} cookies from {self.cookies_file}")
            
            # Categorize cookies by domain
            youtube_cookies = []
            google_cookies = []
            other_cookies = []
            
            for cookie in cookies:
                if not isinstance(cookie, dict):
                    continue
                
                domain = cookie.get('domain', '').lower()
                if not domain:
                    cookie['domain'] = '.youtube.com'
                    youtube_cookies.append(cookie)
                elif 'youtube.com' in domain:
                    youtube_cookies.append(cookie)
                elif 'google.com' in domain:
                    google_cookies.append(cookie)
                else:
                    other_cookies.append(cookie)
            
            logger.debug(f"Cookies: {len(youtube_cookies)} YouTube, "
                        f"{len(google_cookies)} Google, {len(other_cookies)} other")
            
            # Load cookies for each domain
            domains_to_load = [
                (YOUTUBE_BASE_URL, youtube_cookies),
                (GOOGLE_LOGIN_URL, google_cookies),
                (YOUTUBE_BASE_URL, other_cookies),
            ]
            
            total_added = 0
            total_failed = 0
            
            for url, cookie_list in domains_to_load:
                if not cookie_list:
                    continue
                
                try:
                    logger.debug(f"Loading cookies for {url}...")
                    driver.get(url)
                    time.sleep(AFTER_COOKIE_LOAD_SLEEP)
                    
                    added = 0
                    failed = 0
                    
                    for cookie in cookie_list:
                        try:
                            cookie_to_add = cookie.copy()
                            
                            # Validate required fields
                            if 'name' not in cookie_to_add or 'value' not in cookie_to_add:
                                failed += 1
                                continue
                            
                            # Handle domain
                            domain = cookie_to_add.get('domain', '')
                            if not domain:
                                if 'youtube.com' in url:
                                    cookie_to_add['domain'] = '.youtube.com'
                                elif 'google.com' in url:
                                    cookie_to_add['domain'] = '.google.com'
                            
                            # Normalize domain
                            if domain and not domain.startswith('.'):
                                if 'youtube.com' in domain and domain != 'youtube.com':
                                    cookie_to_add['domain'] = '.youtube.com'
                                elif 'google.com' in domain and domain != 'google.com':
                                    cookie_to_add['domain'] = '.google.com'
                            
                            # Handle expiry
                            if 'expiry' in cookie_to_add:
                                expiry = cookie_to_add['expiry']
                                if isinstance(expiry, (int, float)):
                                    if expiry < time.time():
                                        logger.debug(f"Cookie {cookie_to_add.get('name')} expired, skipping")
                                        failed += 1
                                        continue
                                    cookie_to_add['expiry'] = int(expiry)
                                else:
                                    del cookie_to_add['expiry']
                            
                            # Set default path
                            if 'path' not in cookie_to_add:
                                cookie_to_add['path'] = '/'
                            
                            # Remove invalid keys for Selenium
                            invalid_keys = ['httpOnly', 'sameSite', 'storeId', 'hostOnly']
                            for key in invalid_keys:
                                cookie_to_add.pop(key, None)
                            
                            driver.add_cookie(cookie_to_add)
                            added += 1
                            
                        except Exception as e:
                            logger.debug(f"Failed to add cookie '{cookie.get('name', 'unknown')}': {e}")
                            failed += 1
                    
                    logger.debug(f"Loaded {added} cookies for {url}, {failed} failed")
                    total_added += added
                    total_failed += failed
                    
                except Exception as e:
                    logger.warning(f"Error loading cookies for {url}: {e}")
            
            logger.info(f"Total: {total_added} cookies loaded, {total_failed} failed")
            
            # Verify cookies are applied
            driver.get(YOUTUBE_BASE_URL)
            time.sleep(AFTER_COOKIE_LOAD_SLEEP)
            
            if self._verify_login(driver):
                logger.info("Cookies loaded and verified successfully")
                return True
            else:
                logger.warning("Cookies may be invalid or expired")
                if auto_relogin:
                    return self._perform_login(driver, headless)
                return False
                
        except FileNotFoundError:
            logger.warning(f"Cookies file not found: {self.cookies_file}")
            if auto_relogin:
                return self._perform_login(driver, headless)
            return False
        except Exception as e:
            logger.error(f"Error loading cookies: {e}")
            if auto_relogin:
                return self._perform_login(driver, headless)
            return False
    
    def _parse_cookie_header(self, header_text: str) -> List[Dict[str, Any]]:
        """
        Parse cookie header format ("a=1; b=2; ...") to Selenium cookie format
        
        Args:
            header_text: Cookie header string
            
        Returns:
            List of cookie dictionaries
        """
        try:
            # Remove user-agent if present (after |)
            header = header_text.split('|', 1)[0].strip()
            if not header:
                return []
            
            pairs = [p.strip() for p in header.split(';') if p.strip()]
            cookies = []
            
            for pair in pairs:
                if '=' not in pair:
                    continue
                
                name, value = pair.split('=', 1)
                name = name.strip()
                value = value.strip()
                
                if not name:
                    continue
                
                cookies.append({
                    'name': name,
                    'value': value,
                    'domain': '.youtube.com',
                    'path': '/',
                })
            
            return cookies
        except Exception:
            return []
    
    def _verify_login(self, driver: webdriver.Chrome) -> bool:
        """
        Verify if user is logged in
        
        Args:
            driver: Chrome WebDriver instance
            
        Returns:
            True if logged in, False otherwise
        """
        try:
            current_url = driver.current_url.lower()
            page_source = driver.page_source.lower()
            
            # Check for redirect to login
            if 'accounts.google.com' in current_url or 'signin' in current_url:
                return False
            
            # Check for login indicators
            logged_in_indicators = [
                'avatar' in page_source,
                ('account' in page_source and 'menu' in page_source),
                'youtube.com' in current_url and 'sign in' not in page_source
            ]
            
            return any(logged_in_indicators)
        except Exception as e:
            logger.debug(f"Error verifying login: {e}")
            return False
    
    def _perform_login(self, driver: webdriver.Chrome, headless: bool = False) -> bool:
        """
        Perform login (placeholder - should be implemented by caller)
        
        Args:
            driver: Chrome WebDriver instance
            headless: Running in headless mode
            
        Returns:
            True if login successful, False otherwise
        """
        logger.info("Auto-login not implemented in CookieManager")
        return False
    
    def delete_cookies_file(self) -> bool:
        """
        Delete cookies file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(self.cookies_file):
                os.remove(self.cookies_file)
                logger.info(f"Deleted cookies file: {self.cookies_file}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting cookies file: {e}")
            return False
    
    def cookies_file_exists(self) -> bool:
        """
        Check if cookies file exists
        
        Returns:
            True if exists, False otherwise
        """
        return os.path.exists(self.cookies_file)



