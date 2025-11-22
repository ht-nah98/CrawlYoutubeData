"""Database configuration for PostgreSQL connection."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class DatabaseConfig:
    """Database configuration class."""

    def __init__(
        self,
        host: str = None,
        port: int = None,
        user: str = None,
        password: str = None,
        database: str = None,
        echo: bool = False,
        pool_size: int = 20,
        max_overflow: int = 10
    ):
        """
        Initialize database configuration.

        Uses environment variables by default, falls back to provided values.

        Environment variables:
        - DB_HOST: Database host (default: localhost)
        - DB_PORT: Database port (default: 5432)
        - DB_USER: Database user (default: postgres)
        - DB_PASSWORD: Database password
        - DB_NAME: Database name (default: youtube_analytics)
        - DB_ECHO: Enable SQL query logging (default: false)
        """
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or int(os.getenv('DB_PORT', 5432))
        self.user = user or os.getenv('DB_USER', 'postgres')
        self.password = password or os.getenv('DB_PASSWORD', '')
        self.database = database or os.getenv('DB_NAME', 'youtube_analytics')
        self.echo = echo or os.getenv('DB_ECHO', 'false').lower() == 'true'
        self.pool_size = pool_size
        self.max_overflow = max_overflow

    @property
    def url(self) -> str:
        """Get the SQLAlchemy database URL."""
        # Handle Unix socket (host starts with /)
        if self.host.startswith('/'):
            if self.password:
                return f"postgresql://{self.user}:{self.password}@/{self.database}?host={self.host}"
            return f"postgresql://{self.user}@/{self.database}?host={self.host}"
        # Handle TCP connection
        if self.password:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"postgresql://{self.user}@{self.host}:{self.port}/{self.database}"

    @property
    def async_url(self) -> str:
        """Get the async SQLAlchemy database URL."""
        if self.password:
            return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"postgresql+asyncpg://{self.user}@{self.host}:{self.port}/{self.database}"

    def __repr__(self) -> str:
        """String representation of database config."""
        return (
            f"DatabaseConfig("
            f"host={self.host}, "
            f"port={self.port}, "
            f"user={self.user}, "
            f"database={self.database}"
            f")"
        )


# Default configuration instance
default_config = DatabaseConfig()
