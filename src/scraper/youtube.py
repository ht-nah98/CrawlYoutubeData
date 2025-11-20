"""
Script cào dữ liệu analytics từ YouTube Studio
Chỉ tập trung vào việc cào dữ liệu, không quản lý tài khoản

Lưu ý:
- File này chỉ dùng để CÀO DỮ LIỆU từ YouTube Studio
- Để quản lý tài khoản (đăng nhập, lưu cookies, chọn tài khoản), sử dụng get_channel_videos.py
- Cookies phải được setup trước thông qua get_channel_videos.py hoặc config.json

Cách sử dụng:
1. Setup cookies trước bằng get_channel_videos.py:
   python get_channel_videos.py "URL" --account-name "MyAccount"

2. Chạy cào dữ liệu với account cụ thể (BẮT BUỘC):
   python craw.py --account-name "1"
   
   Script sẽ:
   - Tìm account "1" trong config.json
   - Lấy cookies_file từ account đó
   - Lấy tất cả channels của account đó
   - Cào dữ liệu analytics cho tất cả video IDs trong các channels

3. Các tùy chọn khác:
   python craw.py --account-name "1" --headless        # Chạy ở chế độ headless

Lưu ý: --account-name là BẮT BUỘC. Script sẽ không chạy nếu thiếu argument này.
"""
import time
import json
import re
import os
import sys
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Fix encoding cho Windows console
if sys.platform == 'win32':
    try:
        # Thử set UTF-8 encoding cho stdout và stderr
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        # Fallback: wrap stdout/stderr với UTF-8
        import io
        try:
            if not isinstance(sys.stdout, io.TextIOWrapper) or (hasattr(sys.stdout, 'encoding') and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8'):
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
            if not isinstance(sys.stderr, io.TextIOWrapper) or (hasattr(sys.stderr, 'encoding') and sys.stderr.encoding and sys.stderr.encoding.lower() != 'utf-8'):
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        except:
            pass

# Monkey-patch print function để tự động xử lý encoding errors
_original_print = print
def safe_print(*args, **kwargs):
    """Print function an toàn với Unicode trên Windows"""
    try:
        _original_print(*args, **kwargs)
    except UnicodeEncodeError:
        # Nếu vẫn lỗi, encode sang UTF-8 với errors='replace'
        try:
            message = ' '.join(str(arg) for arg in args)
            # Thử encode/decode với UTF-8
            encoded = message.encode('utf-8', errors='replace')
            decoded = encoded.decode('utf-8', errors='replace')
            _original_print(decoded, **kwargs)
        except:
            # Cuối cùng, dùng ASCII với thay thế ký tự
            try:
                message = ' '.join(str(arg) for arg in args)
                encoded = message.encode('ascii', errors='replace')
                decoded = encoded.decode('ascii', errors='replace')
                _original_print(decoded, **kwargs)
            except:
                # Nếu vẫn lỗi, chỉ in thông báo lỗi
                _original_print("(Encoding error: unable to print message)", **kwargs)

# Thay thế print bằng safe_print trên Windows
if sys.platform == 'win32':
    import builtins
    builtins.print = safe_print

# Lock cho thread-safe printing
print_lock = Lock()

def thread_safe_print(*args, **kwargs):
    """Thread-safe print function"""
    with print_lock:
        safe_print(*args, **kwargs)


class YouTubeAnalyticsScraper:
    def __init__(self, cookies_file=None, account_name=None, auto_continue=False, wait_time=30):
        # Đảm bảo thư mục profile tồn tại
        os.makedirs('profile', exist_ok=True)

        # Lưu các settings cho login
        self.auto_continue = auto_continue
        self.wait_time = wait_time
        
        # Ưu tiên cookies_file nếu được cung cấp trực tiếp (từ config.json)
        if cookies_file:
            # Nếu cookies_file không có đường dẫn đầy đủ, đặt vào thư mục profile
            if not os.path.dirname(cookies_file) and cookies_file == 'youtube_cookies.json':
                self.cookies_file = os.path.join('profile', cookies_file)
            else:
                self.cookies_file = cookies_file
            # Thử extract account_name từ cookies_file nếu có pattern
            match = re.search(r'youtube_cookies_(.+)\.json$', self.cookies_file)
            self.account_name = match.group(1) if match else None
            # Nếu account_name được cung cấp và khác với extracted, ưu tiên account_name được cung cấp
            if account_name:
                self.account_name = account_name
        elif account_name:
            # Tạo tên file cookies dựa trên account_name
            # Loại bỏ ký tự đặc biệt để tránh lỗi tên file
            safe_account_name = re.sub(r'[^\w\-_]', '_', account_name)
            self.cookies_file = os.path.join('profile', f'youtube_cookies_{safe_account_name}.json')
            self.account_name = account_name
        else:
            # Mặc định: dùng cookies file mặc định
            self.cookies_file = os.path.join('profile', 'youtube_cookies.json')
            self.account_name = None
        
        self.driver = None
        
    def init_driver(self, headless=False):
        """Khởi tạo Chrome driver với retry mechanism"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
            # Thêm các options để bypass headless detection
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            # Add window size for headless
            chrome_options.add_argument('--window-size=1920,1080')
            # Spoof user agent to look like regular browser
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Fix GPU và virtualization errors trên Windows - thêm nhiều options
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-gpu-sandbox')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-webgl')
        chrome_options.add_argument('--disable-webgl2')
        chrome_options.add_argument('--disable-3d-apis')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--use-gl=swiftshader')
        chrome_options.add_argument('--disable-accelerated-2d-canvas')
        chrome_options.add_argument('--disable-accelerated-video-decode')
        chrome_options.add_argument('--disable-accelerated-video-encode')
        chrome_options.add_argument('--disable-gpu-compositing')
        chrome_options.add_argument('--disable-gpu-rasterization')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        
        # Suppress GPU errors
        chrome_options.add_argument('--log-level=3')  # Chỉ hiện lỗi nghiêm trọng
        prefs = {
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Thử khởi tạo driver với retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                safe_print(f"Đang khởi tạo Chrome driver (lần thử {attempt + 1}/{max_retries})...")
                self.driver = webdriver.Chrome(options=chrome_options)
                
                # Đợi một chút để Chrome ổn định
                time.sleep(2)
                
                # Kiểm tra xem driver còn sống không
                try:
                    self.driver.current_url
                except Exception:
                    raise Exception("Chrome driver bị đóng ngay sau khi khởi tạo")
                
                self.driver.maximize_window()
                safe_print("Chrome driver đã khởi tạo thành công!")
                return
                
            except Exception as e:
                safe_print(f"Lỗi khi khởi tạo Chrome driver (lần thử {attempt + 1}): {str(e)}")
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                
                if attempt < max_retries - 1:
                    safe_print(f"Đợi 3 giây trước khi thử lại...")
                    time.sleep(3)
                else:
                    raise Exception(f"Không thể khởi tạo Chrome driver sau {max_retries} lần thử: {str(e)}")
        
    def login_google(self, headless=False):
        """Đăng nhập Google và lưu cookies

        Args:
            headless: Nếu True, sẽ không yêu cầu input (dùng cho headless mode)
        """
        print("Đang mở trang đăng nhập Google...")
        self.driver.get('https://accounts.google.com')

        if not headless:
            if self.auto_continue:
                print(f"\nVui lòng đăng nhập thủ công trong trình duyệt...")
                print(f"Sẽ tự động tiếp tục sau {self.wait_time} giây...")
                time.sleep(self.wait_time)
                print("Tiếp tục...")
            else:
                print("\nVui lòng đăng nhập thủ công trong trình duyệt...")
                print("Sau khi đăng nhập xong, nhấn Enter ở đây để tiếp tục...")
                try:
                    input()
                except (EOFError, KeyboardInterrupt):
                    print("⚠ Không thể đọc input. Tiếp tục...")
        else:
            print("\n⚠ Headless mode: Vui lòng đăng nhập trong trình duyệt (nếu có)...")
            print(f"   Đợi {self.wait_time} giây để bạn đăng nhập...")
            time.sleep(self.wait_time)
        
        # Điều hướng đến YouTube để lấy cookies của YouTube
        print("\nĐang điều hướng đến YouTube để lấy cookies...")
        self.driver.get('https://www.youtube.com')
        time.sleep(10)  # Đợi trang YouTube load xong
        
        # Lưu cookies (sẽ bao gồm cả cookies của YouTube)
        self.save_cookies()
        print("Đã lưu cookies thành công!")
    
    def check_login_status(self):
        """Kiểm tra xem đã đăng nhập vào YouTube chưa
        
        Returns:
            bool: True nếu đã đăng nhập, False nếu chưa
        """
        try:
            # Truy cập YouTube Studio để kiểm tra
            self.driver.get('https://studio.youtube.com')
            time.sleep(5)
            
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            # Kiểm tra xem có bị redirect về login không
            if 'accounts.google.com' in current_url or 'signin' in current_url:
                print("⚠ Phát hiện: Chưa đăng nhập hoặc cookies đã hết hạn")
                return False
            
            # Kiểm tra các dấu hiệu đã đăng nhập
            logged_in_indicators = [
                'studio.youtube.com' in current_url,
                'analytics' in page_source or 'content' in page_source,
                'avatar' in page_source or 'account' in page_source
            ]
            
            if any(logged_in_indicators):
                print("✓ Đã đăng nhập vào YouTube Studio")
                return True
            else:
                print("⚠ Không chắc chắn trạng thái đăng nhập")
                return False
                
        except Exception as e:
            print(f"Lỗi khi kiểm tra trạng thái đăng nhập: {str(e)}")
            return False
    
    def auto_relogin_if_needed(self, headless=False):
        """Tự động đăng nhập lại nếu cookies hết hạn
        
        Args:
            headless: Chế độ headless
            
        Returns:
            bool: True nếu đăng nhập thành công, False nếu thất bại
        """
        print("\n" + "="*50)
        print("PHÁT HIỆN COOKIES HẾT HẠN - TỰ ĐỘNG ĐĂNG NHẬP LẠI")
        print("="*50)
        
        try:
            # Kiểm tra trạng thái đăng nhập
            if self.check_login_status():
                print("✓ Vẫn còn đăng nhập, không cần đăng nhập lại")
                return True
            
            # Nếu chưa đăng nhập, thử đăng nhập lại
            print("\nCookies đã hết hạn. Đang đăng nhập lại...")
            self.login_google(headless=headless)
            
            # Kiểm tra lại sau khi đăng nhập
            if self.check_login_status():
                print("✓ Đăng nhập lại thành công!")
                return True
            else:
                print("⚠ Đăng nhập lại không thành công. Vui lòng thử lại thủ công.")
                return False
                
        except Exception as e:
            print(f"Lỗi khi đăng nhập lại: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
    def save_cookies(self):
        """Lưu cookies vào file JSON"""
        cookies = self.driver.get_cookies()
        # Đảm bảo thư mục tồn tại nếu có path
        cookies_dir = os.path.dirname(self.cookies_file)
        if cookies_dir and not os.path.exists(cookies_dir):
            os.makedirs(cookies_dir, exist_ok=True)
            print(f"Đã tạo thư mục: {cookies_dir}")
        with open(self.cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu cookies vào: {self.cookies_file}")
        
        # Cập nhật danh sách tài khoản nếu có account_name
        if self.account_name:
            update_accounts_list(self.account_name, self.cookies_file)
    
    def _parse_cookie_header_text(self, raw_text):
        """Chuyển đổi định dạng 'Cookie' header ("a=1; b=2; ...")
        thành list cookies Selenium cho youtube.com.
        Cho phép phần user-agent sau dấu '|' và sẽ bỏ qua.
        """
        try:
            # Lấy phần trước ký tự '|' nếu có (bỏ UA)
            header = raw_text.split('|', 1)[0].strip()
            if not header:
                return []
            pairs = [p.strip() for p in header.split(';') if p.strip()]
            cookies = []
            for pair in pairs:
                if '=' not in pair:
                    continue
                name, value = pair.split('=', 1)
                name = name.strip()
                value = value.strip()
                if not name:
                    continue
                cookies.append({
                    'name': name,
                    'value': value,
                    'domain': '.youtube.com',
                    'path': '/',
                })
            return cookies
        except Exception:
            return []
            
    def load_cookies(self, headless=False, auto_relogin=True):
        """Load cookies từ file JSON
        
        Args:
            headless: Chế độ headless
            auto_relogin: Tự động đăng nhập lại nếu cookies hết hạn (mặc định: True)
        """
        try:
            # Đọc cookies từ file
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                file_text = f.read().strip()
                cookies = None
                # Thử parse JSON trước
                try:
                    cookies = json.loads(file_text)
                except Exception:
                    # Fallback: parse kiểu Cookie header
                    cookies = self._parse_cookie_header_text(file_text)
            
            if not cookies:
                print("File cookies rỗng. Cần đăng nhập lại.")
                return False
            
            print(f"Đã đọc {len(cookies)} cookies từ file")
            
            # Phân loại cookies theo domain
            youtube_cookies = []
            google_cookies = []
            other_cookies = []
            
            for cookie in cookies:
                if not isinstance(cookie, dict):
                    continue
                domain = cookie.get('domain', '').lower()
                if not domain:
                    # Nếu không có domain, thử thêm domain mặc định
                    cookie['domain'] = '.youtube.com'
                    youtube_cookies.append(cookie)
                elif 'youtube.com' in domain:
                    youtube_cookies.append(cookie)
                elif 'google.com' in domain:
                    google_cookies.append(cookie)
                else:
                    other_cookies.append(cookie)
            
            print(f"Phân loại: {len(youtube_cookies)} YouTube cookies, {len(google_cookies)} Google cookies, {len(other_cookies)} cookies khác")
            
            # Load cookies cho từng domain
            domains_to_load = [
                ('https://www.youtube.com', youtube_cookies),
                ('https://accounts.google.com', google_cookies),
                ('https://www.youtube.com', other_cookies)  # Thử load cookies khác vào YouTube
            ]
            
            total_added = 0
            total_failed = 0
            
            for url, cookie_list in domains_to_load:
                if not cookie_list:
                    continue
                
                try:
                    print(f"\nĐang load cookies cho {url}...")
                    self.driver.get(url)
                    time.sleep(2)
                    
                    added_count = 0
                    failed_count = 0
                    
                    for cookie in cookie_list:
                        try:
                            # Tạo bản copy của cookie để tránh modify original
                            cookie_to_add = cookie.copy()
                            
                            # Đảm bảo có name và value
                            if 'name' not in cookie_to_add or 'value' not in cookie_to_add:
                                failed_count += 1
                                continue
                            
                            # Xử lý domain
                            domain = cookie_to_add.get('domain', '')
                            if not domain:
                                # Nếu đang ở YouTube, dùng domain YouTube
                                if 'youtube.com' in url:
                                    cookie_to_add['domain'] = '.youtube.com'
                                elif 'google.com' in url:
                                    cookie_to_add['domain'] = '.google.com'
                            
                            # Normalize domain: nếu domain bắt đầu bằng dấu chấm, giữ nguyên
                            # Nếu không, thêm dấu chấm nếu cần
                            if domain and not domain.startswith('.'):
                                # Kiểm tra xem có phải là subdomain không
                                if 'youtube.com' in domain and domain != 'youtube.com':
                                    cookie_to_add['domain'] = '.youtube.com'
                                elif 'google.com' in domain and domain != 'google.com':
                                    cookie_to_add['domain'] = '.google.com'
                            
                            # Xử lý expiry nếu có
                            if 'expiry' in cookie_to_add:
                                try:
                                    expiry = cookie_to_add['expiry']
                                    if isinstance(expiry, (int, float)):
                                        # Kiểm tra xem expiry có còn hợp lệ không (chưa hết hạn)
                                        if expiry < time.time():
                                            print(f"Cookie {cookie_to_add.get('name', 'unknown')} đã hết hạn, bỏ qua")
                                            failed_count += 1
                                            continue
                                        cookie_to_add['expiry'] = int(expiry)
                                    else:
                                        # Nếu không phải số, xóa bỏ
                                        del cookie_to_add['expiry']
                                except:
                                    if 'expiry' in cookie_to_add:
                                        del cookie_to_add['expiry']
                            
                            # Xử lý path nếu không có
                            if 'path' not in cookie_to_add:
                                cookie_to_add['path'] = '/'
                            
                            # Xóa các thuộc tính không hợp lệ cho Selenium
                            # Selenium không hỗ trợ httpOnly, sameSite trực tiếp
                            # Nhưng có thể bỏ qua chúng
                            invalid_keys = ['httpOnly', 'sameSite', 'storeId', 'hostOnly']
                            for key in invalid_keys:
                                cookie_to_add.pop(key, None)
                            
                            # Thử thêm cookie
                            self.driver.add_cookie(cookie_to_add)
                            added_count += 1
                            
                        except Exception as e:
                            # Log lỗi chi tiết hơn
                            cookie_name = cookie.get('name', 'unknown')
                            print(f"  Không thể thêm cookie '{cookie_name}': {str(e)}")
                            failed_count += 1
                            continue
                    
                    print(f"  → Đã load {added_count} cookies thành công cho {url}")
                    if failed_count > 0:
                        print(f"  → Bỏ qua {failed_count} cookies không hợp lệ")
                    
                    total_added += added_count
                    total_failed += failed_count
                    
                except Exception as e:
                    print(f"Lỗi khi load cookies cho {url}: {str(e)}")
                    continue
            
            print(f"\nTổng kết: Đã load {total_added} cookies thành công, bỏ qua {total_failed} cookies")
            
            # Quay lại YouTube và refresh để áp dụng cookies
            print("\nĐang quay lại YouTube và áp dụng cookies...")
            self.driver.get('https://www.youtube.com')
            time.sleep(3)
            
            # Kiểm tra xem cookies đã được áp dụng chưa bằng cách kiểm tra URL hoặc element
            try:
                # Đợi một chút để trang load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, 'body'))
                )
                
                # Kiểm tra xem có đăng nhập không (có thể kiểm tra bằng cách tìm avatar hoặc menu)
                current_url = self.driver.current_url
                page_source = self.driver.page_source.lower()
                
                # Các dấu hiệu đã đăng nhập: có avatar, có menu account, không redirect về login
                logged_in_indicators = [
                    'avatar' in page_source,
                    'account' in page_source and 'menu' in page_source,
                    'sign in' not in page_source or 'sign in' in page_source and 'avatar' in page_source
                ]
                
                if any(logged_in_indicators) and 'accounts.google.com' not in current_url:
                    print("✓ Cookies đã được áp dụng thành công! Đã đăng nhập vào YouTube.")
                    return True
                else:
                    print("⚠ Cảnh báo: Cookies có thể chưa được áp dụng đúng cách hoặc đã hết hạn.")
                    # Tự động đăng nhập lại nếu được bật
                    if auto_relogin:
                        print("\nĐang thử đăng nhập lại tự động...")
                        if self.auto_relogin_if_needed(headless=headless):
                            return True
                    return False
                    
            except Exception as e:
                print(f"Không thể kiểm tra trạng thái đăng nhập: {str(e)}")
                # Nếu có cookies nhưng không kiểm tra được, thử auto relogin
                if auto_relogin and total_added > 0:
                    if self.auto_relogin_if_needed(headless=headless):
                        return True
                return total_added > 0
            
        except FileNotFoundError:
            print("Không tìm thấy file cookies JSON. Cần đăng nhập lại.")
            # Tự động đăng nhập lại nếu được bật
            if auto_relogin:
                print("\nĐang thử đăng nhập lại tự động...")
                if self.auto_relogin_if_needed(headless=headless):
                    return True
            return False
        except Exception as e:
            print(f"Lỗi khi load cookies: {str(e)}")
            import traceback
            traceback.print_exc()
            # Tự động đăng nhập lại nếu được bật
            if auto_relogin:
                print("\nĐang thử đăng nhập lại tự động...")
                if self.auto_relogin_if_needed(headless=headless):
                    return True
            return False
    
    def switch_account(self, account_name=None, cookies_file=None):
        """Chuyển đổi sang tài khoản khác trong cùng session
        
        Args:
            account_name: Tên tài khoản để chuyển đổi (ưu tiên)
            cookies_file: Đường dẫn đến file cookies (nếu không có account_name)
        
        Returns:
            bool: True nếu chuyển đổi thành công, False nếu thất bại
        """
        if not self.driver:
            print("Driver chưa được khởi tạo. Không thể chuyển đổi tài khoản.")
            return False
        
        # Xác định cookies_file mới
        new_cookies_file = None
        new_account_name = None
        
        if account_name:
            safe_account_name = re.sub(r'[^\w\-_]', '_', account_name)
            new_cookies_file = os.path.join('profile', f'youtube_cookies_{safe_account_name}.json')
            new_account_name = account_name
        elif cookies_file:
            new_cookies_file = cookies_file
            # Thử extract account_name từ cookies_file
            match = re.search(r'youtube_cookies_(.+)\.json$', cookies_file)
            new_account_name = match.group(1) if match else None
        else:
            print("Cần cung cấp account_name hoặc cookies_file để chuyển đổi tài khoản.")
            return False
        
        # Kiểm tra file cookies có tồn tại không
        if not os.path.exists(new_cookies_file):
            print(f"Không tìm thấy file cookies: {new_cookies_file}")
            return False
        
        print(f"\n{'='*50}")
        print(f"Đang chuyển đổi tài khoản...")
        if new_account_name:
            print(f"Tài khoản mới: {new_account_name}")
        print(f"Cookies file: {new_cookies_file}")
        print(f"{'='*50}")
        
        try:
            # Xóa tất cả cookies hiện tại
            print("Đang xóa cookies hiện tại...")
            self.driver.delete_all_cookies()
            
            # Cập nhật cookies_file và account_name
            old_cookies_file = self.cookies_file
            old_account_name = self.account_name
            self.cookies_file = new_cookies_file
            self.account_name = new_account_name
            
            # Load cookies mới
            print("Đang load cookies mới...")
            # Lấy headless từ driver nếu có (giả định không headless nếu không có driver)
            headless_mode = False
            if self.driver:
                # Không có cách trực tiếp để biết headless, mặc định False
                headless_mode = False
            if self.load_cookies(headless=headless_mode):
                print(f"✓ Đã chuyển đổi sang tài khoản: {new_account_name or 'Unknown'}")
                # Cập nhật last_used nếu có account_name
                if new_account_name:
                    update_accounts_list(new_account_name, new_cookies_file)
                return True
            else:
                # Khôi phục lại cookies cũ nếu load thất bại
                print("⚠ Không thể load cookies mới. Khôi phục lại tài khoản cũ...")
                self.cookies_file = old_cookies_file
                self.account_name = old_account_name
                if os.path.exists(old_cookies_file):
                    self.load_cookies(headless=headless_mode)
                return False
                
        except Exception as e:
            print(f"Lỗi khi chuyển đổi tài khoản: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
            
    def retry_find_elements_with_scroll(self, selector, max_retries=3, scroll_attempts=2):
        """Retry tìm elements với scroll để trigger dynamic loading

        Args:
            selector: CSS selector để tìm
            max_retries: Số lần retry tối đa
            scroll_attempts: Số lần scroll mỗi retry

        Returns:
            list: Danh sách elements tìm được
        """
        for attempt in range(max_retries):
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  [DEBUG] Tìm thấy {len(elements)} elements với selector '{selector}' ở attempt {attempt + 1}")
                    return elements

                # Nếu không tìm thấy, thử scroll để trigger loading
                print(f"  [DEBUG] Attempt {attempt + 1}: Không tìm thấy elements, thử scroll...")

                for scroll_attempt in range(scroll_attempts):
                    try:
                        # Scroll xuống cuối trang
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)

                        # Scroll lên đầu
                        self.driver.execute_script("window.scrollTo(0, 0);")
                        time.sleep(1)

                        # Scroll đến giữa
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                        time.sleep(1)

                        # Kiểm tra lại sau mỗi lần scroll
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            print(f"  [DEBUG] Tìm thấy {len(elements)} elements sau scroll attempt {scroll_attempt + 1}")
                            return elements

                    except Exception as e:
                        print(f"  [DEBUG] Lỗi khi scroll: {str(e)}")
                        continue

                # Đợi thêm trước retry tiếp theo
                if attempt < max_retries - 1:
                    time.sleep(2)

            except Exception as e:
                print(f"  [DEBUG] Lỗi khi tìm elements ở attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                continue

        print(f"  [DEBUG] Không tìm thấy elements với selector '{selector}' sau {max_retries} attempts")
        return []

    def wait_for_analytics_page_load(self, timeout=30, headless=False):
        """Đợi YouTube Studio Analytics page load hoàn toàn

        Args:
            timeout: Thời gian chờ tối đa (giây)
            headless: Có đang chạy headless mode không

        Returns:
            bool: True nếu page đã load, False nếu timeout
        """
        # Headless mode cần nhiều thời gian hơn
        if headless:
            timeout = max(timeout, 45)  # Tối thiểu 45s cho headless
            print(f"Đang đợi YouTube Studio Analytics page load hoàn toàn (headless mode, timeout: {timeout}s)...")
        else:
            print(f"Đang đợi YouTube Studio Analytics page load hoàn toàn (timeout: {timeout}s)...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Kiểm tra các dấu hiệu page đã load:
                # 1. URL phải chứa analytics
                current_url = self.driver.current_url
                if 'analytics' not in current_url:
                    time.sleep(1)
                    continue

                # 2. Body element phải tồn tại
                body = self.driver.find_element(By.TAG_NAME, 'body')
                page_text = body.text.lower()

                # 3. Kiểm tra các dấu hiệu data đã load
                load_indicators = [
                    'impressions', 'views', 'viewers', 'analytics',
                    'reach', 'engagement', 'traffic sources', 'how viewers find'
                ]

                found_indicators = sum(1 for indicator in load_indicators if indicator in page_text)

                # 4. Thử tìm một số elements chính
                try:
                    # Tìm top section hoặc metric blocks
                    metric_elements = self.driver.find_elements(By.CSS_SELECTOR,
                        'yta-key-metric-block, [class*="yta-key-metric-block"], #top-section, [id="top-section"]')

                    # Tìm traffic source elements
                    traffic_elements = self.driver.find_elements(By.CSS_SELECTOR,
                        '[id^="title-text-"], [class*="title-text"]')

                    # Tìm impressions elements
                    impression_elements = self.driver.find_elements(By.CSS_SELECTOR,
                        'yta-funnel, [class*="funnel"]')

                    total_elements = len(metric_elements) + len(traffic_elements) + len(impression_elements)

                    if headless:
                        print(f"  [HEADLESS] Indicators found: {found_indicators}, Elements found: {total_elements}")
                        # Headless mode cần ít elements hơn để pass
                        if found_indicators >= 1 and total_elements >= 1:
                            print("✓ YouTube Studio Analytics page đã load hoàn toàn (headless mode)!")
                            return True
                    else:
                        print(f"  Indicators found: {found_indicators}, Elements found: {total_elements}")
                        # Nếu có đủ indicators và elements, coi như page đã load
                        if found_indicators >= 3 and total_elements >= 5:
                            print("✓ YouTube Studio Analytics page đã load hoàn toàn!")
                            return True

                except Exception:
                    pass

                # 5. Scroll xuống để trigger loading của dynamic content
                try:
                    # Headless mode cần scroll nhiều hơn và chậm hơn
                    scroll_delay = 1.5 if headless else 0.5

                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 4);")
                    time.sleep(scroll_delay)
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                    time.sleep(scroll_delay)
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 3/4);")
                    time.sleep(scroll_delay)
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(scroll_delay)
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(scroll_delay)
                except Exception:
                    pass

                # Headless mode cần thời gian nghỉ lâu hơn
                sleep_time = 2 if headless else 1
                time.sleep(sleep_time)  # Đợi trước khi kiểm tra lại

            except Exception as e:
                print(f"Lỗi khi kiểm tra page load: {str(e)}")
                time.sleep(1)
                continue

        print(f"⚠ Timeout sau {timeout}s - page có thể chưa load hoàn toàn")
        return False

    def get_video_analytics(self, video_id, headless=False):
        """Lấy analytics của một video

        Args:
            video_id: ID của video
            headless: Chế độ headless (để tự động đăng nhập lại nếu cần)
        """
        url = f'https://studio.youtube.com/video/{video_id}/analytics/tab-reach_viewers/period-default'
        print(f"\nĐang truy cập: {url}")
        self.driver.get(url)

        # Đợi trang load hoàn toàn
        if not self.wait_for_analytics_page_load(timeout=30, headless=headless):
            print("⚠ Cảnh báo: Page có thể chưa load đủ, thử refresh page...")

            # Thử refresh page cho headless mode
            if headless:
                print("  [HEADLESS] Đang refresh page để thử lại...")
                self.driver.refresh()
                time.sleep(5)  # Đợi sau refresh
                if not self.wait_for_analytics_page_load(timeout=20, headless=headless):
                    print("⚠ Cảnh báo: Page vẫn chưa load đủ sau refresh, tiếp tục với dữ liệu có sẵn")
            else:
                print("⚠ Cảnh báo: Page có thể chưa load đủ, tiếp tục với dữ liệu có sẵn")
        
        # Kiểm tra xem có bị redirect về login không
        current_url = self.driver.current_url.lower()
        if 'accounts.google.com' in current_url or 'signin' in current_url:
            print("⚠ Phát hiện: Bị redirect về trang đăng nhập. Cookies có thể đã hết hạn.")
            print("Đang tự động đăng nhập lại...")
            if self.auto_relogin_if_needed(headless=headless):
                # Thử lại sau khi đăng nhập
                print("Đang truy cập lại analytics page...")
                self.driver.get(url)
                time.sleep(8)
            else:
                print("⚠ Không thể đăng nhập lại. Bỏ qua video này.")
                return {
                    'video_id': video_id,
                    'top_metrics': {},
                    'how_viewers_find': {},
                    'impressions_data': {},
                    'publish_start_date': None,
                    'crawl_datetime': datetime.now().strftime('%d/%m/%Y'),
                    'page_text': '',
                    'error': 'Cookies hết hạn và không thể đăng nhập lại'
                }
        
        analytics_data = {
            'video_id': video_id,
            'top_metrics': {},
            'how_viewers_find': {},
            'impressions_data': {},
            'publish_start_date': None,
            'crawl_datetime': None,
            'page_text': ''
        }
        
        try:
            # Lấy toàn bộ text của trang để debug
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            analytics_data['page_text'] = page_text[:500]  # Lưu 500 ký tự đầu
            
            # Ghi nhận thời điểm cào (thời gian thực) theo định dạng Việt Nam DD/MM/YYYY
            analytics_data['crawl_datetime'] = datetime.now().strftime('%d/%m/%Y')
            
            # Lấy ngày bắt đầu đăng (từ label "Aug 13, 2025 — Now") nếu có
            print("Đang lấy ngày bắt đầu đăng video...")
            analytics_data['publish_start_date'] = self.get_publish_start_date()
            
            # Lấy các metrics trong top section (Key metric card)
            print("Đang lấy dữ liệu Top metrics (key metric card)...")
            analytics_data['top_metrics'] = self.get_top_section_metrics()
            
            # Lấy dữ liệu "How viewers find this video"
            print("Đang lấy dữ liệu 'How viewers find this video'...")
            analytics_data['how_viewers_find'] = self.get_traffic_sources()
            
            # Lấy dữ liệu "Impressions and how they led to watch time"
            print("Đang lấy dữ liệu 'Impressions'...")
            analytics_data['impressions_data'] = self.get_impressions_data()
            
        except Exception as e:
            print(f"Lỗi khi lấy dữ liệu: {str(e)}")
            import traceback
            traceback.print_exc()
            
        return analytics_data
    
    def get_publish_start_date(self):
        """Tìm và parse ngày bắt đầu trong label kiểu 'Aug 13, 2025 — Now' bên cạnh 'Since published'.
        Trả về ISO date (YYYY-MM-DD) nếu tìm được, ngược lại trả về None.
        """
        try:
            wait = WebDriverWait(self.driver, 10)
            # Tìm container dropdown trigger thời gian
            candidates = []
            selectors = [
                '.left-container .label-text',
                '[class*="left-container"] [class*="label-text"]',
                '[class*="dropdown-trigger"] [class*="label-text"]',
                '[id*="time" i] [class*="label-text"]'
            ]
            for sel in selectors:
                try:
                    elems = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, sel)))
                    if elems:
                        candidates.extend(elems)
                except TimeoutException:
                    continue
                except Exception:
                    continue
            
            # Lấy text và tìm pattern 'Mon dd, yyyy — Now'
            # Ví dụ: 'Aug 13, 2025 — Now'
            month_pattern = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
            date_regex = re.compile(rf"\b({month_pattern})\s+\d{{1,2}},\s*\d{{4}}\s+—\s+Now\b")
            for el in candidates:
                text = (el.text or '').strip()
                if not text:
                    continue
                m = date_regex.search(text)
                if m:
                    # trích riêng phần ngày ở đầu
                    try:
                        start_str = text.split('—')[0].strip()
                        dt = datetime.strptime(start_str, '%b %d, %Y')
                        return dt.date().isoformat()
                    except Exception:
                        continue
            
            # Nếu không thấy ở label-text, thử lấy sibling của 'Since published'
            try:
                since_elems = self.driver.find_elements(By.XPATH, "//*[contains(., 'Since published')]")
                for s in since_elems:
                    # thử tìm phần tử label-text trong ancestor gần
                    container = s
                    for _ in range(5):
                        try:
                            container = container.find_element(By.XPATH, './..')
                            label_candidates = container.find_elements(By.CSS_SELECTOR, '[class*="label-text"]')
                            for el in label_candidates:
                                text = (el.text or '').strip()
                                if not text:
                                    continue
                                m = date_regex.search(text)
                                if m:
                                    try:
                                        start_str = text.split('—')[0].strip()
                                        dt = datetime.strptime(start_str, '%b %d, %Y')
                                        return dt.date().isoformat()
                                    except Exception:
                                        continue
                        except Exception:
                            break
            except Exception:
                pass
        except Exception as e:
            print(f"Lỗi khi lấy ngày bắt đầu đăng: {str(e)}")
        return None
    
    def get_top_section_metrics(self):
        """Lấy các key metrics trong #top-section (Impressions, CTR, Views, Unique viewers, ...)"""
        top_metrics = {}
        print("  [DEBUG] Bắt đầu tìm top section metrics...")

        try:
            wait = WebDriverWait(self.driver, 15)
            # Tìm section chứa key metric card
            try:
                section = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '#top-section, [id="top-section"]'))
                )
                print("  [DEBUG] Tìm thấy #top-section element")
            except TimeoutException:
                print("  [DEBUG] Không tìm thấy #top-section element trong 15s")
                # Thử tìm các selector khác
                alternative_selectors = [
                    '[class*="top-section"]',
                    '[data-section="top"]',
                    'section[class*="analytics"]',
                    '.analytics-content [class*="metric"]'
                ]
                section = None
                for sel in alternative_selectors:
                    try:
                        candidates = self.driver.find_elements(By.CSS_SELECTOR, sel)
                        if candidates:
                            section = candidates[0]
                            print(f"  [DEBUG] Tìm thấy alternative section với selector: {sel}")
                            break
                    except Exception:
                        continue

                if not section:
                    print("  [DEBUG] Không tìm thấy top section với bất kỳ selector nào")
                    return top_metrics
            
            # Trong section này, tìm tất cả yta-key-metric-block
            # Đi qua các item để chắc chắn bắt đúng block
            blocks = section.find_elements(By.CSS_SELECTOR, 'yta-key-metric-block, [class*="yta-key-metric-block"]')
            print(f"  [DEBUG] Tìm thấy {len(blocks)} yta-key-metric-block elements")

            if not blocks:
                print("  [DEBUG] Không tìm thấy yta-key-metric-block, thử fallback selectors...")
                # Fallback: tìm theo listbox container
                listbox = section.find_elements(By.CSS_SELECTOR, '#key-metric-blocks, [id="key-metric-blocks"]')
                candidates = listbox[0] if listbox else section
                blocks = candidates.find_elements(By.CSS_SELECTOR, 'yta-key-metric-block, [class*="yta-key-metric-block"]')
                print(f"  [DEBUG] Fallback tìm thấy {len(blocks)} blocks")

                if not blocks:
                    print("  [DEBUG] Vẫn không tìm thấy blocks, thử các selector khác...")
                    # Thử các selector khác
                    alternative_block_selectors = [
                        '[class*="metric-card"]',
                        '[class*="key-metric"]',
                        '[data-testid*="metric"]',
                        '.metric-container',
                        '[class*="analytics-metric"]'
                    ]
                    for alt_sel in alternative_block_selectors:
                        try:
                            alt_blocks = section.find_elements(By.CSS_SELECTOR, alt_sel)
                            if alt_blocks:
                                blocks = alt_blocks
                                print(f"  [DEBUG] Tìm thấy {len(blocks)} blocks với alternative selector: {alt_sel}")
                                break
                        except Exception:
                            continue
            
            for block in blocks:
                try:
                    # Lấy label
                    label_elem = None
                    for sel in ['#metric-label', '[id="metric-label"]', '.metric-label', '[class*="metric-label"]']:
                        elems = block.find_elements(By.CSS_SELECTOR, sel)
                        if elems:
                            label_elem = elems[0]
                            break
                    if not label_elem:
                        # Fallback bằng text dòng đầu tiên
                        block_text = block.text.strip()
                        if block_text:
                            lines = [l.strip() for l in block_text.split('\n') if l.strip()]
                            if len(lines) >= 2:
                                label = lines[0]
                                value = lines[1]
                                if label and value:
                                    top_metrics[label] = value
                                    print(f"Top metric: {label} = {value}")
                        continue
                    label = label_elem.text.strip()
                    if not label:
                        continue
                    # Chuẩn hóa một số label
                    if label.lower() == 'impressions click-through rate':
                        label = 'Impressions click-through rate'
                    if label.lower() == 'unique viewers':
                        label = 'Unique viewers'
                    
                    # Lấy value từ #metric-total trong cùng block
                    value = None
                    for sel in ['#metric-total', '[id="metric-total"]', '.metric-total', '[class*="metric-total"]']:
                        total_elems = block.find_elements(By.CSS_SELECTOR, sel)
                        for te in total_elems:
                            te_text = te.text.strip()
                            if te_text and (any(ch.isdigit() for ch in te_text) or any(ch in te_text for ch in ['%', 'K', 'M', 'B', '.', ':'])):
                                value = te_text
                                break
                        if value:
                            break
                    
                    # Nếu chưa có, thử tìm các id pattern *-value
                    if not value:
                        for sel in ['[id$="-value"]', '[id*="value"]', '[class*="metric-value"]']:
                            val_elems = block.find_elements(By.CSS_SELECTOR, sel)
                            for ve in val_elems:
                                ve_text = ve.text.strip()
                                if ve_text and ve_text != label:
                                    if any(ch.isdigit() for ch in ve_text) or any(ch in ve_text for ch in ['%', 'K', 'M', 'B', '.', ':']):
                                        value = ve_text
                                        break
                            if value:
                                break
                    
                    if label and value:
                        top_metrics[label] = value
                        print(f"Top metric: {label} = {value}")
                except Exception as e:
                    print(f"Lỗi khi xử lý top metric block: {str(e)}")
                    continue

            # Bổ sung: nếu chưa có 'Views', lấy trực tiếp từ EXTERNAL_VIEWS-tab
            if 'Views' not in top_metrics:
                try:
                    views_tab = section.find_element(By.CSS_SELECTOR, '#EXTERNAL_VIEWS-tab, [id="EXTERNAL_VIEWS-tab"]')
                    # Tìm block bên trong tab này
                    views_block = None
                    for sel in ['yta-key-metric-block', '[class*="yta-key-metric-block"]']:
                        try:
                            cand = views_tab.find_element(By.CSS_SELECTOR, sel)
                            if cand:
                                views_block = cand
                                break
                        except:
                            continue
                    if views_block:
                        # Lấy metric-total
                        view_value = None
                        for sel in ['#metric-total', '[id="metric-total"]', '.metric-total', '[class*="metric-total"]']:
                            total_elems = views_block.find_elements(By.CSS_SELECTOR, sel)
                            for te in total_elems:
                                te_text = te.text.strip()
                                if te_text and (any(ch.isdigit() for ch in te_text) or any(ch in te_text for ch in ['%', 'K', 'M', 'B', '.', ':'])):
                                    view_value = te_text
                                    break
                            if view_value:
                                break
                        if view_value:
                            top_metrics['Views'] = view_value
                            print(f"Top metric (EXTERNAL_VIEWS-tab): Views = {view_value}")
                except Exception as e:
                    print(f"Không thể lấy Views từ EXTERNAL_VIEWS-tab: {str(e)}")
        except Exception as e:
            print(f"Lỗi khi lấy top section metrics: {str(e)}")
        
        return top_metrics
        
    def get_traffic_sources(self):
        """Lấy thông tin traffic sources"""
        traffic_data = {}
        print("  [DEBUG] Bắt đầu tìm traffic sources...")

        try:
            wait = WebDriverWait(self.driver, 15)

            # Các nguồn traffic có thể có (bao gồm cả Browse features)
            sources_list = [
                'Direct or unknown',
                'Channel pages',
                'YouTube search',
                'Other YouTube features',
                'Browse features',
                'External',
                'Suggested videos',
                'Playlists',
                'End screens',
                'Cards',
                'Notifications',
                'Subscriptions',
                'Others'
            ]

            try:
                # Tìm các title elements trong yta-table-card
                title_selectors = [
                    '[id^="title-text-"]',  # id="title-text-0", "title-text-1", etc.
                    '[class*="yta-table-card"] [class*="title-text"]',
                    '[class*="title-text"]',
                    'yta-table-card [class*="title"]'
                ]

                title_elements = []
                for selector in title_selectors:
                    try:
                        elements = wait.until(
                            EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                        )
                        if elements:
                            title_elements = elements
                            print(f"  [DEBUG] Tìm thấy {len(title_elements)} title elements với selector: {selector}")
                            break
                    except TimeoutException:
                        print(f"  [DEBUG] Selector '{selector}' timeout sau 15s")
                        continue

                # Nếu không tìm thấy với WebDriverWait, thử retry với scroll
                if not title_elements:
                    print("  [DEBUG] Không tìm thấy title elements ngay lập tức, thử retry với scroll...")
                    for selector in title_selectors:
                        title_elements = self.retry_find_elements_with_scroll(selector, max_retries=2, scroll_attempts=2)
                        if title_elements:
                            print(f"  [DEBUG] Tìm thấy {len(title_elements)} title elements với retry selector: {selector}")
                            break

                    # Nếu vẫn không tìm thấy, thử alternative selectors
                    if not title_elements:
                        print("  [DEBUG] Thử alternative selectors cho traffic sources...")
                        alt_traffic_selectors = [
                            '[class*="traffic-source"]',
                            '[class*="source-title"]',
                            '[data-testid*="traffic"]',
                            '.analytics-table [class*="title"]',
                            '[class*="how-viewers"] [class*="title"]'
                        ]
                        for alt_sel in alt_traffic_selectors:
                            title_elements = self.retry_find_elements_with_scroll(alt_sel, max_retries=2, scroll_attempts=1)
                            if title_elements:
                                print(f"  [DEBUG] Tìm thấy {len(title_elements)} title elements với alternative selector: {alt_sel}")
                                break
                
                # Xử lý từng title element để lấy source name và value
                for title_element in title_elements:
                    try:
                        source_name = title_element.text.strip()
                        if not source_name:
                            continue
                        
                        # Kiểm tra xem có phải là traffic source không
                        is_valid_source = False
                        for source in sources_list:
                            if source.lower() in source_name.lower() or source_name.lower() in source.lower():
                                is_valid_source = True
                                source_name = source  # Chuẩn hóa tên
                                break
                        
                        # Nếu không khớp với danh sách, vẫn thử lấy nếu có vẻ là traffic source
                        if not is_valid_source:
                            # Các từ khóa cho biết đây là traffic source
                            keywords = ['browse', 'direct', 'channel', 'search', 'external', 'suggested', 
                                      'playlist', 'card', 'notification', 'subscription', 'end screen', 
                                      'others', 'other']
                            if any(keyword in source_name.lower() for keyword in keywords):
                                is_valid_source = True
                        
                        if not is_valid_source:
                            continue
                        
                        # Tìm value tương ứng
                        value = None
                        
                        # Cách 1: Tìm trong cùng row/container
                        try:
                            # Tìm parent container
                            row = title_element
                            for _ in range(3):  # Tối đa 3 levels up
                                try:
                                    row = row.find_element(By.XPATH, './..')
                                    row_text = row.text.strip()
                                    
                                    # Tìm các số trong row text (có thể là view count, percentage, etc.)
                                    lines = [line.strip() for line in row_text.split('\n') if line.strip()]
                                    
                                    for i, line in enumerate(lines):
                                        if source_name.lower() in line.lower():
                                            # Tìm value ở các dòng tiếp theo
                                            for j in range(i + 1, min(i + 4, len(lines))):
                                                potential_value = lines[j]
                                                # Kiểm tra xem có phải là số không
                                                if potential_value and (any(char.isdigit() for char in potential_value) or '%' in potential_value):
                                                    # Bỏ qua nếu là tên source khác
                                                    if not any(s.lower() in potential_value.lower() for s in sources_list if s != source_name):
                                                        value = potential_value
                                                        break
                                            if value:
                                                break
                                    
                                    if value:
                                        break
                                except:
                                    continue
                        except:
                            pass
                        
                        # Cách 2: Tìm trong cùng table/card container
                        if not value:
                            try:
                                # Tìm yta-table-card container
                                card = title_element
                                for _ in range(5):
                                    try:
                                        card = card.find_element(By.XPATH, './..')
                                        if 'yta-table-card' in card.get_attribute('class') or 'table-card' in card.get_attribute('class'):
                                            break
                                    except:
                                        continue
                                
                                # Tìm các cells trong card
                                cells = card.find_elements(By.CSS_SELECTOR, '[class*="cell"], td, [role="cell"]')
                                for cell in cells:
                                    cell_text = cell.text.strip()
                                    if cell_text and cell_text != source_name:
                                        # Nếu có số hoặc %, có thể là value
                                        if any(char.isdigit() for char in cell_text) or '%' in cell_text:
                                            if not any(s.lower() in cell_text.lower() for s in sources_list if s != source_name):
                                                value = cell_text
                                                break
                            except:
                                pass
                        
                        # Cách 3: Text parsing từ toàn bộ section
                        if not value:
                            try:
                                # Tìm section chứa "How viewers find"
                                sections = self.driver.find_elements(By.CSS_SELECTOR, '[class*="table"], [class*="card"], section')
                                for section in sections:
                                    section_text = section.text.strip()
                                    if 'viewers find' in section_text.lower() or 'traffic' in section_text.lower():
                                        lines = [line.strip() for line in section_text.split('\n') if line.strip()]
                                        for i, line in enumerate(lines):
                                            if source_name.lower() in line.lower():
                                                # Tìm value ở dòng tiếp theo
                                                if i + 1 < len(lines):
                                                    potential_value = lines[i + 1]
                                                    if potential_value and (any(char.isdigit() for char in potential_value) or '%' in potential_value):
                                                        if potential_value != source_name:
                                                            value = potential_value
                                                            break
                                        if value:
                                            break
                            except:
                                pass
                        
                        if source_name and value:
                            traffic_data[source_name] = value
                            print(f"Tìm thấy: {source_name} = {value}")
                            
                    except Exception as e:
                        print(f"Lỗi khi xử lý traffic source element: {str(e)}")
                        continue
                
            except TimeoutException:
                print("Không tìm thấy title elements, thử phương pháp fallback...")
                
                # Fallback: Text parsing toàn bộ trang
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, 'body').text
                    lines = [line.strip() for line in page_text.split('\n') if line.strip()]
                    
                    for i, line in enumerate(lines):
                        for source in sources_list:
                            if source.lower() in line.lower() and source not in traffic_data:
                                # Tìm value ở dòng tiếp theo
                                if i + 1 < len(lines):
                                    value = lines[i + 1].strip()
                                    if value and value != source and (any(char.isdigit() for char in value) or '%' in value):
                                        traffic_data[source] = value
                                        print(f"Tìm thấy (fallback): {source} = {value}")
                                        break
                except Exception as e:
                    print(f"Lỗi khi dùng phương pháp fallback: {str(e)}")
                    
        except Exception as e:
            print(f"Lỗi khi lấy traffic sources: {str(e)}")
            import traceback
            traceback.print_exc()
            
        return traffic_data
        
    def get_impressions_data(self):
        """Lấy dữ liệu impressions"""
        impressions_data = {}
        print("  [DEBUG] Bắt đầu tìm impressions data...")

        try:
            # Đợi các metric blocks load
            wait = WebDriverWait(self.driver, 15)

            # Tìm tất cả các metric blocks với class yta-key-metric-block
            metric_blocks = self.retry_find_elements_with_scroll(
                'yta-key-metric-block, [class*="yta-key-metric-block"]',
                max_retries=3,
                scroll_attempts=2
            )

            if not metric_blocks:
                print("  [DEBUG] Vẫn không tìm thấy metric blocks, thử alternative selectors...")
                # Thử các alternative selectors
                alt_selectors = [
                    '[class*="metric-card"]',
                    '[class*="key-metric"]',
                    '[data-testid*="metric"]',
                    '.metric-container',
                    '[class*="analytics-metric"]'
                ]
                for alt_sel in alt_selectors:
                    metric_blocks = self.retry_find_elements_with_scroll(alt_sel, max_retries=2, scroll_attempts=1)
                    if metric_blocks:
                        print(f"  [DEBUG] Tìm thấy {len(metric_blocks)} metric blocks với alternative selector: {alt_sel}")
                        break

            if not metric_blocks:
                print("  [DEBUG] Không tìm thấy metric blocks với bất kỳ selector nào")
                return impressions_data

            for block in metric_blocks:
                    try:
                        # Tìm metric label trong block
                        label_elements = block.find_elements(By.CSS_SELECTOR, '#metric-label, [id="metric-label"], .metric-label, [class*="metric-label"]')
                        
                        if not label_elements:
                            # Thử lấy toàn bộ text của block và parse
                            block_text = block.text.strip()
                            if block_text:
                                lines = block_text.split('\n')
                                if len(lines) >= 2:
                                    label = lines[0].strip()
                                    value = lines[1].strip()
                                    if label and value:
                                        impressions_data[label] = value
                                        print(f"Tìm thấy: {label} = {value}")
                            continue
                        
                        # Lấy label từ element
                        label = label_elements[0].text.strip()
                        if not label:
                            continue
                        
                        # Chuẩn hóa tên label cho các metrics đặc biệt
                        # "Views" trong impressions section nên là "Views from impressions"
                        if label.lower() == 'views' and 'impressions' not in label.lower():
                            # Kiểm tra xem có phải là "Views from impressions" không bằng cách tìm views-title
                            try:
                                views_title_elements = self.driver.find_elements(By.CSS_SELECTOR, '#views-title, [id="views-title"]')
                                for views_title_elem in views_title_elements:
                                    views_title_text = views_title_elem.text.strip()
                                    if views_title_text and 'views from impressions' in views_title_text.lower():
                                        label = 'Views from impressions'
                                        break
                            except:
                                pass
                        
                        # Bỏ qua Unique viewers trong impressions_data (đã lấy ở top_metrics)
                        if label.lower() == 'unique viewers':
                            continue
                        
                        # Tìm value - có thể là sibling element hoặc trong cùng block
                        # Thử nhiều cách để lấy value
                        value = None
                        
                        # Ưu tiên: lấy từ container chuẩn metric-and-performance với #metric-total
                        try:
                            total_selectors = [
                                '#metric-and-performance-container #metric-total',
                                '[id="metric-and-performance-container"] [id="metric-total"]',
                                '[id="metric-total"], .metric-total, [class*="metric-total"]'
                            ]
                            for sel in total_selectors:
                                try:
                                    total_elems = block.find_elements(By.CSS_SELECTOR, sel)
                                    for te in total_elems:
                                        te_text = te.text.strip()
                                        if te_text and (any(ch.isdigit() for ch in te_text) or any(ch in te_text for ch in ['%', 'K', 'M', 'B', '.', ':'])):
                                            value = te_text
                                            break
                                    if value:
                                        print(f"  → Tìm value từ metric-total: {value}")
                                        break
                                except:
                                    continue
                        except:
                            pass

                        # Cách 0: Tìm element với id pattern *-value (ví dụ: impressions-value, views-value)
                        # Hoặc các container đặc biệt như average-watch-time
                        try:
                            # Tạo id pattern từ label (ví dụ: "Impressions" -> "impressions-value")
                            # Hoặc "Views from impressions" -> có thể là "views-value"
                            label_id_pattern = label.lower().replace(' ', '-').replace('_', '-')
                            
                            # Tạo các patterns từ từ khóa chính (lấy từ đầu label)
                            label_words = label.lower().split()
                            main_keywords = []
                            if label_words:
                                # Lấy từ đầu tiên làm keyword chính
                                main_keywords.append(label_words[0])
                                # Nếu có nhiều từ, thử kết hợp từ đầu tiên và từ cuối
                                if len(label_words) > 1:
                                    main_keywords.append(f"{label_words[0]}-{label_words[-1]}")
                            
                            # Tìm các container đặc biệt (ví dụ: average-watch-time cho "Average view duration")
                            special_containers = []
                            watch_time_container = None
                            
                            if 'average' in label.lower() and 'duration' in label.lower():
                                special_containers.append('[id="average-watch-time"]')
                                special_containers.append('[id*="average-watch-time"]')
                                special_containers.append('[id*="watch-time"]')
                            
                            # Xử lý đặc biệt cho "Watch time from impressions"
                            if 'watch time' in label.lower() and 'impressions' in label.lower():
                                try:
                                    # Tìm watch-time-container hoặc watch-time-title
                                    watch_time_selectors = [
                                        '[id="watch-time-title"]',
                                        '[class*="watch-time-container"]',
                                        '[id*="watch-time-title"]'
                                    ]
                                    for selector in watch_time_selectors:
                                        try:
                                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                            for elem in elements:
                                                # Kiểm tra xem element này có chứa label không
                                                if label.lower() in elem.text.lower():
                                                    watch_time_container = elem
                                                    # Tìm parent container (watch-time-container)
                                                    for _ in range(3):
                                                        try:
                                                            parent = watch_time_container.find_element(By.XPATH, './..')
                                                            if 'watch-time-container' in parent.get_attribute('class') or parent.get_attribute('id') == 'watch-time-container':
                                                                watch_time_container = parent
                                                                break
                                                            watch_time_container = parent
                                                        except:
                                                            break
                                                    break
                                            if watch_time_container:
                                                break
                                        except:
                                            continue
                                    
                                    # Nếu tìm thấy container, tìm value element trong đó
                                    if watch_time_container:
                                        try:
                                            # Tìm wt-value trong container
                                            wt_value_elem = watch_time_container.find_element(By.CSS_SELECTOR, '[id="wt-value"], [id*="wt-value"]')
                                            wt_value_text = wt_value_elem.text.strip()
                                            if wt_value_text and (any(char.isdigit() for char in wt_value_text) or any(char in wt_value_text for char in ['K', 'M', 'B', '.'])):
                                                value = wt_value_text
                                                print(f"  → Tìm value từ watch-time-container: {value}")
                                        except:
                                            pass
                                except:
                                    pass
                            
                            # Tìm element với id chứa pattern này
                            value_id_patterns = []
                            # Thêm special containers trước
                            value_id_patterns.extend(special_containers)
                            
                            # Thêm pattern đặc biệt cho "Views from impressions"
                            if 'views' in label.lower() and 'impressions' in label.lower() and not value:
                                value_id_patterns.insert(0, '[id="views-value"]')  # Ưu tiên cao nhất
                                value_id_patterns.insert(1, '[id*="views-value"]')
                            
                            # Thêm pattern đặc biệt cho "Unique viewers"
                            if 'unique viewers' in label.lower() and not value:
                                value_id_patterns.insert(0, '[id="unique-viewers-value"]')  # Ưu tiên cao nhất
                                value_id_patterns.insert(1, '[id*="unique-viewers-value"]')
                                value_id_patterns.insert(2, '[id*="unique-value"]')
                            
                            # Thêm pattern đặc biệt cho watch time
                            if 'watch time' in label.lower() and 'impressions' in label.lower() and not value:
                                value_id_patterns.insert(0, '[id="wt-value"]')  # Ưu tiên cao nhất
                                value_id_patterns.insert(1, '[id*="wt-value"]')
                            
                            # Thêm pattern từ từ khóa chính trước (ưu tiên)
                            for keyword in main_keywords:
                                keyword_clean = keyword.replace(' ', '-').replace('_', '-')
                                value_id_patterns.append(f'[id="{keyword_clean}-value"]')
                                value_id_patterns.append(f'[id*="{keyword_clean}-value"]')
                            
                            # Thêm pattern từ toàn bộ label
                            value_id_patterns.extend([
                                f'[id="{label_id_pattern}-value"]',
                                f'[id*="{label_id_pattern}-value"]',
                                f'[id*="-value"]',
                                '[id$="-value"]'
                            ])
                            
                            for pattern in value_id_patterns:
                                try:
                                    value_elements = block.find_elements(By.CSS_SELECTOR, pattern)
                                    if not value_elements:
                                        # Thử tìm trong parent hoặc document
                                        value_elements = self.driver.find_elements(By.CSS_SELECTOR, pattern)
                                    
                                    for ve in value_elements:
                                        ve_text = ve.text.strip()
                                        
                                        # Xử lý trường hợp đặc biệt: value và label cùng một dòng (ví dụ: "19:05 average view duration")
                                        if label.lower() in ve_text.lower():
                                            # Tách text để lấy value (thường là phần đầu có số hoặc thời gian)
                                            parts = ve_text.split()
                                            for i, part in enumerate(parts):
                                                # Nếu part có định dạng thời gian (ví dụ: 19:05) hoặc số
                                                if ':' in part or (any(char.isdigit() for char in part) and any(char in part for char in [':', '.', '%', 'K', 'M', 'B'])):
                                                    # Lấy phần trước label làm value
                                                    potential_value = ' '.join(parts[:i+1])
                                                    if potential_value and potential_value.strip():
                                                        value = potential_value.strip()
                                                        print(f"  → Tìm value từ container text (value trước label): {value}")
                                                        break
                                            if value:
                                                break
                                        
                                        # Nếu không phải trường hợp đặc biệt, xử lý như bình thường
                                        if not value:
                                            # Nếu có số, %, K, M, B thì đây có thể là value
                                            if ve_text and (any(char.isdigit() for char in ve_text) or any(char in ve_text for char in ['%', 'K', 'M', 'B', '.', ':'])):
                                                if ve_text != label and label.lower() not in ve_text.lower():
                                                    value = ve_text
                                                    print(f"  → Tìm value từ id pattern {pattern}: {value}")
                                                    break
                                    
                                    if value:
                                        break
                                except:
                                    continue
                        except:
                            pass
                        
                        # Cách 1: Tìm tất cả yt-formatted-string trong block (YouTube Studio thường dùng)
                        try:
                            formatted_strings = block.find_elements(By.CSS_SELECTOR, 'yt-formatted-string')
                            # Bỏ qua label element, lấy các element khác
                            for fs in formatted_strings:
                                fs_text = fs.text.strip()
                                # Bỏ qua nếu là label hoặc empty
                                if fs_text and fs_text != label and label.lower() not in fs_text.lower():
                                    # Nếu có số hoặc % thì đây có thể là value
                                    if any(char.isdigit() for char in fs_text) or '%' in fs_text:
                                        value = fs_text
                                        break
                            if value:
                                print(f"  → Tìm value từ yt-formatted-string: {value}")
                        except:
                            pass
                        
                        # Cách 2: Tìm element chứa value với các selector phổ biến
                        if not value:
                            value_selectors = [
                                '[class*="metric-value"]',  # Ưu tiên metric-value
                                '[id*="value"]',
                                '[id*="-value"]',
                                '[class*="metric-number"]',
                                '[class*="value"]',
                                '[class*="number"]',
                                'span[class*="metric"]',
                                'div[class*="metric-value"]',
                                'div[class*="metric-number"]',
                                'div[id*="value"]'
                            ]
                            
                            for selector in value_selectors:
                                try:
                                    value_elements = block.find_elements(By.CSS_SELECTOR, selector)
                                    for ve in value_elements:
                                        ve_text = ve.text.strip()
                                        # Bỏ qua nếu là label
                                        if ve_text and ve_text != label and label.lower() not in ve_text.lower():
                                            value = ve_text
                                            break
                                    if value:
                                        print(f"  → Tìm value từ selector {selector}: {value}")
                                        break
                                except:
                                    continue
                        
                        # Cách 3: Lấy text của block và parse (label thường là dòng đầu, value là dòng tiếp theo)
                        if not value:
                            try:
                                block_text = block.text.strip()
                                lines = [line.strip() for line in block_text.split('\n') if line.strip()]
                                
                                # Tìm dòng chứa label
                                label_line_index = -1
                                for i, line in enumerate(lines):
                                    if label.lower() in line.lower():
                                        label_line_index = i
                                        break
                                
                                # Lấy dòng tiếp theo làm value (nếu không phải label)
                                if label_line_index >= 0 and label_line_index + 1 < len(lines):
                                    potential_value = lines[label_line_index + 1]
                                    # Kiểm tra xem có phải là value không (có số hoặc %)
                                    if potential_value and (any(char.isdigit() for char in potential_value) or '%' in potential_value):
                                        if potential_value != label:
                                            value = potential_value
                                            print(f"  → Tìm value từ text parsing: {value}")
                            except:
                                pass
                        
                        # Cách 4: Tìm trong parent container
                        if not value:
                            try:
                                parent = block.find_element(By.XPATH, './..')
                                parent_text = parent.text.strip()
                                lines = [line.strip() for line in parent_text.split('\n') if line.strip()]
                                
                                for i, line in enumerate(lines):
                                    if label.lower() in line.lower() and i + 1 < len(lines):
                                        potential_value = lines[i + 1]
                                        if potential_value and potential_value != label:
                                            # Kiểm tra xem có phải là value không
                                            if any(char.isdigit() for char in potential_value) or '%' in potential_value:
                                                value = potential_value
                                                print(f"  → Tìm value từ parent: {value}")
                                                break
                            except:
                                pass
                        
                        if label and value:
                            impressions_data[label] = value
                            print(f"Tìm thấy: {label} = {value}")
                            
                    except Exception as e:
                        print(f"Lỗi khi xử lý metric block: {str(e)}")
                        continue

            # Fallback: Nếu không tìm thấy metric blocks, thử text parsing
            if not metric_blocks:
                print("Không tìm thấy metric blocks với selector chính xác, thử selector dự phòng...")

                try:
                    all_text = self.driver.find_element(By.TAG_NAME, 'body').text
                    lines = all_text.split('\n')
                    
                    # Tìm các metrics trong text
                    metrics_to_find = [
                        'Impressions',
                        'Impressions click-through rate',
                        'Click-through rate',
                        'CTR',
                        'Views from impressions',
                        'Average view duration',
                        'Watch time from impressions',
                        'Views'
                    ]
                    
                    for i, line in enumerate(lines):
                        for metric in metrics_to_find:
                            if metric.lower() in line.lower() and metric not in impressions_data:
                                # Tìm value ở dòng tiếp theo
                                if i + 1 < len(lines):
                                    value = lines[i + 1].strip()
                                    if value and value != metric:
                                        impressions_data[metric] = value
                                        print(f"Tìm thấy (fallback): {metric} = {value}")
                                        break
                                        
                except Exception as e:
                    print(f"Lỗi khi dùng phương pháp fallback: {str(e)}")
                    
        except Exception as e:
            print(f"Lỗi khi lấy impressions data: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Thêm 3 phần dữ liệu đặc biệt từ yta-funnel
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # 1. Lấy "from YouTube recommending your content" từ discovery-title
            try:
                discovery_elements = self.driver.find_elements(By.CSS_SELECTOR, '#discovery-title, [id="discovery-title"]')
                for elem in discovery_elements:
                    discovery_text = elem.text.strip()
                    if discovery_text and ('recommending' in discovery_text.lower() or '%' in discovery_text):
                        impressions_data['YouTube recommending your content'] = discovery_text
                        print(f"Tìm thấy: YouTube recommending your content = {discovery_text}")
                        break
            except Exception as e:
                print(f"Không tìm thấy discovery-title: {str(e)}")
            
            # 2. Lấy "click-through rate" từ ctr-title
            try:
                ctr_elements = self.driver.find_elements(By.CSS_SELECTOR, '#ctr-title, [id="ctr-title"]')
                for elem in ctr_elements:
                    ctr_text = elem.text.strip()
                    if ctr_text and ('click-through rate' in ctr_text.lower() or '%' in ctr_text):
                        # Extract phần trăm từ text (ví dụ: "5.9% click-through rate" -> "5.9%")
                        if '%' in ctr_text:
                            # Tìm phần số và % đầu tiên
                            match = re.search(r'[\d.]+%', ctr_text)
                            if match:
                                impressions_data['Click-through rate (from impressions)'] = match.group()
                                print(f"Tìm thấy: Click-through rate (from impressions) = {match.group()}")
                            else:
                                impressions_data['Click-through rate (from impressions)'] = ctr_text
                                print(f"Tìm thấy: Click-through rate (from impressions) = {ctr_text}")
                        else:
                            impressions_data['Click-through rate (from impressions)'] = ctr_text
                            print(f"Tìm thấy: Click-through rate (from impressions) = {ctr_text}")
                        break
            except Exception as e:
                print(f"Không tìm thấy ctr-title: {str(e)}")
            
            # 3. Lấy "average view duration" từ div với class paddingten (nếu chưa có)
            try:
                # Tìm tất cả các div với class paddingten chứa "average view duration"
                avg_duration_elements = self.driver.find_elements(By.CSS_SELECTOR, '[class*="paddingten"][class*="yta-funnel"]')
                for elem in avg_duration_elements:
                    elem_text = elem.text.strip()
                    if elem_text and 'average view duration' in elem_text.lower():
                        # Extract thời gian từ text (ví dụ: "19:05 average view duration" -> "19:05")
                        if ':' in elem_text:
                            # Tìm phần thời gian (format MM:SS hoặc HH:MM:SS)
                            time_match = re.search(r'\d{1,2}:\d{2}(?::\d{2})?', elem_text)
                            if time_match:
                                duration_value = time_match.group()
                                # Kiểm tra xem đã có key này chưa, nếu chưa hoặc giá trị khác thì thêm/update
                                if 'Average view duration (from impressions)' not in impressions_data:
                                    impressions_data['Average view duration (from impressions)'] = duration_value
                                    print(f"Tìm thấy: Average view duration (from impressions) = {duration_value}")
                                break
            except Exception as e:
                print(f"Không tìm thấy average view duration từ paddingten: {str(e)}")
            
            # 4. Lấy "Watch time from impressions (hours)" từ watch-time-title và wt-value
            try:
                # Tìm watch-time-title element
                watch_time_title_elements = self.driver.find_elements(By.CSS_SELECTOR, '#watch-time-title, [id="watch-time-title"]')
                for title_elem in watch_time_title_elements:
                    title_text = title_elem.text.strip()
                    if title_text and 'watch time' in title_text.lower() and 'impressions' in title_text.lower():
                        # Tìm wt-value trong cùng container
                        value = None
                        try:
                            # Tìm parent container (watch-time-container hoặc watch-time)
                            container = title_elem
                            for _ in range(5):
                                try:
                                    container = container.find_element(By.XPATH, './..')
                                    container_class = container.get_attribute('class') or ''
                                    container_id = container.get_attribute('id') or ''
                                    if 'watch-time-container' in container_class or 'watch-time' in container_id or 'watch-time-container' in container_id:
                                        break
                                except:
                                    break
                            
                            # Tìm wt-value trong container
                            wt_value_elements = container.find_elements(By.CSS_SELECTOR, '#wt-value, [id="wt-value"]')
                            if not wt_value_elements:
                                # Thử tìm trong document nếu không tìm thấy trong container
                                wt_value_elements = self.driver.find_elements(By.CSS_SELECTOR, '#wt-value, [id="wt-value"]')
                            
                            for wt_elem in wt_value_elements:
                                wt_text = wt_elem.text.strip()
                                if wt_text and (any(char.isdigit() for char in wt_text) or any(char in wt_text for char in ['K', 'M', 'B', '.'])):
                                    value = wt_text
                                    break
                        except Exception as e:
                            print(f"Lỗi khi tìm wt-value: {str(e)}")
                        
                        if value:
                            impressions_data['Watch time from impressions (hours)'] = value
                            print(f"Tìm thấy: Watch time from impressions (hours) = {value}")
                        break
            except Exception as e:
                print(f"Không tìm thấy watch time from impressions: {str(e)}")
                
        except Exception as e:
            print(f"Lỗi khi lấy thêm dữ liệu impressions: {str(e)}")
            
        return impressions_data
        
    def scrape_multiple_videos(self, video_ids, video_account_mapping=None, headless=False):
        """Lấy analytics của nhiều videos
        
        Args:
            video_ids: Danh sách video IDs cần scrape
            video_account_mapping: Dict mapping video_id -> account_name (tùy chọn)
                                  Nếu có, sẽ tự động chuyển đổi tài khoản khi cần
            headless: Chế độ headless (để tự động đăng nhập lại nếu cần)
        
        Returns:
            list: Danh sách kết quả analytics
        """
        results = []
        current_account = self.account_name  # Theo dõi tài khoản hiện tại
        
        for video_id in video_ids:
            print(f"\n{'='*50}")
            print(f"Đang xử lý video: {video_id}")
            print(f"{'='*50}")
            
            # Kiểm tra xem video này cần tài khoản khác không
            if video_account_mapping and video_id in video_account_mapping:
                required_account = video_account_mapping[video_id]
                
                # Nếu tài khoản hiện tại khác với tài khoản cần thiết, chuyển đổi
                if required_account != current_account:
                    print(f"Video này cần tài khoản: {required_account}")
                    if self.switch_account(account_name=required_account):
                        current_account = required_account
                    else:
                        print(f"⚠ Không thể chuyển đổi sang tài khoản {required_account}. Tiếp tục với tài khoản hiện tại.")
            
            data = self.get_video_analytics(video_id, headless=headless)
            results.append(data)
            
            # Nghỉ giữa các requests
            time.sleep(3)
            
        return results
    
    def scrape_multiple_videos_parallel(self, video_ids, video_account_mapping=None, max_workers=None, headless=False, auto_continue=False, wait_time=30):
        """Lấy analytics của nhiều videos song song (đa luồng)

        Mỗi thread có driver riêng và cookies riêng, không bị lộn cookie.

        Args:
            video_ids: Danh sách video IDs cần scrape
            video_account_mapping: Dict mapping video_id -> account_name (bắt buộc khi dùng parallel)
                                  Mỗi video sẽ được scrape bởi thread với account tương ứng
            max_workers: Số thread tối đa (mặc định: số lượng account unique)
            headless: Chạy browser ở chế độ headless
            auto_continue: Tự động tiếp tục đăng nhập
            wait_time: Thời gian chờ trước khi tự động tiếp tục

        Returns:
            list: Danh sách kết quả analytics (có thể không theo thứ tự)
        """
        if not video_account_mapping:
            thread_safe_print("⚠ Cảnh báo: video_account_mapping là bắt buộc khi dùng parallel mode.")
            thread_safe_print("   Chuyển sang chế độ tuần tự...")
            return self.scrape_multiple_videos(video_ids, video_account_mapping)
        
        # Nhóm video theo account
        account_videos = {}
        for video_id in video_ids:
            account = video_account_mapping.get(video_id, self.account_name)
            if account not in account_videos:
                account_videos[account] = []
            account_videos[account].append(video_id)
        
        thread_safe_print(f"\n{'='*50}")
        thread_safe_print("CHẠY ĐA LUỒNG - PHÂN PHỐI VIDEO:")
        thread_safe_print(f"{'='*50}")
        for account, vids in account_videos.items():
            thread_safe_print(f"  Tài khoản '{account}': {len(vids)} video(s)")
        thread_safe_print(f"{'='*50}\n")
        
        # Xác định số worker
        if max_workers is None:
            max_workers = len(account_videos)
        max_workers = min(max_workers, len(account_videos), len(video_ids))
        
        thread_safe_print(f"Sử dụng {max_workers} thread(s) để scrape {len(video_ids)} video(s)\n")
        
        results = []
        results_lock = Lock()  # Lock để thread-safe khi append results
        
        def scrape_video_with_account(video_id, account_name, auto_continue_param, wait_time_param):
            """Helper function để scrape một video với một account cụ thể (thread-safe)"""
            thread_id = f"[Thread-{account_name}]"
            try:
                thread_safe_print(f"{thread_id} Đang khởi tạo scraper cho video: {video_id}")

                # Tạo scraper mới cho thread này (mỗi thread có driver riêng)
                scraper = YouTubeAnalyticsScraper(account_name=account_name, auto_continue=auto_continue_param, wait_time=wait_time_param)
                scraper.init_driver(headless=headless)
                
                # Load cookies
                if not scraper.load_cookies(headless=headless):
                    thread_safe_print(f"{thread_id} ⚠ Không thể load cookies cho {account_name}. Bỏ qua video {video_id}")
                    scraper.close()
                    return {'video_id': video_id, 'error': f'Không thể load cookies cho {account_name}'}
                
                thread_safe_print(f"{thread_id} Đang scrape video: {video_id}")
                
                # Scrape video
                data = scraper.get_video_analytics(video_id, headless=headless)
                
                # Đóng driver
                scraper.close()
                
                thread_safe_print(f"{thread_id} ✓ Hoàn thành video: {video_id}")
                return data
                
            except Exception as e:
                thread_safe_print(f"{thread_id} ✗ Lỗi khi scrape video {video_id}: {str(e)}")
                import traceback
                thread_safe_print(f"{thread_id} Traceback: {traceback.format_exc()}")
                return {'video_id': video_id, 'error': str(e)}
        
        # Chạy song song với ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tất cả tasks
            future_to_video = {}
            for video_id in video_ids:
                account = video_account_mapping.get(video_id, self.account_name)
                future = executor.submit(scrape_video_with_account, video_id, account, auto_continue, wait_time)
                future_to_video[future] = video_id
            
            # Thu thập kết quả khi hoàn thành
            completed = 0
            for future in as_completed(future_to_video):
                video_id = future_to_video[future]
                try:
                    result = future.result()
                    with results_lock:
                        results.append(result)
                    completed += 1
                    thread_safe_print(f"\n[{completed}/{len(video_ids)}] Đã hoàn thành video: {video_id}")
                except Exception as e:
                    thread_safe_print(f"✗ Exception khi xử lý video {video_id}: {str(e)}")
                    with results_lock:
                        results.append({'video_id': video_id, 'error': str(e)})
        
        thread_safe_print(f"\n{'='*50}")
        thread_safe_print(f"HOÀN THÀNH: Đã scrape {len(results)}/{len(video_ids)} video(s)")
        thread_safe_print(f"{'='*50}\n")
        
        return results
        
    def save_results(self, results, output_file='analytics_results.json'):
        """Lưu kết quả ra file JSON (merge với dữ liệu cũ, tránh trùng lặp video_id)"""
        # Đọc dữ liệu cũ nếu có
        existing_results = []
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_results = json.load(f)
                    if not isinstance(existing_results, list):
                        existing_results = []
            except Exception as e:
                print(f"⚠ Lỗi khi đọc file cũ {output_file}: {str(e)}")
                existing_results = []
        
        # Tạo dict để dễ dàng kiểm tra và cập nhật
        results_dict = {}
        for result in existing_results:
            video_id = result.get('video_id')
            if video_id:
                results_dict[video_id] = result
        
        # Merge với kết quả mới (ghi đè nếu video_id đã tồn tại)
        new_count = 0
        updated_count = 0
        for result in results:
            video_id = result.get('video_id')
            if video_id:
                if video_id in results_dict:
                    # Cập nhật kết quả cũ
                    results_dict[video_id] = result
                    updated_count += 1
                else:
                    # Thêm mới
                    results_dict[video_id] = result
                    new_count += 1
        
        # Chuyển lại thành list và sắp xếp theo video_id
        final_results = list(results_dict.values())
        final_results.sort(key=lambda x: x.get('video_id', ''))
        
        # Lưu lại
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, ensure_ascii=False, indent=2)
        
        print(f"\nĐã lưu kết quả vào {output_file}")
        print(f"  - Video IDs mới: {new_count}")
        print(f"  - Video IDs cập nhật: {updated_count}")
        print(f"  - Tổng số video IDs trong file: {len(final_results)}")
        
    def close(self):
        """Đóng browser"""
        if self.driver:
            self.driver.quit()


def update_accounts_list(account_name, cookies_file):
    """Cập nhật danh sách tài khoản trong config.json"""
    config_file = 'config.json'
    config_data = {'accounts': []}

    # Đọc config hiện tại
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except:
            pass

    # Đảm bảo có key 'accounts'
    if 'accounts' not in config_data:
        config_data['accounts'] = []

    # Kiểm tra xem tài khoản đã tồn tại chưa
    account_exists = False
    for acc in config_data['accounts']:
        if acc.get('name') == account_name:
            # Cập nhật thông tin
            acc['cookies_file'] = cookies_file
            account_exists = True
            break

    # Nếu chưa tồn tại, thêm mới
    if not account_exists:
        config_data['accounts'].append({
            'name': account_name,
            'cookies_file': cookies_file,
            'channels': []  # Khởi tạo danh sách channels rỗng
        })

    # Lưu lại config.json
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)

    print(f"Đã cập nhật danh sách tài khoản trong config.json: {account_name}")

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Cào dữ liệu analytics từ YouTube Studio',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python craw.py --account-name "1"
  python craw.py --account-name "1" --headless
  python craw.py --account-name "1" --parallel
  python craw.py --account-name "1" --parallel --max-workers 3
        """
    )
    parser.add_argument(
        '--account-name',
        type=str,
        required=True,
        help='Tên tài khoản để chạy (BẮT BUỘC - sẽ lấy cookies_file và channels từ account này trong config.json)'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Chạy browser ở chế độ headless (không hiển thị cửa sổ)'
    )
    parser.add_argument(
        '--auto-continue',
        action='store_true',
        help='Tự động tiếp tục sau khi đăng nhập Google mà không cần nhấn Enter (chờ 30 giây)'
    )
    parser.add_argument(
        '--wait-time',
        type=int,
        default=30,
        help='Thời gian chờ trước khi tự động tiếp tục (giây) - dùng với --auto-continue'
    )
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Cào nhiều channels song song (mỗi channel trong một thread riêng)'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        default=None,
        help='Số thread tối đa khi dùng --parallel (mặc định: số lượng channels)'
    )
    
    args = parser.parse_args()
    
    # Đọc cấu hình từ config.json
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Không tìm thấy file config.json. Sử dụng cấu hình mặc định.")
        config = {}
    except Exception as e:
        print(f"Lỗi khi đọc config.json: {str(e)}")
        return
    
    # Nếu có --account-name, tìm account trong config
    if args.account_name:
        accounts = config.get('accounts', [])
        target_account = None
        
        # Tìm account theo tên
        for acc in accounts:
            if acc.get('name') == args.account_name:
                target_account = acc
                break
        
        if not target_account:
            print(f"\n{'='*50}")
            print(f"LỖI: Không tìm thấy account '{args.account_name}' trong config.json")
            print(f"{'='*50}")
            print("\nDanh sách accounts có sẵn:")
            for acc in accounts:
                channels_count = len(acc.get('channels', []))
                total_videos = sum(len(ch.get('video_ids', [])) for ch in acc.get('channels', []))
                print(f"  - {acc.get('name', 'Unknown')} (Channels: {channels_count}, Videos: {total_videos})")
            print("="*50)
            return
        
        # Lấy thông tin từ account
        account_name = target_account.get('name')
        cookies_file = target_account.get('cookies_file')
        # Chuẩn hóa path (xử lý cả Windows và Unix paths)
        if cookies_file:
            cookies_file = os.path.normpath(cookies_file).replace('\\', '/')
        account_channels = target_account.get('channels', [])
        
        if not account_channels:
            print(f"\n{'='*50}")
            print(f"⚠ Cảnh báo: Account '{account_name}' không có channels nào")
            print(f"{'='*50}")
            return
        
        print(f"\n{'='*50}")
        print(f"ACCOUNT: {account_name}")
        print(f"{'='*50}")
        print(f"Cookies file: {cookies_file}")
        print(f"Số lượng channels: {len(account_channels)}")
        total_videos = sum(len(ch.get('video_ids', [])) for ch in account_channels)
        print(f"Tổng số video IDs: {total_videos}")
        print(f"{'='*50}\n")
        
        # Lấy các giá trị từ config hoặc args
        headless = args.headless or config.get('headless', False)
        auto_continue = args.auto_continue or config.get('auto_continue', False)
        wait_time = args.wait_time or config.get('wait_time', 30)
        use_parallel = args.parallel or config.get('parallel', False)
        max_workers = args.max_workers or config.get('max_workers', None)
        
        # Nếu có nhiều channels và bật parallel, dùng chế độ song song
        if use_parallel and len(account_channels) > 1:
            print(f"\n{'='*50}")
            print("CHẾ ĐỘ: PARALLEL (Cào nhiều channels song song)")
            print(f"{'='*50}\n")
            process_channels_parallel(
                account_channels=account_channels,
                cookies_file=cookies_file,
                account_name=account_name,
                headless=headless,
                max_workers=max_workers,
                auto_continue=auto_continue,
                wait_time=wait_time
            )
        else:
            # Chế độ tuần tự (sequential)
            if use_parallel and len(account_channels) <= 1:
                print(f"\n⚠ Cảnh báo: Chỉ có {len(account_channels)} channel(s), không cần dùng parallel mode.")
                print("   Chuyển sang chế độ tuần tự.\n")
            
            # Xử lý từng channel của account này
            for idx, channel in enumerate(account_channels, 1):
                channel_url = channel.get('url', '')
                video_ids = channel.get('video_ids', [])
                channel_output_file = channel.get('output_file', None)
                
                if not video_ids:
                    print(f"\nChannel {idx}: {channel_url}")
                    print("  ⚠ Không có video IDs, bỏ qua channel này.")
                    continue
                
                print(f"\n{'='*60}")
                print(f"CHANNEL {idx}/{len(account_channels)}: {channel_url}")
                print(f"{'='*60}")
                print(f"  - Video IDs: {len(video_ids)} video(s)")
                if channel_output_file:
                    print(f"  - Output file: {channel_output_file}")
                print(f"{'='*60}\n")
                
                # Xử lý channel này - chỉ cào dữ liệu
                process_channel(
                    channel_url=channel_url,
                    video_ids=video_ids,
                    cookies_file=cookies_file,  # Dùng cookies_file từ account
                    output_file=channel_output_file,
                    account_name=account_name,  # Dùng account_name từ account
                    headless=headless,
                    auto_continue=auto_continue,
                    wait_time=wait_time
                )
        
        return
    
    # Nếu không có --account-name, báo lỗi và yêu cầu chỉ định
    print(f"\n{'='*50}")
    print("LỖI: Thiếu argument --account-name")
    print(f"{'='*50}")
    print("\nVui lòng chỉ định tên tài khoản để chạy:")
    print("  python craw.py --account-name \"1\"")
    print("\nDanh sách accounts có sẵn trong config.json:")
    accounts = config.get('accounts', [])
    if accounts:
        for acc in accounts:
            channels_count = len(acc.get('channels', []))
            total_videos = sum(len(ch.get('video_ids', [])) for ch in acc.get('channels', []))
            print(f"  - {acc.get('name', 'Unknown')} (Channels: {channels_count}, Videos: {total_videos})")
    else:
        print("  (Chưa có account nào)")
    print("="*50)
    return


def process_channels_parallel(account_channels=None, cookies_file=None, account_name=None,
                              headless=False, max_workers=None, auto_continue=False, wait_time=30):
    """
    Cào dữ liệu analytics từ YouTube Studio cho nhiều channels song song

    Mỗi channel sẽ được xử lý trong một thread riêng với driver riêng.

    Args:
        account_channels: Danh sách channels từ account
        cookies_file: Đường dẫn file cookies
        account_name: Tên tài khoản
        headless: Chạy browser ở chế độ headless
        max_workers: Số thread tối đa (mặc định: số lượng channels)
        auto_continue: Tự động tiếp tục đăng nhập
        wait_time: Thời gian chờ trước khi tự động tiếp tục
    """
    if not account_channels:
        print("Không có channels để xử lý!")
        return
    
    # Lọc các channels có video_ids
    valid_channels = []
    for channel in account_channels:
        video_ids = channel.get('video_ids', [])
        if video_ids:
            valid_channels.append(channel)
        else:
            channel_url = channel.get('url', '')
            thread_safe_print(f"⚠ Channel {channel_url}: Không có video IDs, bỏ qua.")
    
    if not valid_channels:
        print("Không có channel nào có video IDs để xử lý!")
        return
    
    # Xác định số worker
    if max_workers is None:
        max_workers = len(valid_channels)
    max_workers = min(max_workers, len(valid_channels))
    
    thread_safe_print(f"\n{'='*60}")
    thread_safe_print("CHẠY PARALLEL - PHÂN PHỐI CHANNELS:")
    thread_safe_print(f"{'='*60}")
    for idx, channel in enumerate(valid_channels, 1):
        channel_url = channel.get('url', '')
        video_ids = channel.get('video_ids', [])
        thread_safe_print(f"  Channel {idx}: {channel_url} ({len(video_ids)} video(s))")
    thread_safe_print(f"{'='*60}")
    thread_safe_print(f"Sử dụng {max_workers} thread(s) để xử lý {len(valid_channels)} channel(s)\n")
    
    results_lock = Lock()  # Lock để thread-safe khi ghi kết quả
    completed_channels = []  # Danh sách channels đã hoàn thành
    
    def process_single_channel(channel, channel_idx, total_channels, auto_continue_param, wait_time_param):
        """Helper function để xử lý một channel trong thread riêng"""
        thread_id = f"[Thread-Channel-{channel_idx}]"
        channel_url = channel.get('url', '')
        video_ids = channel.get('video_ids', [])
        channel_output_file = channel.get('output_file', None)

        try:
            thread_safe_print(f"\n{thread_id} Bắt đầu xử lý channel: {channel_url}")
            thread_safe_print(f"{thread_id} Số lượng video: {len(video_ids)}")

            # Gọi process_channel với driver riêng
            # Tạo scraper riêng cho thread này
            scraper = YouTubeAnalyticsScraper(cookies_file=cookies_file, account_name=account_name, auto_continue=auto_continue_param, wait_time=wait_time_param)
            scraper.init_driver(headless=headless)
            
            try:
                # Load cookies
                if not scraper.load_cookies(headless=headless):
                    thread_safe_print(f"{thread_id} ⚠ Không thể load cookies. Bỏ qua channel {channel_url}")
                    scraper.close()
                    return {
                        'channel_url': channel_url,
                        'status': 'error',
                        'error': 'Không thể load cookies'
                    }
                
                # Lấy analytics cho tất cả videos trong channel
                results = scraper.scrape_multiple_videos(video_ids, headless=headless)
                
                # Lưu kết quả với output_file riêng hoặc mặc định
                if not channel_output_file:
                    # Tạo tên file dựa trên channel URL và index để tránh trùng
                    safe_channel_name = re.sub(r'[^\w\-_]', '_', channel_url.split('/')[-1])
                    channel_output_file = f'analytics_results_{safe_channel_name}_{channel_idx}.json'
                
                # Lưu kết quả (thread-safe)
                with results_lock:
                    scraper.save_results(results, output_file=channel_output_file)
                    completed_channels.append({
                        'channel_url': channel_url,
                        'video_count': len(video_ids),
                        'output_file': channel_output_file,
                        'status': 'success'
                    })
                
                thread_safe_print(f"{thread_id} ✓ Hoàn thành channel: {channel_url}")
                thread_safe_print(f"{thread_id}   - Đã cào {len(results)} video(s)")
                thread_safe_print(f"{thread_id}   - Output file: {channel_output_file}")
                
                scraper.close()
                
                return {
                    'channel_url': channel_url,
                    'status': 'success',
                    'video_count': len(video_ids),
                    'results_count': len(results),
                    'output_file': channel_output_file
                }
                
            except Exception as e:
                thread_safe_print(f"{thread_id} ✗ Lỗi khi xử lý channel {channel_url}: {str(e)}")
                import traceback
                thread_safe_print(f"{thread_id} Traceback: {traceback.format_exc()}")
                scraper.close()
                return {
                    'channel_url': channel_url,
                    'status': 'error',
                    'error': str(e)
                }
                
        except Exception as e:
            thread_safe_print(f"{thread_id} ✗ Lỗi khi khởi tạo scraper cho channel {channel_url}: {str(e)}")
            import traceback
            thread_safe_print(f"{thread_id} Traceback: {traceback.format_exc()}")
            return {
                'channel_url': channel_url,
                'status': 'error',
                'error': str(e)
            }
    
    # Chạy song song với ThreadPoolExecutor
    all_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tất cả tasks
        future_to_channel = {}
        for idx, channel in enumerate(valid_channels, 1):
            future = executor.submit(process_single_channel, channel, idx, len(valid_channels), auto_continue, wait_time)
            future_to_channel[future] = channel
        
        # Thu thập kết quả khi hoàn thành
        completed = 0
        for future in as_completed(future_to_channel):
            channel = future_to_channel[future]
            channel_url = channel.get('url', '')
            try:
                result = future.result()
                all_results.append(result)
                completed += 1
                thread_safe_print(f"\n[{completed}/{len(valid_channels)}] Đã hoàn thành channel: {channel_url}")
            except Exception as e:
                thread_safe_print(f"✗ Exception khi xử lý channel {channel_url}: {str(e)}")
                all_results.append({
                    'channel_url': channel_url,
                    'status': 'error',
                    'error': str(e)
                })
    
    # Tổng kết
    thread_safe_print(f"\n{'='*60}")
    thread_safe_print("TỔNG KẾT PARALLEL PROCESSING:")
    thread_safe_print(f"{'='*60}")
    success_count = sum(1 for r in all_results if r.get('status') == 'success')
    error_count = len(all_results) - success_count
    thread_safe_print(f"  - Tổng số channels: {len(valid_channels)}")
    thread_safe_print(f"  - Thành công: {success_count}")
    thread_safe_print(f"  - Lỗi: {error_count}")
    thread_safe_print(f"{'='*60}\n")
    
    # In chi tiết kết quả
    for result in all_results:
        channel_url = result.get('channel_url', 'Unknown')
        status = result.get('status', 'unknown')
        if status == 'success':
            thread_safe_print(f"✓ {channel_url}: {result.get('results_count', 0)} video(s) -> {result.get('output_file', 'N/A')}")
        else:
            thread_safe_print(f"✗ {channel_url}: Lỗi - {result.get('error', 'Unknown error')}")


def process_channel(channel_url=None, video_ids=None, cookies_file=None, output_file=None,
                    account_name=None, headless=False, video_account_mapping=None,
                    auto_continue=False, wait_time=30):
    """
    Cào dữ liệu analytics từ YouTube Studio cho một channel
    
    Lưu ý: Hàm này chỉ cào dữ liệu, không quản lý tài khoản.
    Cookies phải được setup trước thông qua get_channel_videos.py hoặc config.json
    """
    
    if not video_ids:
        print("Không có video IDs để xử lý!")
        return
    
    # Chế độ tuần tự (sequential)
    # Hiển thị thông tin tài khoản đang sử dụng
    if account_name:
        print(f"\nĐang sử dụng tài khoản: {account_name}")
    elif cookies_file:
        print(f"\nĐang sử dụng cookies file: {cookies_file}")
    else:
        print("\nSử dụng tài khoản mặc định")
    
    # Khởi tạo scraper với account_name hoặc cookies_file
    scraper = YouTubeAnalyticsScraper(cookies_file=cookies_file, account_name=account_name,
                                      auto_continue=auto_continue, wait_time=wait_time)
    scraper.init_driver(headless=headless)
    
    try:
        # Thử load cookies - nếu không có thì báo lỗi và dừng
        if not scraper.load_cookies(headless=headless):
            print("\n" + "="*50)
            print("LỖI: KHÔNG CÓ COOKIES!")
            print("="*50)
            print("Vui lòng setup cookies trước bằng cách:")
            print("1. Sử dụng get_channel_videos.py để đăng nhập và lưu cookies")
            print("2. Hoặc chỉ định cookies_file trong config.json")
            if account_name:
                print(f"\nTài khoản yêu cầu: {account_name}")
            if cookies_file:
                print(f"Cookies file: {cookies_file}")
            print("="*50)
            return
        # load_cookies() đã tự refresh và kiểm tra trạng thái đăng nhập
        
        # Hiển thị thông tin về mapping tài khoản nếu có
        if video_account_mapping:
            print("\n" + "="*50)
            print("MAPPING VIDEO - TÀI KHOẢN:")
            print("="*50)
            for vid, acc in video_account_mapping.items():
                print(f"  Video {vid} -> Tài khoản: {acc}")
            print("="*50)
        
        # Lấy analytics
        results = scraper.scrape_multiple_videos(video_ids, video_account_mapping=video_account_mapping, headless=headless)
        
        # Lưu kết quả với output_file (mặc định nếu không có)
        if not output_file:
            output_file = 'analytics_results.json'
        scraper.save_results(results, output_file=output_file)
        
        # In kết quả
        print("\n" + "="*50)
        print("KẾT QUẢ:")
        print("="*50)
        for result in results:
            print(f"\nVideo ID: {result['video_id']}")
            print(f"Traffic Sources: {result['how_viewers_find']}")
            print(f"Impressions Data: {result['impressions_data']}")
            
    except Exception as e:
        print(f"Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Đóng driver
        if scraper.driver:
            # Chỉ yêu cầu input nếu không phải headless mode
            if not headless:
                try:
                    input("\nNhấn Enter để đóng trình duyệt...")
                except (EOFError, KeyboardInterrupt):
                    # Nếu không có stdin (headless hoặc script), bỏ qua
                    pass
            scraper.close()


if __name__ == '__main__':
    main()
