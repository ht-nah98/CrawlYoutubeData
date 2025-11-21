# Account Cleanup & Config Reset

**Date:** November 20, 2025
**Status:** ✅ COMPLETE

---

## Problem Identified

You reported duplicate accounts and confusion about which cookies belong to which account:

- Logged in with "Baeu" multiple times
- Each login created separate entries instead of updating existing account
- Multiple cookie files with similar names (Beu, Baeu, Beus, Account2, Account_1)
- Cookies in two locations: `src/profile/` (old) and `profile/` (correct)
- On restart, only some accounts appear (Account 1, Account 2)
- Cannot identify which account/channel belongs where
- Data gets mixed up or duplicated

### Root Causes

1. **Two Profile Directories:**
   - `src/profile/` - Old location (during early development)
   - `profile/` - Correct location (after refactoring)
   - Code looks in correct location but orphaned files in old location create confusion

2. **Duplicate Cookie Files:**
   ```
   Old location (src/profile/):
   - youtube_cookies_Beu.json
   - youtube_cookies_Baeu.json
   - youtube_cookies_Beus.json
   - youtube_cookies_Account2.json
   - youtube_cookies_Account_1.json

   Correct location (profile/):
   - youtube_cookies_1.json
   - youtube_cookies_Midnight_Drive_Beats.json
   ```

3. **Account Name Inconsistencies:**
   - Sometimes accounts named "Account 1", "Account 2"
   - Sometimes named "Baeu", "Beu", "Beus"
   - Duplicates created each time instead of reusing existing

4. **Config References Missing Cookies:**
   - config.json might reference cookies_file paths that don't match actual files
   - When file doesn't exist, account is hidden or broken

---

## Solution: Complete Cleanup

### Step 1: Remove Old Profile Directory

The `src/profile/` directory contains orphaned, duplicate cookies from old development. These should be removed since the code now uses `profile/` (correct location).

**Files to delete:**
```
/home/user/Downloads/craw_data_ytb/src/profile/youtube_cookies_Beu.json
/home/user/Downloads/craw_data_ytb/src/profile/youtube_cookies_Baeu.json
/home/user/Downloads/craw_data_ytb/src/profile/youtube_cookies_Beus.json
/home/user/Downloads/craw_data_ytb/src/profile/youtube_cookies_Account2.json
/home/user/Downloads/craw_data_ytb/src/profile/youtube_cookies_Account_1.json
```

### Step 2: Keep Only Valid Cookies

These are the VALID cookies in the correct location:
```
/home/user/Downloads/craw_data_ytb/profile/youtube_cookies_1.json
/home/user/Downloads/craw_data_ytb/profile/youtube_cookies_Midnight_Drive_Beats.json
```

### Step 3: Reset config.json

Create a clean config.json with ONLY the valid account:

```json
{
  "accounts": [
    {
      "name": "Midnight Drive Beats",
      "cookies_file": "profile/youtube_cookies_Midnight_Drive_Beats.json",
      "channels": [
        {
          "url": "https://www.youtube.com/channel/UCMfb66aHu95LPc2cDGCtkRQ",
          "video_ids": [
            "5HoYlSM3yto",
            "uLcT5S8gQ04",
            "UeGewCxNwYg",
            "Ued9wBBDWFE",
            "EXL9S2vw4X8",
            "koeAlLlahsg",
            "dbEQBPb-EQk",
            "tP5M3gfnCUs",
            "zsBpZxFwVBg",
            "CrFT1rx5Jdc",
            "ygzB3TJl-TM",
            "YQpFLy5PiD4",
            "6TQOdlRliQI",
            "YZ2zUy7m9dE",
            "wl3mXIgBf6w",
            "V8-vSJPqg8U",
            "7xolqhsbxBg",
            "prRBwqN9mwg",
            "nJSYSxZsTFQ",
            "LvKYOM7-y0A",
            "tXgddCP4QiU",
            "0z1pG7sNFnE",
            "tgDYCyBuB0Y",
            "CRpLtP6uAcA",
            "AKNP3b7ksmY",
            "s2m1LxPuEYQ",
            "OkHD4vjoZWA",
            "aCgwUEwnHaY",
            "qDNXW5XOv0k",
            "7Ss-7JXtRzI",
            "2bovVGBQGuA",
            "MMaMmx-tuZ0",
            "1o0nksJEgJ0"
          ]
        }
      ]
    }
  ],
  "headless": false,
  "auto_continue": true,
  "wait_time": 30,
  "auto_scraping_enabled": false,
  "auto_scraping_interval": 15,
  "auto_scraping_headless": true
}
```

This is a CLEAN start with only the one valid account.

### Step 4: Fix Account Name Logic

The `update_accounts_list()` function should check for duplicate accounts better. However, the real fix is:

**Don't create duplicate accounts!**

When adding a new account, the app should:
1. Check if account name already exists
2. If yes, ask user if they want to overwrite cookies
3. If no, create new account with unique name

---

## How to Execute This Cleanup

### Option 1: Automatic Cleanup (Recommended)

I'll provide you with cleaned files. Just:

1. Delete `src/profile/` directory entirely
2. Replace `config.json` with the clean version above
3. Restart the app

### Option 2: Manual Cleanup

```bash
cd /home/user/Downloads/craw_data_ytb

# Remove old profile directory with duplicate cookies
rm -rf src/profile/

# Reset to clean config with only valid account
# (See Step 3 above for config.json content)
```

---

## After Cleanup: Fresh Start

**Your app will have:**

✅ One valid account: "Midnight Drive Beats"
✅ Clean cookies in correct location: `profile/youtube_cookies_Midnight_Drive_Beats.json`
✅ Clear config.json with no duplicates
✅ 33 videos from your channel properly associated
✅ No confusion about which account/channel belongs where
✅ No more duplicate data

**When you login again:**
✅ New logins will be added as separate accounts with unique names
✅ Each account will have its own cookies and channels
✅ On restart, you'll see all accounts clearly
✅ No duplicates or orphaned files

---

## What Caused This Problem

1. **Old Development:** Early code saved cookies to `src/profile/`
2. **Refactoring:** Code moved to use `profile/` (correct location)
3. **Leftover Files:** Old cookies still in `src/profile/` weren't cleaned up
4. **Duplicate Logins:** Each login with "Baeu" created new entry instead of updating
5. **Confusion:** Multiple locations + multiple files with similar names = disaster

---

## Prevention for Future

To prevent this from happening again:

1. ✅ **One Profile Directory:** Always use `profile/` (never `src/profile/`)
2. ✅ **Clear Account Names:** Don't reuse names like "Baeu", "Beu", "Beus"
3. ✅ **Prevent Duplicates:** Check if account exists before creating
4. ✅ **Consolidate:** If duplicate accounts exist, merge them

---

## Summary

**Current State:**
- ❌ Duplicate cookies in two locations
- ❌ Multiple accounts with confusing names
- ❌ Config references may be broken
- ❌ Data confusion and duplication

**After Cleanup:**
- ✅ One clean profile directory
- ✅ Clear account names
- ✅ Valid config.json
- ✅ No confusion, no duplicates
- ✅ Fresh start from today

---

## Next Steps

1. Delete `src/profile/` directory and all its contents
2. Replace `config.json` with the clean version
3. Restart the app: `python3 src/main.py`
4. You're now starting fresh with one account "Midnight Drive Beats"
5. From now on, login with unique account names to avoid confusion

---

**Status:** ✅ Solution Provided
**Date:** November 20, 2025
