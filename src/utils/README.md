# Utils Module - YouTube Analytics Scraper

Module tiện ích tập trung để giảm code duplication và cải thiện maintainability.

## Các Module

### 1. ConfigManager (`config_manager.py`)
Quản lý file `config.json` với validation và type safety.

**Ví dụ sử dụng:**
```python
from utils import ConfigManager

# Khởi tạo
config = ConfigManager()

# Đọc config
accounts = config.get_accounts()
headless = config.get('headless', False)

# Ghi config
config.set('headless', True)
config.add_account('account1', 'profile/cookies.json')
config.save()
```

### 2. Logger (`logger.py`)
Hệ thống logging thay thế print statements.

**Ví dụ sử dụng:**
```python
from utils import setup_logger, get_logger

# Setup logger
logger = setup_logger('my_app', level=logging.INFO)

# Sử dụng
logger.info("Thông tin")
logger.warning("Cảnh báo")
logger.error("Lỗi")
logger.debug("Debug")
```

### 3. ChromeDriverManager (`chrome_driver.py`)
Quản lý Chrome WebDriver với cấu hình chuẩn.

**Ví dụ sử dụng:**
```python
from utils import ChromeDriverManager

# Tạo driver
driver = ChromeDriverManager.create_driver(headless=False)

# Thêm stealth scripts
ChromeDriverManager.add_stealth_scripts(driver)

# Sử dụng driver
driver.get('https://www.youtube.com')
```

### 4. CookieManager (`cookie_manager.py`)
Quản lý cookies YouTube/Google.

**Ví dụ sử dụng:**
```python
from utils import CookieManager

# Khởi tạo
cookie_mgr = CookieManager(account_name='account1')

# Load cookies
cookie_mgr.load_cookies(driver, auto_relogin=True)

# Save cookies
cookie_mgr.save_cookies(driver)
```

### 5. Validators (`validators.py`)
Validation utilities cho input.

**Ví dụ sử dụng:**
```python
from utils import validate_youtube_url, validate_account_name

# Validate URL
is_valid, error = validate_youtube_url('https://youtube.com/@channel')
if not is_valid:
    print(f"Error: {error}")

# Validate account name
is_valid, error = validate_account_name('my_account')
if not is_valid:
    print(f"Error: {error}")
```

### 6. Constants (`constants.py`)
Tất cả constants tập trung ở một nơi.

**Sử dụng:**
```python
from utils.constants import DEFAULT_TIMEOUT, YOUTUBE_BASE_URL

timeout = DEFAULT_TIMEOUT
url = YOUTUBE_BASE_URL
```

## Migration Guide

### Thay thế print statements
```python
# Cũ
print("Thông tin")

# Mới
from utils import get_logger
logger = get_logger()
logger.info("Thông tin")
```

### Thay thế config access
```python
# Cũ
with open('config.json') as f:
    config = json.load(f)
accounts = config.get('accounts', [])

# Mới
from utils import ConfigManager
config = ConfigManager()
accounts = config.get_accounts()
```

### Thay thế Chrome driver creation
```python
# Cũ
options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

# Mới
from utils import ChromeDriverManager
driver = ChromeDriverManager.create_driver(headless=True)
```

## Benefits

1. **Giảm code duplication**: Logic chung được tập trung
2. **Dễ maintain**: Thay đổi ở một nơi, áp dụng toàn bộ
3. **Type safety**: Type hints giúp phát hiện lỗi sớm
4. **Testability**: Dễ test các utility functions
5. **Consistency**: Cùng một cách làm việc trong toàn bộ project



