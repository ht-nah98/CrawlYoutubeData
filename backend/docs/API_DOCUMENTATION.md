# 📚 YouTube Analytics API - Tài Liệu Đầy Đủ

Tài liệu đầy đủ về REST API cho hệ thống YouTube Analytics.

## 📋 Mục Lục

1. [Tổng Quan](#tổng-quan)
2. [Base URL & Authentication](#base-url--authentication)
3. [Endpoints](#endpoints)
   - [System](#system)
   - [Accounts](#accounts)
   - [Channels](#channels)
   - [Videos](#videos)
   - [Analytics](#analytics)
4. [Schemas](#schemas)
5. [Error Handling](#error-handling)
6. [Examples](#examples)

---

## 🌐 Tổng Quan

YouTube Analytics API là RESTful API được xây dựng bằng FastAPI, cung cấp các chức năng:

- ✅ Quản lý tài khoản YouTube
- ✅ Quản lý kênh YouTube
- ✅ Quản lý video
- ✅ Lưu trữ và truy vấn dữ liệu analytics
- ✅ Thống kê và báo cáo

**Version**: 1.0.0  
**Framework**: FastAPI  
**Database**: PostgreSQL

---

## 🔗 Base URL & Authentication

### Base URL

```
http://localhost:9001
```

**Lưu ý**: Port có thể thay đổi tùy theo cấu hình trong `.env` file.

### Authentication

Hiện tại API không yêu cầu authentication. Trong production, nên thêm API key hoặc JWT token.

### Interactive Documentation

- **Swagger UI**: http://localhost:9001/docs
- **ReDoc**: http://localhost:9001/redoc

---

## 📡 Endpoints

### System

#### Health Check

Kiểm tra trạng thái API và database.

**GET** `/health`

**Response**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Example**:
```bash
curl http://localhost:9001/health
```

#### Root Endpoint

Thông tin về API.

**GET** `/`

**Response**:
```json
{
  "name": "YouTube Analytics API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc",
  "endpoints": {
    "accounts": "/accounts",
    "channels": "/channels",
    "videos": "/videos",
    "analytics": "/analytics"
  }
}
```

---

### Accounts

Quản lý tài khoản YouTube.

#### List Accounts

Lấy danh sách tất cả tài khoản.

**GET** `/accounts`

**Query Parameters**:
- `skip` (int, default: 0): Số bản ghi bỏ qua (pagination)
- `limit` (int, default: 100): Số bản ghi tối đa

**Response**: `List[AccountResponse]`

**Example**:
```bash
curl http://localhost:9001/accounts?skip=0&limit=10
```

**Response Example**:
```json
[
  {
    "id": 1,
    "name": "Beau",
    "cookies_file": "data/cookies/profile/youtube_cookies_Beau.json",
    "created_at": "2025-01-22T10:00:00",
    "updated_at": "2025-01-22T10:00:00"
  }
]
```

#### Create Account

Tạo tài khoản mới.

**POST** `/accounts`

**Request Body**: `AccountCreate`
```json
{
  "name": "My Account",
  "cookies_file": "data/cookies/profile/youtube_cookies_MyAccount.json"
}
```

**Response**: `AccountResponse` (201 Created)

**Example**:
```bash
curl -X POST http://localhost:9001/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Account",
    "cookies_file": "data/cookies/profile/youtube_cookies_MyAccount.json"
  }'
```

**Error Responses**:
- `409 Conflict`: Tài khoản đã tồn tại

#### Get Account

Lấy thông tin tài khoản theo ID.

**GET** `/accounts/{account_id}`

**Path Parameters**:
- `account_id` (int): ID của tài khoản

**Response**: `AccountResponse`

**Example**:
```bash
curl http://localhost:9001/accounts/1
```

**Error Responses**:
- `404 Not Found`: Tài khoản không tồn tại

#### Update Account

Cập nhật thông tin tài khoản.

**PUT** `/accounts/{account_id}`

**Request Body**: `AccountUpdate`
```json
{
  "name": "Updated Name",
  "cookies_file": "new/path/to/cookies.json"
}
```

**Response**: `AccountResponse`

**Example**:
```bash
curl -X PUT http://localhost:9001/accounts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name"
  }'
```

#### Delete Account

Xóa tài khoản.

**DELETE** `/accounts/{account_id}`

**Response**: `204 No Content`

**Example**:
```bash
curl -X DELETE http://localhost:9001/accounts/1
```

---

### Channels

Quản lý kênh YouTube.

#### List Channels

Lấy danh sách kênh.

**GET** `/channels`

**Query Parameters**:
- `account_id` (int, optional): Lọc theo tài khoản
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 100): Pagination limit

**Response**: `List[ChannelResponse]`

**Example**:
```bash
curl http://localhost:9001/channels?account_id=1
```

**Response Example**:
```json
[
  {
    "id": 1,
    "account_id": 1,
    "url": "https://www.youtube.com/channel/UC...",
    "channel_id": "UC...",
    "channel_name": "My Channel",
    "created_at": "2025-01-22T10:00:00",
    "updated_at": "2025-01-22T10:00:00"
  }
]
```

#### Create Channel

Tạo kênh mới cho một tài khoản.

**POST** `/channels`

**Request Body**: `ChannelCreate`
```json
{
  "account_id": 1,
  "url": "https://www.youtube.com/channel/UC...",
  "channel_id": "UC...",
  "channel_name": "My Channel"
}
```

**Response**: `ChannelResponse` (201 Created)

**Example**:
```bash
curl -X POST http://localhost:9001/channels \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "url": "https://www.youtube.com/channel/UC...",
    "channel_id": "UC...",
    "channel_name": "My Channel"
  }'
```

**Error Responses**:
- `404 Not Found`: Tài khoản không tồn tại

#### Get Channel

Lấy thông tin kênh theo ID.

**GET** `/channels/{channel_id}`

**Response**: `ChannelResponse`

#### Update Channel

Cập nhật thông tin kênh.

**PUT** `/channels/{channel_id}`

**Request Body**: `ChannelUpdate`
```json
{
  "channel_name": "Updated Channel Name"
}
```

#### Delete Channel

Xóa kênh.

**DELETE** `/channels/{channel_id}`

**Response**: `204 No Content`

---

### Videos

Quản lý video YouTube.

#### List Videos

Lấy danh sách video.

**GET** `/videos`

**Query Parameters**:
- `channel_id` (int, optional): Lọc theo kênh
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 100): Pagination limit

**Response**: `List[VideoResponse]`

**Example**:
```bash
curl http://localhost:9001/videos?channel_id=1
```

**Response Example**:
```json
[
  {
    "id": 1,
    "video_id": "dQw4w9WgXcQ",
    "channel_id": 1,
    "title": "Video Title",
    "publish_date": "2025-01-01",
    "created_at": "2025-01-22T10:00:00",
    "updated_at": "2025-01-22T10:00:00"
  }
]
```

#### Create Video

Tạo video mới.

**POST** `/videos`

**Request Body**: `VideoCreate`
```json
{
  "video_id": "dQw4w9WgXcQ",
  "channel_id": 1,
  "title": "Video Title",
  "publish_date": "2025-01-01"
}
```

**Response**: `VideoResponse` (201 Created)

**Note**: Nếu video đã tồn tại, API sẽ trả về video hiện có thay vì tạo mới.

#### Bulk Create Videos

Tạo nhiều video cùng lúc.

**POST** `/videos/bulk`

**Request Body**: `BulkVideoCreate`
```json
{
  "channel_id": 1,
  "video_ids": [
    "dQw4w9WgXcQ",
    "jNQXAC9IVRw",
    "9bZkp7q19f0"
  ]
}
```

**Response**: `List[VideoResponse]` (201 Created)

**Example**:
```bash
curl -X POST http://localhost:9001/videos/bulk \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": 1,
    "video_ids": ["dQw4w9WgXcQ", "jNQXAC9IVRw"]
  }'
```

#### Get Video

Lấy thông tin video theo YouTube video ID.

**GET** `/videos/{video_id}`

**Path Parameters**:
- `video_id` (string): YouTube video ID (11 ký tự)

**Response**: `VideoResponse`

**Example**:
```bash
curl http://localhost:9001/videos/dQw4w9WgXcQ
```

#### Update Video

Cập nhật thông tin video.

**PUT** `/videos/{video_id}`

**Request Body**: `VideoUpdate`
```json
{
  "title": "Updated Title",
  "publish_date": "2025-01-01"
}
```

#### Delete Video

Xóa video.

**DELETE** `/videos/{video_id}`

**Response**: `204 No Content`

---

### Analytics

Quản lý dữ liệu analytics.

#### List Analytics

Lấy danh sách analytics với các bộ lọc.

**GET** `/analytics`

**Query Parameters**:
- `account_id` (int, optional): Lọc theo tài khoản
- `video_id` (string, optional): Lọc theo video
- `date_from` (date, optional): Từ ngày (YYYY-MM-DD)
- `date_to` (date, optional): Đến ngày (YYYY-MM-DD)
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 100, max: 1000): Pagination limit

**Response**: `List[VideoAnalyticsResponse]`

**Example**:
```bash
curl "http://localhost:9001/analytics?account_id=1&date_from=2025-01-01&date_to=2025-01-31"
```

#### Create Analytics

Tạo bản ghi analytics mới.

**POST** `/analytics`

**Request Body**: `VideoAnalyticsCreate`
```json
{
  "video_id": "dQw4w9WgXcQ",
  "account_id": 1,
  "impressions": 10000,
  "views": 5000,
  "unique_viewers": 4500,
  "ctr_percentage": 5.2,
  "views_from_impressions": 4800,
  "youtube_recommending_percentage": 60.0,
  "ctr_from_impressions_percentage": 4.8,
  "avg_view_duration_seconds": 120,
  "watch_time_hours": 150.5,
  "publish_start_date": "2025-01-01",
  "top_metrics": {
    "top_countries": ["US", "VN", "UK"],
    "top_devices": ["Mobile", "Desktop"]
  },
  "traffic_sources": {
    "YouTube search": 40.0,
    "Suggested videos": 35.0,
    "Browse features": 25.0
  },
  "impressions_data": {
    "impressions": 10000,
    "impressions_ctr": 5.2
  },
  "page_text": "Raw page text content"
}
```

**Response**: `VideoAnalyticsResponse` (201 Created)

**Note**: Nếu video chưa tồn tại, API sẽ tự động tạo video mới.

#### Bulk Create Analytics

Tạo nhiều bản ghi analytics cùng lúc.

**POST** `/analytics/bulk`

**Request Body**: `BulkAnalyticsCreate`
```json
{
  "analytics": [
    {
      "video_id": "dQw4w9WgXcQ",
      "account_id": 1,
      "views": 5000,
      "impressions": 10000
    },
    {
      "video_id": "jNQXAC9IVRw",
      "account_id": 1,
      "views": 3000,
      "impressions": 8000
    }
  ]
}
```

**Response**: `List[VideoAnalyticsResponse]` (201 Created)

#### Get Video Analytics

Lấy tất cả analytics của một video.

**GET** `/analytics/video/{video_id}`

**Query Parameters**:
- `skip` (int, default: 0): Pagination offset
- `limit` (int, default: 100, max: 1000): Pagination limit

**Response**: `List[VideoAnalyticsResponse]`

**Example**:
```bash
curl http://localhost:9001/analytics/video/dQw4w9WgXcQ
```

#### Get Account Statistics

Lấy thống kê tổng hợp của một tài khoản.

**GET** `/analytics/account/{account_id}/stats`

**Query Parameters**:
- `date_from` (date, optional): Từ ngày (YYYY-MM-DD)
- `date_to` (date, optional): Đến ngày (YYYY-MM-DD)

**Response**: `AnalyticsStatsResponse`
```json
{
  "total_videos": 50,
  "total_impressions": 500000,
  "total_views": 250000,
  "total_watch_time_hours": 1250.5,
  "average_ctr_percentage": 5.2,
  "average_views_per_video": 5000,
  "date_from": "2025-01-01",
  "date_to": "2025-01-31"
}
```

**Example**:
```bash
curl "http://localhost:9001/analytics/account/1/stats?date_from=2025-01-01&date_to=2025-01-31"
```

#### Get Analytics by ID

Lấy analytics theo ID.

**GET** `/analytics/{analytics_id}`

**Response**: `VideoAnalyticsResponse`

#### Update Analytics

Cập nhật bản ghi analytics.

**PUT** `/analytics/{analytics_id}`

**Request Body**: `VideoAnalyticsUpdate`
```json
{
  "views": 5500,
  "impressions": 11000,
  "ctr_percentage": 5.5
}
```

#### Delete Analytics

Xóa bản ghi analytics.

**DELETE** `/analytics/{analytics_id}`

**Response**: `204 No Content`

---

## 📋 Schemas

### Account Schemas

#### AccountCreate
```json
{
  "name": "string (required, 1-255 chars)",
  "cookies_file": "string (optional, max 500 chars)"
}
```

#### AccountResponse
```json
{
  "id": "integer",
  "name": "string",
  "cookies_file": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Channel Schemas

#### ChannelCreate
```json
{
  "account_id": "integer (required)",
  "url": "string (required)",
  "channel_id": "string (optional, max 50 chars)",
  "channel_name": "string (optional, max 255 chars)"
}
```

#### ChannelResponse
```json
{
  "id": "integer",
  "account_id": "integer",
  "url": "string",
  "channel_id": "string",
  "channel_name": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Video Schemas

#### VideoCreate
```json
{
  "video_id": "string (required, exactly 11 chars)",
  "channel_id": "integer (optional)",
  "title": "string (optional, max 500 chars)",
  "publish_date": "date (optional, YYYY-MM-DD)"
}
```

#### VideoResponse
```json
{
  "id": "integer",
  "video_id": "string",
  "channel_id": "integer",
  "title": "string",
  "publish_date": "date",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### Analytics Schemas

#### VideoAnalyticsCreate
```json
{
  "video_id": "string (required, 11 chars)",
  "account_id": "integer (required)",
  "impressions": "integer (optional)",
  "views": "integer (optional)",
  "unique_viewers": "integer (optional)",
  "ctr_percentage": "float (optional)",
  "views_from_impressions": "integer (optional)",
  "youtube_recommending_percentage": "float (optional)",
  "ctr_from_impressions_percentage": "float (optional)",
  "avg_view_duration_seconds": "integer (optional)",
  "watch_time_hours": "float (optional)",
  "publish_start_date": "date (optional)",
  "top_metrics": "object (optional)",
  "traffic_sources": "object (optional)",
  "impressions_data": "object (optional)",
  "page_text": "string (optional)"
}
```

#### VideoAnalyticsResponse
```json
{
  "id": "integer",
  "video_id": "string",
  "account_id": "integer",
  "impressions": "integer",
  "views": "integer",
  "unique_viewers": "integer",
  "ctr_percentage": "float",
  "views_from_impressions": "integer",
  "youtube_recommending_percentage": "float",
  "ctr_from_impressions_percentage": "float",
  "avg_view_duration_seconds": "integer",
  "watch_time_hours": "float",
  "publish_start_date": "date",
  "top_metrics": "object",
  "traffic_sources": "object",
  "impressions_data": "object",
  "page_text": "string",
  "scraped_at": "datetime",
  "traffic_sources_breakdown": []
}
```

---

## ⚠️ Error Handling

API sử dụng HTTP status codes chuẩn:

### Status Codes

- `200 OK`: Request thành công
- `201 Created`: Tạo resource thành công
- `204 No Content`: Xóa thành công (không có response body)
- `400 Bad Request`: Request không hợp lệ
- `404 Not Found`: Resource không tồn tại
- `409 Conflict`: Resource đã tồn tại (ví dụ: tài khoản trùng tên)
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Lỗi server

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### Example Error Responses

**404 Not Found**:
```json
{
  "detail": "Account 1 not found"
}
```

**409 Conflict**:
```json
{
  "detail": "Account 'MyAccount' already exists"
}
```

**422 Validation Error**:
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 💡 Examples

### Python Example

```python
import requests

BASE_URL = "http://localhost:9001"

# Create account
response = requests.post(
    f"{BASE_URL}/accounts",
    json={
        "name": "My Account",
        "cookies_file": "data/cookies/profile/youtube_cookies_MyAccount.json"
    }
)
account = response.json()
account_id = account["id"]

# Create channel
response = requests.post(
    f"{BASE_URL}/channels",
    json={
        "account_id": account_id,
        "url": "https://www.youtube.com/channel/UC...",
        "channel_id": "UC...",
        "channel_name": "My Channel"
    }
)
channel = response.json()
channel_id = channel["id"]

# Bulk create videos
response = requests.post(
    f"{BASE_URL}/videos/bulk",
    json={
        "channel_id": channel_id,
        "video_ids": ["dQw4w9WgXcQ", "jNQXAC9IVRw"]
    }
)
videos = response.json()

# Create analytics
response = requests.post(
    f"{BASE_URL}/analytics",
    json={
        "video_id": "dQw4w9WgXcQ",
        "account_id": account_id,
        "views": 5000,
        "impressions": 10000,
        "ctr_percentage": 5.2
    }
)
analytics = response.json()

# Get account statistics
response = requests.get(
    f"{BASE_URL}/analytics/account/{account_id}/stats",
    params={
        "date_from": "2025-01-01",
        "date_to": "2025-01-31"
    }
)
stats = response.json()
print(f"Total views: {stats['total_views']}")
```

### cURL Examples

```bash
# Health check
curl http://localhost:9001/health

# List accounts
curl http://localhost:9001/accounts

# Create account
curl -X POST http://localhost:9001/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "My Account", "cookies_file": "path/to/cookies.json"}'

# Get account stats
curl "http://localhost:9001/analytics/account/1/stats?date_from=2025-01-01&date_to=2025-01-31"

# List analytics with filters
curl "http://localhost:9001/analytics?account_id=1&video_id=dQw4w9WgXcQ&date_from=2025-01-01"
```

### JavaScript/TypeScript Example

```typescript
const BASE_URL = "http://localhost:9001";

// Create account
const account = await fetch(`${BASE_URL}/accounts`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    name: "My Account",
    cookies_file: "data/cookies/profile/youtube_cookies_MyAccount.json"
  })
}).then(res => res.json());

// Get account statistics
const stats = await fetch(
  `${BASE_URL}/analytics/account/${account.id}/stats?date_from=2025-01-01&date_to=2025-01-31`
).then(res => res.json());

console.log(`Total views: ${stats.total_views}`);
```

---

## 🔄 Workflow Example

### Quy trình làm việc điển hình:

1. **Tạo tài khoản**
   ```bash
   POST /accounts
   ```

2. **Tạo kênh cho tài khoản**
   ```bash
   POST /channels
   ```

3. **Thêm video vào kênh**
   ```bash
   POST /videos/bulk
   ```

4. **Cào dữ liệu analytics và lưu vào database**
   ```bash
   POST /analytics
   ```

5. **Xem thống kê**
   ```bash
   GET /analytics/account/{account_id}/stats
   ```

---

## 📝 Notes

- Tất cả datetime fields sử dụng ISO 8601 format
- Date fields sử dụng format `YYYY-MM-DD`
- Video ID phải chính xác 11 ký tự (YouTube video ID format)
- Pagination: `skip` và `limit` có thể được sử dụng cho các endpoints list
- Bulk operations giúp tối ưu hiệu suất khi cần tạo nhiều records

---

## 🔗 Related Documentation

- [Docker Deployment Guide](DOCKER_DEPLOYMENT.md)
- [Backend README](backend/README.md)
- [Interactive API Docs](http://localhost:9001/docs)

---

**Version**: 1.0.0  
**Last Updated**: 2025-01-22  
**Maintained by**: YouTube Analytics Team

