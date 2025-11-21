# API Quick Start Guide

Get the YouTube Analytics API up and running in 5 minutes.

## 1. Install Dependencies

```bash
cd /home/user/Downloads/craw_data_ytb
pip install -r requirements.txt
```

## 2. Setup PostgreSQL Database

### Option A: Using Docker (Recommended)
```bash
docker run -d \
  --name youtube_analytics_db \
  -e POSTGRES_USER=youtube_user \
  -e POSTGRES_PASSWORD=strong_password \
  -e POSTGRES_DB=youtube_analytics \
  -p 5432:5432 \
  postgres:15
```

### Option B: Local PostgreSQL
```bash
# Ubuntu/Debian
sudo apt-get install postgresql
sudo -u postgres createdb youtube_analytics
sudo -u postgres createuser youtube_user

# macOS
brew install postgresql
createdb youtube_analytics
createuser youtube_user
```

## 3. Configure Environment

```bash
# Create .env file from template
cp .env.example .env

# Edit with your database credentials
nano .env
```

Example `.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_USER=youtube_user
DB_PASSWORD=strong_password
DB_NAME=youtube_analytics
```

## 4. Start the API Server

```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

Output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
✓ Database tables created successfully
✓ Database connection healthy
```

## 5. Access the API

- **Interactive Docs**: http://localhost:8000/docs
- **API Base URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

## Common Tasks

### Create Your First Account

```bash
curl -X POST "http://localhost:8000/accounts" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyAccount",
    "cookies_file": "profile/youtube_cookies_MyAccount.json"
  }'
```

### Add Videos to Account

```bash
curl -X POST "http://localhost:8000/videos/bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": null,
    "video_ids": ["dQw4w9WgXcQ", "video_id_2", "video_id_3"]
  }'
```

### Import Analytics Data

```bash
python -c "from src.database.migrate_json_to_db import main; main()"
```

### Query Analytics

```bash
curl "http://localhost:8000/analytics?account_id=1&limit=10"
```

### Get Account Statistics

```bash
curl "http://localhost:8000/analytics/account/1/stats"
```

## Stopping the Server

Press `Ctrl+C` in the terminal.

## Next Steps

- Read full documentation: [docs/BACKEND_SETUP.md](docs/BACKEND_SETUP.md)
- Learn API endpoints: Use the interactive docs at `/docs`
- Configure the scraper to use the database
- Setup database backups

## Troubleshooting

### "Database connection failed"
- Ensure PostgreSQL is running
- Check `.env` credentials
- Test connection: `psql -U youtube_user -d youtube_analytics`

### "Module not found" errors
- Reinstall requirements: `pip install -r requirements.txt --force-reinstall`

### API returns 404
- Verify PostgreSQL database exists
- Check that tables were created
- Review API logs in terminal

## API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Check API status |
| POST | `/accounts` | Create account |
| GET | `/accounts` | List accounts |
| POST | `/analytics` | Add analytics |
| GET | `/analytics` | Query analytics |
| POST | `/analytics/bulk` | Bulk import analytics |
| GET | `/analytics/account/{id}/stats` | Get statistics |

## Performance Tips

- Use bulk endpoints for large data imports
- Filter queries by date range to reduce results
- Monitor database logs for slow queries
- Use pagination (skip/limit parameters)

Enjoy! 🚀
