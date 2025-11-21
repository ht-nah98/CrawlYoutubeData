"""Database module for YouTube Analytics backend."""

from src.database.config import DatabaseConfig, default_config
from src.database.connection import DatabaseConnection, db
from src.database.models import (
    Base,
    Account,
    Channel,
    Video,
    VideoAnalytics,
    TrafficSource,
    ScrapingHistory,
)

__all__ = [
    'DatabaseConfig',
    'default_config',
    'DatabaseConnection',
    'db',
    'Base',
    'Account',
    'Channel',
    'Video',
    'VideoAnalytics',
    'TrafficSource',
    'ScrapingHistory',
]
