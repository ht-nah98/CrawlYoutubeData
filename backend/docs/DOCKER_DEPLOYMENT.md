# 🐳 Hướng dẫn Triển khai Backend với Docker

Tài liệu này hướng dẫn cách triển khai backend YouTube Analytics lên server sử dụng Docker.

## 📋 Yêu cầu

- Docker Engine 20.10+
- Docker Compose 2.0+
- Ít nhất 2GB RAM
- Ít nhất 10GB dung lượng ổ cứng

## 🚀 Các bước triển khai

### 1. Chuẩn bị môi trường

#### Tạo file `.env` từ template:

```bash
cd /home/hgai-03/anhht/CrawlYoutubeData
cp backend/.env.example .env
```

#### Chỉnh sửa file `.env` với thông tin của bạn:

```env
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=<MẬT_KHẨU_MẠNH>  # Thay đổi mật khẩu này!
DB_NAME=youtube_analytics
DB_ECHO=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# Production Settings
PRODUCTION=true  # Đặt true cho production
```

**⚠️ QUAN TRỌNG:** Đổi mật khẩu database thành mật khẩu mạnh!

### 2. Kiểm tra cấu trúc thư mục

Đảm bảo bạn có:
- `backend/` - Thư mục backend
- `data/cookies/profile/` - Thư mục chứa cookies (nếu có)
- `config.json` - File cấu hình (nếu có)

### 3. Build và chạy với Docker Compose

```bash
# Build và khởi động tất cả services
docker-compose up -d

# Xem logs
docker-compose logs -f

# Xem logs của backend
docker-compose logs -f backend

# Xem logs của database
docker-compose logs -f postgres
```

### 4. Khởi tạo Database

Database sẽ tự động được khởi tạo khi container backend khởi động lần đầu. Nếu cần khởi tạo thủ công:

```bash
# Vào container backend
docker-compose exec backend bash

# Chạy script khởi tạo database
python scripts/setup/init_db.py

# Thoát
exit
```

### 5. Kiểm tra hoạt động

#### Kiểm tra health check:

```bash
curl http://localhost:8000/health
```

Kết quả mong đợi:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

#### Kiểm tra API documentation:

Mở trình duyệt và truy cập:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Quản lý Container

### Dừng services:

```bash
docker-compose stop
```

### Khởi động lại:

```bash
docker-compose restart
```

### Dừng và xóa containers (giữ data):

```bash
docker-compose down
```

### Dừng và xóa tất cả (bao gồm volumes - MẤT DỮ LIỆU):

```bash
docker-compose down -v
```

### Rebuild sau khi thay đổi code:

```bash
docker-compose build --no-cache backend
docker-compose up -d
```

## 📊 Xem trạng thái

```bash
# Xem trạng thái các containers
docker-compose ps

# Xem sử dụng tài nguyên
docker stats

# Xem logs real-time
docker-compose logs -f
```

## 🔍 Troubleshooting

### Lỗi kết nối database

```bash
# Kiểm tra database có chạy không
docker-compose ps postgres

# Kiểm tra logs database
docker-compose logs postgres

# Test kết nối từ backend container
docker-compose exec backend python -c "from src.database.config import DatabaseConfig; print(DatabaseConfig())"
```

### Lỗi port đã được sử dụng

Nếu port 8000 hoặc 5432 đã được sử dụng, thay đổi trong `.env`:

```env
API_PORT=8001
DB_PORT=5433
```

Và cập nhật `docker-compose.yml` nếu cần.

### Lỗi Chrome/Chromium trong container

Nếu gặp lỗi liên quan đến Chrome, kiểm tra:

```bash
# Vào container và test Chrome
docker-compose exec backend bash
google-chrome --version
chromedriver --version
```

### Xóa và rebuild hoàn toàn

```bash
# Dừng và xóa tất cả
docker-compose down -v

# Xóa images
docker rmi crawl_youtube_data-backend

# Rebuild từ đầu
docker-compose build --no-cache
docker-compose up -d
```

## 🔒 Bảo mật Production

### 1. Thay đổi mật khẩu mặc định

**BẮT BUỘC** thay đổi mật khẩu database trong `.env`:

```env
DB_PASSWORD=<MẬT_KHẨU_MẠNH_ÍT_NHẤT_16_KÝ_TỰ>
```

### 2. Giới hạn truy cập API

Chỉnh sửa CORS trong `backend/src/api/main.py` để giới hạn origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Thay đổi
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Sử dụng reverse proxy (Nginx)

Khuyến nghị sử dụng Nginx làm reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Bật HTTPS

Sử dụng Let's Encrypt với Certbot:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

## 📦 Backup và Restore

### Backup database:

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres youtube_analytics > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T postgres psql -U postgres youtube_analytics < backup_20240101.sql
```

### Backup volumes:

```bash
# Backup data volume
docker run --rm -v crawl_youtube_data_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

## 🔄 Cập nhật

### Cập nhật code mới:

```bash
# Pull code mới
git pull

# Rebuild và restart
docker-compose build backend
docker-compose up -d
```

### Cập nhật dependencies:

```bash
# Rebuild với --no-cache để cài đặt lại dependencies
docker-compose build --no-cache backend
docker-compose up -d
```

## 📝 Ghi chú

- Database data được lưu trong Docker volume `postgres_data`
- Cookies và data files được mount từ `./data` trên host
- Logs có thể xem bằng `docker-compose logs`
- Health check tự động chạy mỗi 30 giây

## 🆘 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra logs: `docker-compose logs -f`
2. Kiểm tra health: `curl http://localhost:8000/health`
3. Kiểm tra database: `docker-compose exec postgres psql -U postgres -d youtube_analytics`

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-22

