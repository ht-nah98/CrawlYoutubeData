"""FastAPI dependencies."""

from sqlalchemy.orm import Session

from src.database.connection import db


def get_db() -> Session:
    """
    Dependency to get database session.

    Usage in routes:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            # use db session
    """
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()
