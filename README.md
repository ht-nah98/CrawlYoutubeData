# 🎥 YouTube Analytics Scraper

**Công cụ chuyên nghiệp để cào dữ liệu analytics từ YouTube Studio với giao diện GUI hiện đại**

## ✨ Tính năng chính

### 🎯 **Giao diện GUI hiện đại**
- **Giao diện đẹp mắt** với thiết kế Material Design
- **Responsive** - tự động fullscreen và có thể resize
- **Cuộn mượt mà** với mouse wheel support
- **Real-time logging** với màu sắc phân biệt
- **Progress tracking** với thanh tiến trình animated

### 🔐 **Quản lý tài khoản thông minh**
- **Đăng nhập GUI** - không cần terminal, chỉ cần nhấn nút
- **Quản lý nhiều tài khoản** YouTube cùng lúc
- **Tự động lưu cookies** và tái sử dụng
- **Chuyển đổi tài khoản** dễ dàng
- **Tự động kiểm tra** và đăng nhập lại khi cookies hết hạn

### 📊 **Cào dữ liệu toàn diện**
- **Quét toàn bộ video IDs** từ kênh YouTube (dùng yt-dlp)
- **Lấy analytics chi tiết** từ YouTube Studio:
  - **Traffic Sources**: Direct, Channel pages, YouTube search, Browse features, External, v.v.
  - **Impressions Data**: Impressions, CTR, Views, Average view duration, Watch time, Unique viewers
  - **Top Metrics**: Tất cả key metrics từ dashboard
- **Cào song song** nhiều video với đa luồng
- **Tự động retry** khi gặp lỗi

### ⚡ **Chế độ tự động**
- **Auto-scraping** theo lịch trình (mỗi X phút)
- **Chạy nhiều quá trình** cùng lúc mà không bị conflict
- **Headless mode** để chạy ngầm
- **Parallel processing** với nhiều Chrome drivers

### 💾 **Lưu trữ và xuất dữ liệu**
- **Merge thông minh** - tránh trùng lặp video IDs
- **Xuất JSON** với cấu trúc rõ ràng
- **Backup tự động** kết quả cũ
- **Timestamp** theo định dạng Việt Nam

## 🚀 Cài đặt

### 1. **Yêu cầu hệ thống**
- Python 3.8 trở lên
- Chrome browser
- Windows/Linux/macOS

### 2. **Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Cài đặt Chrome WebDriver (tự động)**
```bash
pip install webdriver-manager
```

## 🎮 Cách sử dụng

### 🖥️ **Chế độ GUI (Khuyến nghị)**

**Khởi chạy giao diện:**
```bash
python gui.py
```

### 🎮 **Hướng dẫn sử dụng GUI chi tiết**

#### **📝 Phần nhập liệu:**
- **Ô "Link kênh"**: Nhập URL kênh YouTube (hỗ trợ @channelname, /c/channel, /channel/UC...)
- **Ô "Giới hạn số video"**: Để trống = lấy tất cả, hoặc nhập số để giới hạn

#### **🎛️ Các nút điều khiển chính:**

**🔵 Nút "📹 Lấy danh sách video"**
- **Chức năng**: Quét tất cả video IDs từ kênh YouTube
- **Khi nào dùng**: Lần đầu tiên hoặc khi muốn cập nhật danh sách video mới
- **Quy trình**: 
  1. Nhập URL kênh → Nhấn nút này
  2. Nếu chưa có tài khoản → Popup hỏi tạo tài khoản mới
  3. Nếu đồng ý → Mở Chrome để đăng nhập Google
  4. Sau đăng nhập → Nhấn "✅ Đã đăng nhập xong" trong popup
  5. Tự động lưu cookies và video IDs vào config.json

**🟢 Nút "🚀 Bắt đầu cào dữ liệu"**
- **Chức năng**: Cào dữ liệu analytics từ tất cả video đã load
- **Khi nào dùng**: Sau khi đã có danh sách video (từ nút trên hoặc từ config.json)
- **Đặc biệt**: 
  - ✅ **Luôn luôn bật** - có thể nhấn nhiều lần để chạy song song
  - ✅ **Không bị vô hiệu hóa** khi đang chạy
  - ✅ **Mỗi lần nhấn tạo một thread riêng**

**🔴 Nút "⏹️ Dừng"**
- **Chức năng**: Dừng quá trình cào dữ liệu hiện tại
- **Lưu ý**: Chỉ dừng thread hiện tại, các thread khác vẫn chạy

**🗑️ Nút "🗑️ Xóa log"**
- **Chức năng**: Xóa sạch nhật ký hoạt động
- **Khi nào dùng**: Khi log quá dài, muốn làm sạch màn hình

#### **⚙️ Cài đặt nâng cao:**

**📦 Chế độ tự động cào dữ liệu:**
- **☑️ Checkbox "Bật chế độ tự động"**: 
  - Bật: Tự động cào dữ liệu theo lịch trình
  - Tắt: Chỉ cào khi nhấn nút thủ công
- **⏰ Ô "Cào mỗi X phút"**: Đặt khoảng thời gian giữa các lần cào (mặc định: 30 phút)

**🔐 Cài đặt đăng nhập Google:**
- **☑️ Checkbox "Tự động tiếp tục sau đăng nhập"**:
  - Bật: Sau khi đăng nhập, tự động tiếp tục sau X giây
  - Tắt: Cần nhấn Enter trong terminal để tiếp tục
- **⏱️ Ô "Thời gian chờ"**: Số giây chờ trước khi tự động tiếp tục (mặc định: 30s)

#### **📊 Theo dõi tiến trình:**
- **Thanh tiến trình**: Hiển thị % hoàn thành của quá trình hiện tại
- **Nhật ký hoạt động**: 
  - 🔵 **INFO**: Thông tin thường
  - 🟢 **SUCCESS**: Thành công  
  - 🟡 **WARNING**: Cảnh báo
  - 🔴 **ERROR**: Lỗi
- **Thanh trạng thái**: Hiển thị số tài khoản và video đã load

#### **🔄 Quy trình sử dụng từng bước:**

**🆕 Lần đầu sử dụng:**
1. **Khởi động**: `python gui.py`
2. **Nhập URL**: Dán link kênh YouTube vào ô "Link kênh"
3. **Lấy video**: Nhấn "📹 Lấy danh sách video"
4. **Tạo tài khoản**: Chọn "Có" khi được hỏi tạo tài khoản mới
5. **Đặt tên**: Nhập tên tài khoản hoặc để trống (tự động tạo)
6. **Đăng nhập**: Chrome mở → Đăng nhập Google → Nhấn "✅ Đã đăng nhập xong"
7. **Cào dữ liệu**: Nhấn "🚀 Bắt đầu cào dữ liệu"
8. **Theo dõi**: Xem tiến trình trong log và thanh progress

**🔄 Lần sau sử dụng:**
1. **Khởi động**: `python gui.py` 
2. **Tự động load**: Phần mềm tự động load tài khoản và video từ config.json
3. **Cào ngay**: Nhấn "🚀 Bắt đầu cào dữ liệu" (không cần đăng nhập lại)

**🤖 Chế độ tự động:**
1. **Bật tự động**: ☑️ Tick "Bật chế độ tự động" 
2. **Đặt thời gian**: Nhập số phút trong ô "Cào mỗi"
3. **Để chạy**: Phần mềm sẽ tự động cào theo lịch trình
4. **Theo dõi**: Xem countdown trong "Trạng thái"

#### **💡 Mẹo sử dụng:**
- **Chạy song song**: Có thể nhấn "🚀 Bắt đầu cào dữ liệu" nhiều lần để tăng tốc
- **Không đóng Chrome**: Khi đang cào, không đóng cửa sổ Chrome
- **Kiểm tra log**: Luôn theo dõi log để biết trạng thái
- **Backup config**: Sao lưu file `config.json` để không mất dữ liệu

### 💻 **Chế độ Command Line**

**Cào dữ liệu với tài khoản cụ thể:**
```bash
python craw.py --account-name "tài_khoản_1"
```

**Các tùy chọn nâng cao:**
```bash
# Chạy headless (không hiển thị browser)
python craw.py --account-name "account1" --headless

# Tự động tiếp tục sau đăng nhập
python craw.py --account-name "account1" --auto-continue --wait-time 60

# Cào song song nhiều channels
python craw.py --account-name "account1" --parallel --max-workers 3
```

### 📺 **Quét video IDs từ kênh**

**Lấy tất cả video từ kênh:**
```bash
python get_channel_videos.py "https://www.youtube.com/@channelname" --account-name "MyAccount"
```

**Các định dạng URL được hỗ trợ:**
- `https://www.youtube.com/@channelname`
- `https://www.youtube.com/c/channelname`  
- `https://www.youtube.com/channel/UCxxxxx`
- `https://www.youtube.com/user/username`

**Tùy chọn quản lý tài khoản:**
```bash
# Chọn tài khoản tương tác
python get_channel_videos.py "URL" --interactive

# Liệt kê tài khoản
python get_channel_videos.py --list-accounts

# Chuyển đổi tài khoản
python get_channel_videos.py "URL" --switch-account "AccountName"

# Sử dụng cookies có sẵn
python get_channel_videos.py "URL" --account-name "MyAccount" --use-existing-cookies
```

## 📋 Cấu trúc config.json

```json
{
  "accounts": [
    {
      "name": "account_1",
      "cookies_file": "profile/youtube_cookies_account_1.json",
      "channels": [
        {
          "url": "https://www.youtube.com/@channelname",
          "video_ids": ["video_id_1", "video_id_2", "..."],
          "output_file": "analytics_results_channel1.json"
        }
      ]
    },
    {
      "name": "account_2", 
      "cookies_file": "profile/youtube_cookies_account_2.json",
      "channels": [...]
    }
  ],
  "auto_scraping_enabled": true,
  "auto_scraping_interval": 30,
  "auto_scraping_headless": true,
  "headless": false,
  "auto_continue": true,
  "wait_time": 30,
  "parallel": false,
  "max_workers": 3
}
```

## 📊 Cấu trúc dữ liệu output

```json
[
  {
    "video_id": "AzD7z8Nc-c0",
    "crawl_datetime": "09/11/2025",
    "publish_start_date": "2025-08-13",
    "top_metrics": {
      "Impressions": "15,234",
      "Impressions click-through rate": "5.2%", 
      "Views": "1,234",
      "Unique viewers": "987"
    },
    "how_viewers_find": {
      "Direct or unknown": "1,234 (45.2%)",
      "Channel pages": "567 (20.8%)",
      "YouTube search": "890 (32.6%)",
      "Browse features": "123 (4.5%)",
      "External": "45 (1.6%)"
    },
    "impressions_data": {
      "Impressions": "15,234",
      "Click-through rate (from impressions)": "5.2%",
      "Views from impressions": "793",
      "Average view duration (from impressions)": "3:45",
      "Watch time from impressions (hours)": "49.2",
      "YouTube recommending your content": "78.5% of impressions"
    },
    "page_text": "First 500 characters of page content..."
  }
]
```

## 🔧 Tính năng nâng cao

### 🔄 **Parallel Processing**
- **Đa luồng**: Mỗi tài khoản chạy trên Chrome driver riêng
- **Thread-safe**: Không bị conflict giữa các quá trình
- **Load balancing**: Tự động phân phối video cho các tài khoản
- **Fault tolerance**: Một thread lỗi không ảnh hưởng thread khác

### 🤖 **Auto Scraping**
- **Lịch trình linh hoạt**: Cào mỗi X phút (có thể tùy chỉnh)
- **Auto reload config**: Tự động load tài khoản mới từ config.json
- **Headless mode**: Chạy ngầm không cần giao diện
- **Smart retry**: Tự động thử lại khi gặp lỗi

### 🛡️ **Error Handling**
- **Auto re-login**: Tự động đăng nhập lại khi cookies hết hạn
- **Retry mechanism**: Thử lại nhiều lần khi gặp lỗi network
- **Graceful degradation**: Tiếp tục với video khác khi một video lỗi
- **Comprehensive logging**: Log chi tiết mọi hoạt động

### 💡 **Smart Features**
- **Cookie management**: Tự động quản lý và refresh cookies
- **Account switching**: Chuyển đổi tài khoản trong cùng session
- **Data merging**: Merge kết quả mới với dữ liệu cũ, tránh trùng lặp
- **Progress tracking**: Theo dõi tiến trình real-time

## ⚠️ Lưu ý quan trọng

### 🔐 **Bảo mật**
- **Cookies được mã hóa** và lưu local
- **Không lưu password** - chỉ lưu session cookies
- **Tự động expire** cookies cũ để bảo mật

### 🎯 **Yêu cầu quyền truy cập**
- ⚠️ **QUAN TRỌNG**: Bạn phải có **quyền quản lý kênh YouTube** mới có thể cào được dữ liệu analytics
- Chỉ cào được dữ liệu của kênh mà tài khoản có quyền truy cập
- Không thể cào dữ liệu của kênh người khác

### 🔄 **Cập nhật CSS Selectors**
YouTube Studio thường xuyên thay đổi giao diện. Nếu gặp lỗi:

1. Mở YouTube Studio Analytics trong Chrome
2. Nhấn F12 để mở DevTools  
3. Inspect các elements chứa dữ liệu
4. Cập nhật CSS selectors trong code:
   - `get_top_section_metrics()`: Key metrics
   - `get_traffic_sources()`: Traffic sources
   - `get_impressions_data()`: Impressions metrics

## 🐛 Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| **Không tìm thấy elements** | CSS selectors đã thay đổi | Cập nhật selectors theo hướng dẫn trên |
| **Cookies hết hạn** | Session timeout | Xóa file cookies và đăng nhập lại |
| **Trang load chậm** | Mạng chậm hoặc headless mode | Tăng `wait_time` trong config |
| **Chrome driver lỗi** | Driver không tương thích | Cài đặt lại: `pip install webdriver-manager` |
| **Không có quyền truy cập** | Tài khoản không quản lý kênh | Đăng nhập tài khoản có quyền quản lý |

## 🚀 Workflow khuyến nghị

### **Lần đầu setup:**
```bash
# 1. Khởi chạy GUI
python gui.py

# 2. Nhập URL kênh và tạo tài khoản
# 3. Đăng nhập qua popup dialog
# 4. Bắt đầu cào dữ liệu
```

### **Sử dụng hàng ngày:**
```bash
# Chỉ cần khởi chạy GUI và nhấn "Bắt đầu cào dữ liệu"
python gui.py
```

### **Chạy tự động (server):**
```bash
# Setup auto-scraping trong config.json
# Sau đó chạy GUI hoặc command line
python gui.py  # Hoặc python craw.py --account-name "account1" --headless
```

## 📈 Mở rộng và tùy chỉnh

### **Thêm metrics mới:**
- Chỉnh sửa các hàm `get_*_data()` trong `craw.py`
- Thêm CSS selectors cho metrics mới
- Cập nhật cấu trúc JSON output

### **Tích hợp với hệ thống khác:**
- Xuất CSV/Excel: Thêm module pandas
- Gửi thông báo: Tích hợp Telegram/Email API  
- Database: Lưu vào MySQL/PostgreSQL
- Dashboard: Tích hợp với Grafana/PowerBI

### **Tự động hóa:**
- Cron job (Linux/macOS): `0 */6 * * * cd /path/to/project && python craw.py --account-name "account1" --headless`
- Task Scheduler (Windows): Tạo task chạy script theo lịch
- Docker: Containerize để deploy dễ dàng

## 📝 Changelog

### **v2.0** (Current)
- ✅ Giao diện GUI hiện đại với Material Design
- ✅ Đăng nhập GUI thay vì terminal
- ✅ Quản lý nhiều tài khoản với config.json
- ✅ Parallel processing với đa luồng
- ✅ Auto-scraping theo lịch trình
- ✅ Smart error handling và auto retry
- ✅ Real-time progress tracking

### **v1.0** 
- ✅ Cào dữ liệu analytics cơ bản
- ✅ Đăng nhập terminal
- ✅ Lưu cookies đơn giản

## 🤝 Đóng góp

Mọi đóng góp đều được chào đón! Vui lòng:

1. Fork repository
2. Tạo feature branch
3. Commit changes  
4. Push và tạo Pull Request

## 📄 License

MIT License - Xem file LICENSE để biết chi tiết.

## 🆘 Hỗ trợ

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra phần **Xử lý lỗi** ở trên
2. Tạo Issue trên GitHub với log chi tiết
3. Đính kèm file config.json (ẩn thông tin nhạy cảm)

---

**⭐ Nếu tool hữu ích, đừng quên star repo nhé! ⭐**