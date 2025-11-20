"""
Chrome Driver Manager for YouTube Analytics Scraper
Centralizes Chrome driver initialization and configuration
"""
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

from .constants import (
    CHROME_WINDOW_SIZE, CHROME_USER_AGENT, MAX_RETRIES, RETRY_DELAY,
    DEFAULT_TIMEOUT, HEADLESS_TIMEOUT
)
from .logger import get_logger

logger = get_logger(__name__)


class ChromeDriverManager:
    """Manages Chrome WebDriver instances"""
    
    @staticmethod
    def create_options(headless: bool = False, user_data_dir: Optional[str] = None) -> Options:
        """
        Create Chrome options with standard configuration
        
        Args:
            headless: Run in headless mode
            user_data_dir: Optional user data directory for profile
            
        Returns:
            Configured Chrome Options
        """
        options = Options()
        
        if headless:
            options.add_argument('--headless')
            options.add_argument('--disable-web-security')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--no-first-run')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument(f'--window-size={CHROME_WINDOW_SIZE}')
            options.add_argument(f'--user-agent={CHROME_USER_AGENT}')
        else:
            options.add_argument(f'--window-size={CHROME_WINDOW_SIZE}')
        
        # Common options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # GPU and performance options
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-gpu-sandbox')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-webgl')
        options.add_argument('--disable-webgl2')
        options.add_argument('--disable-3d-apis')
        options.add_argument('--use-gl=swiftshader')
        options.add_argument('--disable-accelerated-2d-canvas')
        options.add_argument('--disable-accelerated-video-decode')
        options.add_argument('--disable-accelerated-video-encode')
        options.add_argument('--disable-gpu-compositing')
        options.add_argument('--disable-gpu-rasterization')
        
        # Background and performance
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        
        # Logging
        options.add_argument('--log-level=3')
        
        # Notifications
        prefs = {
            "profile.default_content_setting_values.notifications": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        # User data dir (for profile isolation)
        if user_data_dir:
            options.add_argument(f'--user-data-dir={user_data_dir}')
        
        return options
    
    @staticmethod
    def create_driver(headless: bool = False, user_data_dir: Optional[str] = None,
                     use_webdriver_manager: bool = True) -> webdriver.Chrome:
        """
        Create Chrome WebDriver with retry mechanism
        
        Args:
            headless: Run in headless mode
            user_data_dir: Optional user data directory
            use_webdriver_manager: Use webdriver-manager for automatic driver management
            
        Returns:
            Chrome WebDriver instance
            
        Raises:
            WebDriverException: If driver creation fails after retries
        """
        options = ChromeDriverManager.create_options(headless, user_data_dir)
        
        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"Creating Chrome driver (attempt {attempt + 1}/{MAX_RETRIES})...")
                
                # Try with webdriver-manager first if enabled
                if use_webdriver_manager:
                    try:
                        from webdriver_manager.chrome import ChromeDriverManager as WDM
                        service = Service(WDM().install())
                        driver = webdriver.Chrome(service=service, options=options)
                        logger.debug("Chrome driver created using webdriver-manager")
                    except ImportError:
                        logger.warning("webdriver-manager not available, using default Chrome driver")
                        driver = webdriver.Chrome(options=options)
                else:
                    driver = webdriver.Chrome(options=options)
                
                # Wait for driver to stabilize
                time.sleep(2)
                
                # Verify driver is working
                try:
                    _ = driver.current_url
                except Exception:
                    raise WebDriverException("Chrome driver closed immediately after creation")
                
                if not headless:
                    driver.maximize_window()
                
                logger.info("Chrome driver created successfully")
                return driver
                
            except Exception as e:
                logger.warning(f"Failed to create Chrome driver (attempt {attempt + 1}): {e}")
                
                # Cleanup failed driver
                try:
                    if 'driver' in locals():
                        driver.quit()
                except:
                    pass
                
                if attempt < MAX_RETRIES - 1:
                    logger.debug(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    raise WebDriverException(
                        f"Failed to create Chrome driver after {MAX_RETRIES} attempts: {e}"
                    )
        
        # Should not reach here, but just in case
        raise WebDriverException("Failed to create Chrome driver")
    
    @staticmethod
    def add_stealth_scripts(driver: webdriver.Chrome) -> None:
        """
        Add scripts to make browser less detectable
        
        Args:
            driver: Chrome WebDriver instance
        """
        try:
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                '''
            })
            logger.debug("Added stealth scripts to Chrome driver")
        except Exception as e:
            logger.warning(f"Could not add stealth scripts: {e}")



