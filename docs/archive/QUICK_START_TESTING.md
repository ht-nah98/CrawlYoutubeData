# Quick Start Testing Guide

## 5-Minute Test

```bash
# 1. Start the app
python3 src/main.py

# 2. Create Account "Test1"
   - Click "🔐 Đăng nhập YouTube"
   - Enter name: "Test1"
   - Close browser or login
   ✓ Account created

# 3. Add Channel to Test1
   - Dropdown shows: "Test1"
   - Enter URL: https://www.youtube.com/@testchannel
   - Click "📹 Lấy danh sách video"
   - Log shows: "Saving to account: Test1" ✓ [BUG #2 FIXED]

# 4. Check config.json
   cat config.json
   ✓ Should show: {"accounts": [{"name": "Test1", "channels": [...]}]}

# 5. Close app
   - Press Ctrl+C or close window

# 6. Restart app
   python3 src/main.py
   ✓ Test1 still visible in dropdown [BUG #1 FIXED]
   ✓ Channels still there [BUG #1 FIXED]
```

## Expected Log Output

```
When creating account:
  ✓ Đã lưu cookies vào: profile/youtube_cookies_Test1.json
  ✓ Tài khoản 'Test1' đã được lưu vào config.json  [BUG #1]

When adding channel:
  Đang lưu kênh vào tài khoản: Test1...  [BUG #2]
  ✓ Đã lưu vào config.json

When scraping:
  [1/1] 🔄 Cào tài khoản: Test1
  👤 Cookies: profile/youtube_cookies_Test1.json  [BUG #2]
  📹 Số kênh: 1
     ├─ Kênh 1: https://www.youtube.com/@testchannel (50 videos)
  ✓ Sử dụng cookies của Test1: profile/youtube_cookies_Test1.json  [BUG #2]
```

## Multi-Account Test

```
1. Create Account "Test1" with 2 channels
2. Create Account "Test2" with 1 channel
3. Restart - Both visible ✓
4. Scrape - Shows which cookies used for each ✓
5. Check logs - Clear account-channel relationships ✓
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Account not saving | Check log for "đã được lưu vào config.json" |
| Channel not linked | Check config.json has channels under account |
| Wrong cookies used | Check log shows correct account name |
| Scraping errors | Verify config.json structure is correct |

## Files to Check

1. **config.json** - Should show accounts > channels structure
2. **Log output** - Should show account names and cookies files
3. **profile/** - Should have youtube_cookies_[name].json files

---

**Status:** Ready for testing! ✅
