# Developer Guide

Quick reference for developers working with the YouTube Analytics Backend.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                      │
│  (REST API, routing, request validation)                    │
│                    src/api/main.py                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                   Route Handlers                            │
│  (accounts, channels, videos, analytics)                   │
│                 src/api/routes/*.py                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                SQLAlchemy ORM Layer                         │
│        (Database abstraction, models)                       │
│                src/database/models.py                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│                 PostgreSQL Database                         │
│            (Persistent data storage)                        │
│                  youtube_analytics                          │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Database Models (`src/database/models.py`)

```python
from src.database.models import Account, Video, VideoAnalytics

# Create new instances
account = Account(name="Beau", cookies_file="path/to/cookies.json")
video = Video(video_id="dQw4w9WgXcQ", title="Test Video")
analytics = VideoAnalytics(
    video_id="dQw4w9WgXcQ",
    account_id=1,
    views=100,
    impressions=1000
)

# Query
account = session.query(Account).filter(Account.name == "Beau").first()
videos = session.query(Video).filter(Video.channel_id == 1).all()
```

### 2. Database Connection (`src/database/connection.py`)

```python
from src.database.connection import db

# Get session
session = db.get_session()

# Use context manager (recommended)
with db.session_scope() as session:
    # Operations here
    pass

# Create tables
db.create_tables()

# Check health
db.health_check()

# Close
db.close()
```

### 3. Scraper Integration (`src/database/writers.py`)

```python
from src.database.writers import db_writer

# Save single analytics
analytics = db_writer.save_analytics(
    video_id="dQw4w9WgXcQ",
    account_name="Beau",
    analytics_data={
        'top_metrics': {...},
        'impressions_data': {...},
        'how_viewers_find': {...}
    }
)

# Bulk operations
records = db_writer.bulk_save_analytics(
    videos_data=[...],
    account_name="Beau"
)

# Query
analytics = db_writer.get_video_analytics(
    video_id="dQw4w9WgXcQ",
    account_name="Beau"
)
```

### 4. API Routes Structure

Each route file follows this pattern:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.api.schemas import *
from src.api.dependencies import get_db
from src.database.models import *

router = APIRouter(prefix="/endpoint", tags=["tag"])

@router.get("", response_model=List[ResponseSchema])
def list_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List items with pagination."""
    return db.query(Model).offset(skip).limit(limit).all()

@router.post("", response_model=ResponseSchema, status_code=201)
def create_item(item: CreateSchema, db: Session = Depends(get_db)):
    """Create new item."""
    db_item = Model(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
```

## Common Tasks

### Add New API Endpoint

1. **Create schema** in `src/api/schemas.py`:
```python
class NewItemResponse(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True
```

2. **Add route** in appropriate file:
```python
@router.get("/items/{item_id}", response_model=NewItemResponse)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item
```

3. **Register route** in `src/api/main.py`:
```python
from src.api.routes import new_routes
app.include_router(new_routes.router)
```

### Query Database

```python
from src.database.connection import db
from src.database.models import VideoAnalytics

with db.session_scope() as session:
    # Get single record
    analytics = session.query(VideoAnalytics).filter(
        VideoAnalytics.video_id == "dQw4w9WgXcQ"
    ).first()

    # Get multiple records
    records = session.query(VideoAnalytics).filter(
        VideoAnalytics.views > 100
    ).all()

    # Count
    count = session.query(VideoAnalytics).count()

    # Aggregate
    from sqlalchemy import func
    total_views = session.query(func.sum(VideoAnalytics.views)).scalar()
```

### Update Record

```python
with db.session_scope() as session:
    analytics = session.query(VideoAnalytics).filter(
        VideoAnalytics.id == 1
    ).first()

    if analytics:
        analytics.views = 150
        analytics.impressions = 2000
        # Changes committed on session exit
```

### Delete Record

```python
with db.session_scope() as session:
    analytics = session.query(VideoAnalytics).filter(
        VideoAnalytics.id == 1
    ).first()

    if analytics:
        session.delete(analytics)
        # Deleted on session exit
```

## Migration & Data Import

### Running Migration

```bash
# Command line
python -m src.database.migrate_json_to_db

# Programmatically
from src.database.migrate_json_to_db import JsonToDbMigrator
migrator = JsonToDbMigrator()
stats = migrator.run()
```

### Adding Custom Migration

```python
from src.database.connection import db
from src.database.models import Account

with db.session_scope() as session:
    # Create new account
    account = Account(
        name="NewAccount",
        cookies_file="profile/cookies.json"
    )
    session.add(account)
    # Committed automatically
```

## Testing

### Test Database Connection

```bash
python -c "from src.database.connection import db; print('OK' if db.health_check() else 'FAILED')"
```

### Test API

```bash
# Start server in background
python -m uvicorn src.api.main:app --port 8000 &

# Test endpoint
curl http://localhost:8000/health

# Stop server
kill %1
```

### Test Route Handler

```python
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

response = client.get("/health")
assert response.status_code == 200

response = client.post("/accounts", json={"name": "Test"})
assert response.status_code == 201
```

## Error Handling

### In Routes

```python
from fastapi import HTTPException, status

@router.get("/{item_id}")
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item {item_id} not found"
        )

    return item
```

### In Database Operations

```python
try:
    with db.session_scope() as session:
        # Operations
        pass
except IntegrityError as e:
    # Duplicate key, foreign key violation, etc.
    print(f"Integrity error: {e}")
except OperationalError as e:
    # Connection error, syntax error, etc.
    print(f"Operational error: {e}")
```

## Debugging

### Enable SQL Logging

```python
# In .env
DB_ECHO=true

# Or in code
config = DatabaseConfig(echo=True)
db = DatabaseConnection(config)
```

### Check Query Results

```python
with db.session_scope() as session:
    query = session.query(VideoAnalytics).filter(VideoAnalytics.views > 100)

    # Print SQL
    print(query.statement)

    # Print results
    for result in query:
        print(result)
```

### View Database Directly

```bash
psql -U youtube_user -d youtube_analytics

# Inside psql:
SELECT * FROM accounts;
SELECT * FROM video_analytics LIMIT 10;
```

## Performance Optimization

### Eager Loading

```python
from sqlalchemy.orm import joinedload

# Avoid N+1 queries
analytics_list = session.query(VideoAnalytics).options(
    joinedload(VideoAnalytics.account),
    joinedload(VideoAnalytics.video)
).all()
```

### Pagination

```python
# Always paginate large result sets
page_size = 100
offset = (page - 1) * page_size

results = session.query(Model).offset(offset).limit(page_size).all()
```

### Bulk Operations

```python
# Faster than individual inserts
records = [
    VideoAnalytics(video_id=vid, account_id=1, views=100)
    for vid in video_ids
]
session.bulk_save_objects(records)
session.commit()
```

### Indexing Strategy

Indexes are already created on:
- `video_id` (frequently filtered)
- `account_id` (frequently filtered)
- `scraped_at` (date range filters)
- Composite index: (video_id, account_id)

## Code Style

- Use type hints: `def get_item(item_id: int) -> Item:`
- Use docstrings: """Brief description. Longer explanation."""
- Follow PEP 8: 4-space indentation, 80-char lines
- Use f-strings: `f"Value: {value}"`
- Handle exceptions explicitly

## File Organization

```
src/
├── api/              # Web API
│   ├── routes/       # Endpoint implementations
│   ├── schemas.py    # Pydantic models
│   ├── main.py       # FastAPI app
│   └── dependencies.py
└── database/         # Database layer
    ├── models.py     # SQLAlchemy models
    ├── connection.py # Connection management
    ├── writers.py    # Scraper integration
    └── migrate_json_to_db.py
```

## Deployment

### Local Development

```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

### Production

```bash
# Use gunicorn with uvicorn workers
gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Or use systemd service
```

## Useful Commands

```bash
# Check Python version
python --version

# Install dependencies
pip install -r requirements.txt

# Run specific route tests
python -m pytest tests/test_analytics.py

# Format code
black src/

# Check linting
flake8 src/

# Type checking
mypy src/

# Run API
python -m uvicorn src.api.main:app --reload
```

## Resources

- FastAPI Docs: https://fastapi.tiangolo.com/
- SQLAlchemy Docs: https://docs.sqlalchemy.org/
- PostgreSQL Docs: https://www.postgresql.org/docs/
- Pydantic Docs: https://docs.pydantic.dev/

## Getting Help

1. Check `docs/BACKEND_SETUP.md` for comprehensive documentation
2. View interactive API docs at `http://localhost:8000/docs`
3. Check database schema: `src/database/schema.sql`
4. Review example code in route files
5. Check error messages carefully

---

Happy coding! 🚀
