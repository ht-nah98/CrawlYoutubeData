# Testing Guide: Account Persistence Bug Fix

## Quick Test Steps

### Test 1: Create New Account and Verify Persistence
**Time:** ~5 minutes (without actual YouTube login)

1. **Start the application**
   ```bash
   python3 src/main.py
   ```

2. **Create new account**
   - Look at the "👤 Tài khoản Google" section
   - Click "🔐 Đăng nhập YouTube" button
   - When Chrome opens, you CAN either:
     - **Option A:** Manually login to YouTube (real test)
     - **Option B:** Close Chrome and cancel (quick test)

3. **After login/cancel, check:**
   - Account appears in dropdown ✓
   - Account shows in "DANH SÁCH TÀI KHOẢN ĐÃ LƯU" section ✓
   - Check `config.json` file contains the account

4. **Verify config.json**
   ```bash
   cat config.json | grep -A 5 "accounts"
   ```
   Should show your account in the `accounts` array

5. **Restart the application**
   ```bash
   python3 src/main.py
   ```

6. **Verify account still appears**
   - Account in dropdown ✓
   - Account in account list display ✓
   - All channels still visible ✓

---

## Test 2: Multiple Accounts
**Time:** ~10 minutes

1. **Create 2-3 accounts** (using Test 1 steps)
2. **Restart application**
3. **Verify all accounts appear**
4. **Switch between accounts**
   - Select different accounts from dropdown
   - Verify correct channels load
5. **Restart again**
6. **Verify all accounts still there**

---

## Test 3: Config.json Structure Validation
**Time:** ~2 minutes

1. **After creating an account, check config.json structure:**
   ```json
   {
     "accounts": [
       {
         "name": "Test Account",
         "cookies_file": "profile/youtube_cookies_Test_Account.json",
         "channels": []
       }
     ]
   }
   ```

2. **Verify:**
   - [ ] `accounts` array exists
   - [ ] Account has `name` field
   - [ ] Account has `cookies_file` field pointing to profile/
   - [ ] `channels` array exists (may be empty)

---

## Test 4: Edge Cases

### 4A: Account with Special Characters
1. Create account named "My Account #1"
2. Verify cookies file is: `youtube_cookies_My_Account__1.json` (sanitized)
3. Verify account appears in config.json with original name
4. Restart and verify it's still there

### 4B: Duplicate Account Names
1. Try creating two accounts with same name
2. System should update the first account (not create duplicate)
3. Verify config.json has only ONE account with that name

### 4C: Manual config.json Editing
1. Manually add account to config.json:
   ```json
   {
     "accounts": [
       {
         "name": "Manual Account",
         "cookies_file": "profile/youtube_cookies_Manual_Account.json",
         "channels": []
       }
     ]
   }
   ```
2. Restart app
3. Account should appear in dropdown

---

## Test 5: Integration with Scraping

1. Create account and login
2. Add channel URL
3. Click "📹 Lấy danh sách video"
4. Account should have channels in config.json
5. Restart app
6. Verify account + channels still there
7. Can select channels from dropdown

---

## Verification Checklist

### Before Running Application
- [ ] Code changes applied correctly (check app.py lines 1678-1681)
- [ ] `update_accounts_list` is imported at top
- [ ] No syntax errors in the file

### After Login
- [ ] Log shows: "✓ Tài khoản 'Name' đã được lưu vào config.json"
- [ ] Account appears in dropdown
- [ ] Account shows in display area
- [ ] `config.json` updated with account entry

### After Restart
- [ ] Application loads accounts from config.json
- [ ] Accounts appear in dropdown automatically
- [ ] Accounts show in display area
- [ ] Can select and use account without re-login
- [ ] Cookies file still accessible

---

## Log Output Verification

**Expected log messages after login:**

```
✓ Đã lưu cookies vào: profile/youtube_cookies_MyAccount.json
✓ Tài khoản 'MyAccount' đã được lưu vào config.json
✓ Tài khoản mới đã được tạo: MyAccount
```

**Expected log on restart:**

```
✓ Tự động load 1 tài khoản từ config.json
  - Tài khoản 'MyAccount': 0 kênh, 0 video
✓ Đã tự động load 0 video IDs từ 1 tài khoản
✓ Tải tài khoản mặc định: MyAccount
```

---

## Debugging If Test Fails

### Symptom: Account doesn't appear after login

1. **Check cookies saved:**
   ```bash
   ls -la profile/youtube_cookies_*.json
   ```
   Should show the new cookies file

2. **Check config.json:**
   ```bash
   cat config.json
   ```
   Should have account entry

3. **Check logs in application:**
   Look for "Đã lưu vào config.json" message

4. **Verify update_accounts_list is being called:**
   - Add temporary print/log in function
   - Check if message appears

### Symptom: Account disappears on restart

1. **Check config.json isn't being overwritten:**
   ```bash
   git status config.json
   ```

2. **Verify config.json isn't corrupted:**
   ```bash
   python3 -m json.tool config.json
   ```

3. **Check file permissions:**
   ```bash
   ls -la config.json
   ```
   Should be readable and writable

### Symptom: Accounts list shows but can't use account

1. Check cookies file exists
2. Try loading cookies with the account
3. Check if cookies are valid/not expired

---

## Performance Notes

- Loading accounts from config.json: < 100ms
- No significant impact on startup time
- Minimal file I/O (only reading config.json at startup)

---

## Success Criteria

✅ Test passes when:
1. Account created via login
2. Account persists in config.json
3. Account appears after restart
4. Multiple accounts work correctly
5. Account switching works
6. Channels persist with accounts

---

## Rollback Instructions

If issues occur, rollback to previous version:

```bash
git checkout src/gui/app.py
```

This reverts the change. Issue will return but application will still function.
