# 🚀 YouTube Analytics Backend Server

This is the backend server component of the YouTube Analytics application. It provides a REST API for managing YouTube accounts, channels, videos, and analytics data.

## 📋 Features

- **REST API** - Full-featured API with FastAPI
- **Database** - PostgreSQL with SQLAlchemy ORM
- **Scraper** - Selenium-based YouTube scraper
- **Documentation** - Auto-generated API docs (Swagger/ReDoc)
- **CORS** - Enabled for cross-origin requests

## 🏗️ Architecture

```
backend/
├── src/
│   ├── api/          # FastAPI application
│   ├── database/     # Database models and connection
│   ├── scraper/      # Web scraping engine
│   ├── core/         # Business logic
│   └── utils/        # Utilities
├── scripts/          # Setup and migration scripts
├── server.py         # Main entry point
├── requirements.txt  # Python dependencies
└── .env             # Environment configuration
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Edit `.env` file with your database credentials:

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=admin
DB_NAME=youtube_analytics
DB_ECHO=false

API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
```

### 3. Initialize Database

```bash
python scripts/setup/init_db.py
```

### 4. Start Server

```bash
python server.py
```

The server will start on `http://localhost:8000`

## 📚 API Documentation

Once the server is running, access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔌 API Endpoints

### System
- `GET /health` - Health check
- `GET /` - API information

### Accounts
- `GET /accounts` - List all accounts
- `POST /accounts` - Create new account
- `GET /accounts/{id}` - Get account by ID
- `PUT /accounts/{id}` - Update account
- `DELETE /accounts/{id}` - Delete account

### Channels
- `GET /channels` - List all channels
- `POST /channels` - Create new channel
- `GET /channels/{id}` - Get channel by ID
- `DELETE /channels/{id}` - Delete channel

### Videos
- `GET /videos` - List all videos
- `POST /videos` - Create new video
- `POST /videos/bulk` - Bulk create videos
- `GET /videos/{id}` - Get video by ID

### Analytics
- `GET /analytics` - List analytics data
- `POST /analytics` - Create analytics entry
- `POST /analytics/bulk` - Bulk import analytics
- `GET /analytics/account/{id}/stats` - Get account statistics

## 🗄️ Database Schema

The application uses PostgreSQL with the following tables:

- **accounts** - YouTube accounts
- **channels** - YouTube channels
- **videos** - Video metadata
- **video_analytics** - Analytics data
- **traffic_sources** - Traffic source breakdown
- **scraping_history** - Scraping logs

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DB_HOST | Database host | localhost |
| DB_PORT | Database port | 5432 |
| DB_USER | Database user | postgres |
| DB_PASSWORD | Database password | - |
| DB_NAME | Database name | youtube_analytics |
| API_HOST | API host | 0.0.0.0 |
| API_PORT | API port | 8000 |

## 🚢 Deployment

### Option 1: Direct Python

```bash
python server.py
```

### Option 2: Using Uvicorn

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Option 3: Docker

```bash
docker build -t youtube-analytics-backend .
docker run -p 8000:8000 youtube-analytics-backend
```

### Option 4: Production (with Gunicorn)

```bash
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🧪 Testing

### Test API Health

```bash
curl http://localhost:8000/health
```

### Test Endpoints

```bash
# List accounts
curl http://localhost:8000/accounts

# Create account
curl -X POST http://localhost:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Account", "cookies_file": "test.json"}'
```

## 📊 Monitoring

The server provides:
- Health check endpoint
- Request logging
- Database connection monitoring
- Error tracking

## 🔒 Security

- CORS enabled (configure in `src/api/main.py`)
- Database connection pooling
- SQL injection prevention (SQLAlchemy ORM)
- Input validation (Pydantic)

## 🐛 Troubleshooting

### Database Connection Error

```bash
# Check PostgreSQL is running
psql -U postgres -d youtube_analytics

# Verify .env credentials
cat .env
```

### Port Already in Use

```bash
# Change port in .env or use different port
API_PORT=8001
```

### Module Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📝 Development

### Running in Development Mode

```bash
python server.py
# Server will auto-reload on code changes
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## 📞 Support

For issues or questions:
1. Check API documentation at `/docs`
2. Review server logs
3. Verify database connection
4. Check environment configuration

## 📄 License

Proprietary - All rights reserved

---

**Version**: 1.0.0  
**Last Updated**: 2025-11-22
