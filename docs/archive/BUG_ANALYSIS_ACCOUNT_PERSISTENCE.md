# Bug Analysis: Accounts Disappearing After Restart

## Problem Summary
When users login to an account in the GUI, the account is created and appears. However, after restarting the tool, the account is no longer visible in the dropdown list.

## Root Causes Identified

### 1. **Missing `update_accounts_list()` Call in GUI Login (CRITICAL)**
**Location:** `src/gui/app.py:1620` in `gui_login_and_save_cookies()`

**Issue:** The GUI login function (`gui_login_and_save_cookies()`) saves cookies to a file but **NEVER calls** `update_accounts_list()` to update `config.json`.

**Impact:** The account is created in memory during the session, but NOT persisted to `config.json`. When the app restarts, there's no account data to load.

**Code Evidence:**
```python
# Lines 1620-1687: gui_login_and_save_cookies()
# This function:
# ✓ Creates Chrome driver
# ✓ Shows login dialog
# ✓ Gets cookies from driver
# ✓ Saves cookies to file (line 1673-1674)
# ✗ MISSING: Does NOT call update_accounts_list() to save account to config.json
```

### 2. **Account Dropdown Population Logic Issue (SECONDARY)**
**Location:** `src/gui/app.py:2086-2101` in `get_account_names()`

**Issue:** When you create a new account via login, the code tries to refresh the dropdown:
```python
# Lines 2281-2285: After successful login
account_names = self.get_account_names()  # Gets from config.json
if CUSTOM_TK_AVAILABLE:
    self.account_dropdown.configure(values=account_names)
else:
    self.account_dropdown.configure(values=account_names)

self.account_var.set(account_name)
self.on_account_changed()
```

**The problem:** Since `update_accounts_list()` was never called, `config.json` has no record of the new account. When `get_account_names()` reads `config.json`, it returns an empty list (or doesn't include the new account).

### 3. **Account Display vs Config.json Mismatch (TERTIARY)**
**Location:** `src/gui/app.py:2438-2468` in `display_accounts_in_ui()`

**Issue:** The UI shows accounts from `config.json` in the "DANH SÁCH TÀI KHOẢN ĐÃ LƯU" section. If accounts aren't saved to `config.json`, this display is empty.

## Why Cookies Are Saved But Account Isn't

The code flow is:
1. User clicks "🔐 Đăng nhập YouTube"
2. → Calls `on_login_button_click()` (lines ~2240)
3. → Calls `gui_login_and_save_cookies(account_name)` (line 1620)
4. → Saves cookies to file ✓
5. → **BUT** does NOT call `update_accounts_list(account_name, cookies_file)` ✗
6. → Returns to GUI, tries to refresh dropdown
7. → `get_account_names()` reads `config.json` (which has no record of the account)
8. → Dropdown shows empty or outdated list

On restart:
- GUI loads from `config.json`
- `config.json` has no account record → accounts list is empty
- User sees "Chưa có tài khoản nào"

## Complete Fix Needed

### Fix 1: Add `update_accounts_list()` Call
After successfully saving cookies in `gui_login_and_save_cookies()`, call:
```python
update_accounts_list(account_name, cookies_file)
```

### Fix 2: Ensure config.json is properly loaded
Make sure the account dropdown is refreshed from the updated `config.json`.

### Fix 3: Add Persistence Verification
Test that after login, accounts appear in:
- The dropdown list
- The account display area
- Persists across restart

## Files That Need Changes
1. `src/gui/app.py` - Line 1676 area: Add `update_accounts_list()` call
2. Test coverage - Verify account persistence after restart

## Expected Behavior After Fix
1. User logs in with account name
2. Cookies saved + Account added to config.json
3. Dropdown updates to show the new account
4. On restart: Account still visible and functional
5. User can switch between multiple accounts seamlessly
