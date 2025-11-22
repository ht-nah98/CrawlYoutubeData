"""
GUI Configuration Management
"""

import json
import os
from typing import Dict, Any


class GUIConfig:
    """Manages GUI configuration"""
    
    DEFAULT_CONFIG = {
        "backend_url": "http://localhost:8000",
        "api_timeout": 30,
        "theme": "dark",
        "window_size": "1200x800",
        "auto_connect": True,
        "cache_enabled": True,
        "log_level": "INFO"
    }
    
    def __init__(self, config_file: str = "config.json"):
        """
        Initialize configuration
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = self.DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self) -> None:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
    
    def save(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        self.save()
    
    @property
    def backend_url(self) -> str:
        """Get backend URL"""
        return self.get("backend_url", "http://localhost:8000")
    
    @backend_url.setter
    def backend_url(self, value: str):
        """Set backend URL"""
        self.set("backend_url", value)
    
    @property
    def theme(self) -> str:
        """Get theme"""
        return self.get("theme", "dark")
    
    @theme.setter
    def theme(self, value: str):
        """Set theme"""
        self.set("theme", value)
    
    @property
    def window_size(self) -> str:
        """Get window size"""
        return self.get("window_size", "1200x800")
    
    @window_size.setter
    def window_size(self, value: str):
        """Set window size"""
        self.set("window_size", value)
    
    def __repr__(self) -> str:
        return f"<GUIConfig(backend='{self.backend_url}', theme='{self.theme}')>"


# Global configuration instance
config = GUIConfig()
