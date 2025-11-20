"""
Config Manager for YouTube Analytics Scraper
Handles reading, writing, and validation of config.json
"""
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from .constants import CONFIG_FILE, DEFAULT_AUTO_CONTINUE, DEFAULT_WAIT_TIME, \
    DEFAULT_AUTO_SCRAPING_INTERVAL, DEFAULT_HEADLESS, DEFAULT_AUTO_SCRAPING_ENABLED, \
    DEFAULT_AUTO_SCRAPING_HEADLESS
from .logger import get_logger

logger = get_logger(__name__)


class ConfigManager:
    """Manages application configuration"""
    
    def __init__(self, config_file: str = CONFIG_FILE):
        """
        Initialize ConfigManager
        
        Args:
            config_file: Path to config file
        """
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> Dict[str, Any]:
        """
        Load config from file
        
        Returns:
            Config dictionary
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.debug(f"Loaded config from {self.config_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config file: {e}")
                self._config = self._get_default_config()
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                self._config = self._get_default_config()
        else:
            logger.info(f"Config file not found, using defaults")
            self._config = self._get_default_config()
            self.save()
        
        return self._config
    
    def save(self) -> bool:
        """
        Save config to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            config_dir = os.path.dirname(self.config_file)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
            logger.debug(f"Saved config to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get config value
        
        Args:
            key: Config key (supports dot notation, e.g., 'accounts.0.name')
            default: Default value if key not found
            
        Returns:
            Config value or default
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                if isinstance(value, dict):
                    value = value[k]
                elif isinstance(value, list):
                    value = value[int(k)]
                else:
                    return default
            return value
        except (KeyError, IndexError, ValueError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        Set config value
        
        Args:
            key: Config key (supports dot notation)
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        keys = key.split('.')
        config = self._config
        
        try:
            # Navigate to parent dict/list
            for k in keys[:-1]:
                if isinstance(config, dict):
                    if k not in config:
                        config[k] = {}
                    config = config[k]
                elif isinstance(config, list):
                    config = config[int(k)]
            
            # Set value
            final_key = keys[-1]
            if isinstance(config, dict):
                config[final_key] = value
            elif isinstance(config, list):
                config[int(final_key)] = value
            else:
                return False
            
            return True
        except (KeyError, IndexError, ValueError, TypeError) as e:
            logger.error(f"Error setting config key '{key}': {e}")
            return False
    
    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Get all accounts
        
        Returns:
            List of account dictionaries
        """
        return self.get('accounts', [])
    
    def get_account(self, account_name: str) -> Optional[Dict[str, Any]]:
        """
        Get account by name
        
        Args:
            account_name: Account name
            
        Returns:
            Account dictionary or None
        """
        accounts = self.get_accounts()
        for account in accounts:
            if account.get('name') == account_name:
                return account
        return None
    
    def add_account(self, account_name: str, cookies_file: str) -> bool:
        """
        Add or update account
        
        Args:
            account_name: Account name
            cookies_file: Path to cookies file
            
        Returns:
            True if successful, False otherwise
        """
        accounts = self.get_accounts()
        
        # Check if account exists
        for account in accounts:
            if account.get('name') == account_name:
                account['cookies_file'] = cookies_file
                if 'channels' not in account:
                    account['channels'] = []
                self.save()
                logger.info(f"Updated account: {account_name}")
                return True
        
        # Add new account
        new_account = {
            'name': account_name,
            'cookies_file': cookies_file,
            'channels': []
        }
        accounts.append(new_account)
        self.set('accounts', accounts)
        self.save()
        logger.info(f"Added new account: {account_name}")
        return True
    
    def add_channel_to_account(self, account_name: str, channel_url: str, 
                               video_ids: List[str], output_file: Optional[str] = None) -> bool:
        """
        Add or update channel in account
        
        Args:
            account_name: Account name
            channel_url: Channel URL
            video_ids: List of video IDs
            output_file: Optional output file path
            
        Returns:
            True if successful, False otherwise
        """
        account = self.get_account(account_name)
        if not account:
            logger.error(f"Account '{account_name}' not found")
            return False
        
        if 'channels' not in account:
            account['channels'] = []
        
        # Normalize channel URL
        normalized_url = channel_url.replace('/videos', '').rstrip('/')
        
        # Find existing channel
        for channel in account['channels']:
            if channel.get('url', '').replace('/videos', '').rstrip('/') == normalized_url:
                # Merge video IDs (avoid duplicates)
                existing_ids = set(channel.get('video_ids', []))
                new_ids = [vid for vid in video_ids if vid not in existing_ids]
                channel['video_ids'].extend(new_ids)
                channel['video_ids'] = list(dict.fromkeys(channel['video_ids']))  # Remove duplicates
                
                if output_file:
                    channel['output_file'] = output_file
                
                self.save()
                logger.info(f"Updated channel in account '{account_name}': {normalized_url}")
                return True
        
        # Add new channel
        new_channel = {
            'url': normalized_url,
            'video_ids': video_ids.copy()
        }
        if output_file:
            new_channel['output_file'] = output_file
        
        account['channels'].append(new_channel)
        self.save()
        logger.info(f"Added new channel to account '{account_name}': {normalized_url}")
        return True
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get application settings
        
        Returns:
            Settings dictionary
        """
        return {
            'headless': self.get('headless', DEFAULT_HEADLESS),
            'auto_continue': self.get('auto_continue', DEFAULT_AUTO_CONTINUE),
            'wait_time': self.get('wait_time', DEFAULT_WAIT_TIME),
            'auto_scraping_enabled': self.get('auto_scraping_enabled', DEFAULT_AUTO_SCRAPING_ENABLED),
            'auto_scraping_interval': self.get('auto_scraping_interval', DEFAULT_AUTO_SCRAPING_INTERVAL),
            'auto_scraping_headless': self.get('auto_scraping_headless', DEFAULT_AUTO_SCRAPING_HEADLESS),
        }
    
    def update_settings(self, **kwargs) -> bool:
        """
        Update application settings
        
        Args:
            **kwargs: Settings to update
            
        Returns:
            True if successful, False otherwise
        """
        for key, value in kwargs.items():
            self.set(key, value)
        return self.save()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'accounts': [],
            'headless': DEFAULT_HEADLESS,
            'auto_continue': DEFAULT_AUTO_CONTINUE,
            'wait_time': DEFAULT_WAIT_TIME,
            'auto_scraping_enabled': DEFAULT_AUTO_SCRAPING_ENABLED,
            'auto_scraping_interval': DEFAULT_AUTO_SCRAPING_INTERVAL,
            'auto_scraping_headless': DEFAULT_AUTO_SCRAPING_HEADLESS,
        }
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get full config dictionary"""
        return self._config.copy()



