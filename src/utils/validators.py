"""
Validation utilities for YouTube Analytics Scraper
"""
import re
from typing import Optional, Tuple
from urllib.parse import urlparse
from .constants import VIDEO_ID_LENGTH, CHANNEL_ID_PREFIX
from .logger import get_logger

logger = get_logger(__name__)


def validate_youtube_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate YouTube channel/video URL
    
    Args:
        url: URL to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"
    
    url = url.strip()
    if not url:
        return False, "URL cannot be empty"
    
    # Supported YouTube URL patterns
    patterns = [
        r'^https?://(www\.)?youtube\.com/@[\w-]+',
        r'^https?://(www\.)?youtube\.com/c/[\w-]+',
        r'^https?://(www\.)?youtube\.com/channel/UC[\w-]+',
        r'^https?://(www\.)?youtube\.com/user/[\w-]+',
        r'^https?://(www\.)?youtube\.com/watch\?v=[\w-]+',
    ]
    
    for pattern in patterns:
        if re.match(pattern, url, re.IGNORECASE):
            return True, None
    
    return False, f"Invalid YouTube URL format: {url}"


def validate_account_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate account name
    
    Args:
        name: Account name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not isinstance(name, str):
        return False, "Account name must be a non-empty string"
    
    name = name.strip()
    if not name:
        return False, "Account name cannot be empty"
    
    # Check for invalid characters (for file names)
    invalid_chars = r'[<>:"/\\|?*]'
    if re.search(invalid_chars, name):
        return False, f"Account name contains invalid characters: {invalid_chars}"
    
    # Check length
    if len(name) > 100:
        return False, "Account name is too long (max 100 characters)"
    
    return True, None


def validate_video_id(video_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate YouTube video ID
    
    Args:
        video_id: Video ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not video_id or not isinstance(video_id, str):
        return False, "Video ID must be a non-empty string"
    
    video_id = video_id.strip()
    
    if len(video_id) != VIDEO_ID_LENGTH:
        return False, f"Video ID must be {VIDEO_ID_LENGTH} characters long"
    
    if video_id.startswith(CHANNEL_ID_PREFIX):
        return False, "This appears to be a channel ID, not a video ID"
    
    # Video IDs typically contain alphanumeric characters, hyphens, and underscores
    if not re.match(r'^[\w-]+$', video_id):
        return False, "Video ID contains invalid characters"
    
    return True, None


def validate_channel_id(channel_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate YouTube channel ID
    
    Args:
        channel_id: Channel ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not channel_id or not isinstance(channel_id, str):
        return False, "Channel ID must be a non-empty string"
    
    channel_id = channel_id.strip()
    
    if not channel_id.startswith(CHANNEL_ID_PREFIX):
        return False, f"Channel ID must start with '{CHANNEL_ID_PREFIX}'"
    
    if len(channel_id) != 24:  # UC + 22 characters
        return False, "Channel ID must be 24 characters long"
    
    return True, None


def sanitize_account_name(name: str) -> str:
    """
    Sanitize account name for use in file names
    
    Args:
        name: Account name to sanitize
        
    Returns:
        Sanitized account name
    """
    if not name:
        return "account_unknown"
    
    # Replace invalid characters with underscore
    sanitized = re.sub(r'[^\w\-_]', '_', name)
    
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure not empty
    if not sanitized:
        sanitized = "account_unknown"
    
    return sanitized

