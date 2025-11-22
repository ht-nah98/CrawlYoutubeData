"""Database connection and session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session

from src.database.config import DatabaseConfig
from src.database.models import Base


class DatabaseConnection:
    """Manages database connection and sessions."""

    def __init__(self, config: DatabaseConfig = None):
        """
        Initialize database connection.

        Args:
            config: DatabaseConfig instance (uses defaults if None)
        """
        self.config = config or DatabaseConfig()
        self.engine = None
        self.SessionLocal = None
        self._init_engine()

    def _init_engine(self) -> None:
        """Initialize SQLAlchemy engine with connection pooling."""
        self.engine = create_engine(
            self.config.url,
            echo=self.config.echo,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_pre_ping=True,  # Verify connections before using them
            pool_recycle=3600,   # Recycle connections after 1 hour
        )

        # Enable foreign keys for SQLite (if used)
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if 'sqlite' in str(self.engine.url):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self) -> None:
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
        print(f"✓ Database tables created successfully at {self.config.database}")

    def drop_tables(self) -> None:
        """Drop all tables from the database (WARNING: Data loss)."""
        Base.metadata.drop_all(bind=self.engine)
        print(f"✓ All database tables dropped from {self.config.database}")

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope around a series of operations.

        Usage:
            with db.session_scope() as session:
                # use session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            from sqlalchemy import text
            with self.session_scope() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"✗ Database health check failed: {e}")
            return False

    def close(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()


# Global database instance
db = DatabaseConnection()
