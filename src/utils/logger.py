"""
Logging utility for YouTube Analytics Scraper
Replaces print statements with proper logging
"""
import logging
import sys
from typing import Optional
from .constants import LOG_FORMAT, LOG_DATE_FORMAT

# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logger(name: str = 'youtube_scraper', level: int = logging.INFO, 
                 log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup and configure logger
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    global _logger
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not setup file logging: {e}")
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    _logger = logger
    return logger


def get_logger(name: str = 'youtube_scraper') -> logging.Logger:
    """
    Get logger instance (creates if not exists)
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    global _logger
    
    if _logger is None:
        return setup_logger(name)
    
    return _logger


# Convenience functions for backward compatibility
def log_info(message: str):
    """Log info message"""
    get_logger().info(message)


def log_warning(message: str):
    """Log warning message"""
    get_logger().warning(message)


def log_error(message: str):
    """Log error message"""
    get_logger().error(message)


def log_debug(message: str):
    """Log debug message"""
    get_logger().debug(message)


def log_success(message: str):
    """Log success message (as info with prefix)"""
    get_logger().info(f"✓ {message}")



