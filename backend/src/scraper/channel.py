"""
Script để lấy tất cả video IDs từ một kênh YouTube sử dụng yt-dlp
Tự động đăng nhập, lưu cookies và quản lý nhiều tài khoản

Lưu ý quan trọng:
- Bước lấy video IDs từ channel KHÔNG cần cookies, chỉ dùng yt-dlp
- Cookies chỉ dùng để quản lý tài khoản và có thể dùng cho các mục đích khác (như cào analytics)

Cách sử dụng:
1. Cài đặt yt-dlp và selenium: pip install yt-dlp selenium

2. Chạy script với URL kênh và account name:
   python get_channel_videos.py "https://www.youtube.com/@channelname" --account-name "MyAccount"
   
   - Tự động đăng nhập và lưu cookies với tên account (để dùng cho craw.py)
   - Cookies lưu vào: profile/youtube_cookies_MyAccount.json
   - Tự động cập nhật danh sách tài khoản vào config.json
   - Mỗi channel có thể gắn với account riêng
   - Video IDs sẽ được lưu tự động vào config.json (lấy bằng yt-dlp, không cần cookies)

3. Chọn tài khoản tương tác:
   python get_channel_videos.py "URL" --interactive
   
4. Xem danh sách tài khoản:
   python get_channel_videos.py --list-accounts

5. Chuyển đổi tài khoản:
   python get_channel_videos.py "URL" --switch-account "AccountName"

6. Sử dụng cookies đã tồn tại:
   python get_channel_videos.py "URL" --account-name "MyAccount" --use-existing-cookies

Tính năng quản lý cookies và tài khoản:
   - Tự động kiểm tra và tái sử dụng cookies đã tồn tại
   - Load cookies từ file JSON (để dùng cho craw.py)
   - Chuyển đổi tài khoản (switch account) giữa các tài khoản đã lưu
   - Quản lý nhiều tài khoản trong cùng một hệ thống
   - Chọn tài khoản tương tác từ danh sách đã lưu
   - Tự động cập nhật thời gian sử dụng cuối
   - Cookies được lưu ở format JSON để dùng cho craw.py (cào analytics), không dùng cho bước lấy video IDs

Cấu trúc config.json:
   - Mỗi account có danh sách channels riêng
   - Mỗi channel có url và video_ids
   - Video IDs luôn được gộp (merge) với video_ids cũ, tránh trùng lặp
   - Có thể có nhiều accounts, mỗi account có nhiều channels
   - Dễ dàng phân biệt channel thuộc account nào

Các định dạng URL kênh được hỗ trợ:
- https://www.youtube.com/@channelname
- https://www.youtube.com/c/channelname
- https://www.youtube.com/channel/UCxxxxx
- https://www.youtube.com/user/username
"""
import json
import yt_dlp
import sys
import argparse
import os
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def load_cookies(cookies_file=None, account_name=None):
    """
    Load cookies từ file JSON (chỉ kiểm tra và xác nhận cookies hợp lệ)
    
    Args:
        cookies_file: Đường dẫn file cookies JSON
        account_name: Tên tài khoản (ưu tiên, sẽ tạo cookies_file từ account_name)
    
    Returns:
        str: Đường dẫn file cookies JSON (None nếu không load được)
    """
    # Xác định cookies_file
    if account_name:
        safe_account_name = re.sub(r'[^\w\-_]', '_', account_name)
        cookies_file = os.path.join('data/cookies/profile', f'youtube_cookies_{safe_account_name}.json')
    elif not cookies_file:
        cookies_file = os.path.join('data/cookies/profile', 'youtube_cookies.json')
    
    if not os.path.exists(cookies_file):
        print(f"Không tìm thấy file cookies: {cookies_file}")
        return None
    
    try:
        # Kiểm tra cookies file có hợp lệ không
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        if not cookies or len(cookies) == 0:
            print(f"File cookies rỗng: {cookies_file}")
            return None
        
        print(f"Đã load {len(cookies)} cookies từ: {cookies_file}")
        
        # Cập nhật account nếu có account_name
        if account_name:
            update_accounts_list(account_name, cookies_file)
        
        return cookies_file
        
    except Exception as e:
        print(f"Lỗi khi load cookies: {str(e)}")
        return None


def switch_account(account_name=None, cookies_file=None):
    """
    Chuyển đổi sang tài khoản khác
    
    Args:
        account_name: Tên tài khoản để chuyển đổi (ưu tiên)
        cookies_file: Đường dẫn đến file cookies (nếu không có account_name)
    
    Returns:
        str: Đường dẫn file cookies JSON (None nếu không chuyển đổi được)
    """
    # Xác định cookies_file mới
    new_cookies_file = None
    new_account_name = None
    
    if account_name:
        safe_account_name = re.sub(r'[^\w\-_]', '_', account_name)
        new_cookies_file = os.path.join('data/cookies/profile', f'youtube_cookies_{safe_account_name}.json')
        new_account_name = account_name
    elif cookies_file:
        new_cookies_file = cookies_file
        # Thử extract account_name từ cookies_file
        match = re.search(r'youtube_cookies_(.+)\.json$', cookies_file)
        new_account_name = match.group(1) if match else None
    else:
        print("Cần cung cấp account_name hoặc cookies_file để chuyển đổi tài khoản.")
        return None
    
    # Kiểm tra file cookies có tồn tại không
    if not os.path.exists(new_cookies_file):
        print(f"Không tìm thấy file cookies: {new_cookies_file}")
        return None
    
    print(f"\n{'='*50}")
    print(f"Đang chuyển đổi tài khoản...")
    if new_account_name:
        print(f"Tài khoản mới: {new_account_name}")
    print(f"Cookies file: {new_cookies_file}")
    print(f"{'='*50}")
    
    # Load cookies mới
    cookies_json_file = load_cookies(cookies_file=new_cookies_file, account_name=new_account_name)
    
    if cookies_json_file:
        print(f"✓ Đã chuyển đổi sang tài khoản: {new_account_name or 'Unknown'}")
        return cookies_json_file
    else:
        print("⚠ Không thể load cookies mới.")
        return None


def get_channel_video_ids(channel_url):
    """
    Lấy tất cả video IDs từ một kênh YouTube sử dụng yt-dlp (không cần cookies)
    
    Args:
        channel_url: URL của kênh YouTube (ví dụ: https://www.youtube.com/@channelname hoặc https://www.youtube.com/c/channelname)
    
    Returns:
        List các video IDs
    """
    video_ids = []
    
    # Chuyển đổi URL để truy cập trực tiếp tab videos
    # Nếu là channel ID, thêm /videos
    if '/channel/' in channel_url:
        if not channel_url.endswith('/videos'):
            channel_url = channel_url.rstrip('/') + '/videos'
    elif '/@' in channel_url:
        if not channel_url.endswith('/videos'):
            channel_url = channel_url.rstrip('/') + '/videos'
    elif '/c/' in channel_url or '/user/' in channel_url:
        if not channel_url.endswith('/videos'):
            channel_url = channel_url.rstrip('/') + '/videos'
    
    # Cấu hình yt-dlp (không sử dụng cookies)
    ydl_opts = {
        'quiet': False,  # Hiển thị progress
        'extract_flat': True,  # Chỉ lấy metadata, không download
        'no_warnings': False,
        'ignoreerrors': True,  # Bỏ qua lỗi nếu có video không thể extract
    }
    
    try:
        print(f"Đang quét kênh: {channel_url}")
        print("Vui lòng đợi...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Lấy thông tin kênh
            info = ydl.extract_info(channel_url, download=False)
            
            if not info:
                print("Không thể lấy thông tin kênh!")
                return []
            
            # Hàm helper để extract video ID từ entry
            def extract_video_id(entry):
                """Extract video ID từ một entry"""
                if not entry:
                    return None
                
                # Trường hợp 1: Entry có 'id' và là video ID hợp lệ (11 ký tự)
                if 'id' in entry:
                    video_id = entry['id']
                    # Kiểm tra xem có phải là video ID không (11 ký tự, không phải channel ID)
                    if len(video_id) == 11 and not video_id.startswith('UC'):
                        return video_id
                
                # Trường hợp 2: Entry có 'url' - extract video ID từ URL
                if 'url' in entry:
                    url = entry['url']
                    if 'watch?v=' in url:
                        video_id = url.split('watch?v=')[1].split('&')[0].split('#')[0]
                        if len(video_id) == 11:
                            return video_id
                
                # Trường hợp 3: Entry là string (video ID trực tiếp)
                if isinstance(entry, str) and len(entry) == 11 and not entry.startswith('UC'):
                    return entry
                
                return None
            
            # Hàm helper để extract video IDs từ entries (có thể recursive)
            def extract_videos_from_entries(entries, depth=0):
                """Extract video IDs từ entries, xử lý cả playlist entries"""
                ids = []
                if not entries:
                    return ids
                
                for entry in entries:
                    if not entry:
                        continue
                
                    # Kiểm tra xem entry có phải là playlist không
                    entry_type = entry.get('_type', '')
                    if entry_type == 'playlist' or 'playlist' in str(entry.get('id', '')).lower():
                        # Nếu là playlist, extract từ entries của playlist
                        if 'entries' in entry and entry['entries']:
                            ids.extend(extract_videos_from_entries(entry['entries'], depth + 1))
                            continue
                        
                    # Extract video ID
                    video_id = extract_video_id(entry)
                    if video_id and video_id not in ids:
                        ids.append(video_id)
                
                return ids
            
            # Trích xuất video IDs
            if 'entries' in info and info['entries']:
                entries = info['entries']
                print(f"\nĐang xử lý {len(entries)} entry(s)...")
                
                # Extract video IDs từ entries
                video_ids = extract_videos_from_entries(entries)
                
                # Hiển thị kết quả
                if video_ids:
                    print(f"\nTìm thấy {len(video_ids)} video(s):")
                    for i, video_id in enumerate(video_ids[:50], 1):  # Hiển thị tối đa 50 video đầu
                        print(f"{i}. {video_id}")
                    if len(video_ids) > 50:
                        print(f"... và {len(video_ids) - 50} video khác")
                    print(f"\nTổng cộng: {len(video_ids)} video IDs")
                else:
                    print("Không tìm thấy video ID nào trong entries!")
                    print("Có thể kênh chưa có video hoặc cần truy cập tab /videos")
            else:
                # Nếu không có entries, có thể là single video
                video_id = extract_video_id(info)
                if video_id:
                    video_ids.append(video_id)
                    print(f"\nTìm thấy 1 video: {video_id}")
                else:
                    print("Không tìm thấy video nào trong kênh này!")
                    print("Thử kiểm tra lại URL hoặc đảm bảo kênh có video công khai")
                    
    except yt_dlp.utils.DownloadError as e:
        print(f"Lỗi khi tải thông tin kênh: {str(e)}")
        print("\nGợi ý:")
        print("- Kiểm tra lại URL kênh (ví dụ: https://www.youtube.com/@channelname)")
        print("- Đảm bảo kênh công khai và có video")
        return []
    except Exception as e:
        print(f"Lỗi khi quét kênh: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
    
    return video_ids


def init_chrome_driver(headless=False):
    """Khởi tạo Chrome driver"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--log-level=3')
    prefs = {
        "profile.default_content_setting_values.notifications": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()
        return driver
    except Exception as e:
        print(f"Lỗi khi khởi tạo Chrome driver: {str(e)}")
        raise


def login_and_save_cookies(account_name=None, cookies_file=None):
    """
    Đăng nhập Google/YouTube và lưu cookies
        
        Args:
        account_name: Tên tài khoản (tùy chọn)
        cookies_file: Đường dẫn file cookies (tùy chọn, sẽ tự tạo nếu có account_name)
        
        Returns:
        str: Đường dẫn file cookies đã lưu
    """
    # Xác định cookies_file
    if account_name:
        # Tạo tên file cookies dựa trên account_name
        safe_account_name = re.sub(r'[^\w\-_]', '_', account_name)
        cookies_file = os.path.join('data/cookies/profile', f'youtube_cookies_{safe_account_name}.json')
    elif not cookies_file:
        # Mặc định: dùng cookies file mặc định
        cookies_file = os.path.join('data/cookies/profile', 'youtube_cookies.json')
    
    # Đảm bảo thư mục profile tồn tại
    os.makedirs('data/cookies/profile', exist_ok=True)
    
    # Kiểm tra xem cookies_file đã tồn tại chưa
    if os.path.exists(cookies_file):
        print(f"Cookies file đã tồn tại: {cookies_file}")
        response = input("Bạn có muốn đăng nhập lại? (y/n): ").strip().lower()
        if response != 'y':
            return cookies_file
    
    print("\n" + "="*50)
    print("ĐĂNG NHẬP VÀ LƯU COOKIES")
    print("="*50)
    if account_name:
        print(f"Tài khoản: {account_name}")
    print(f"Cookies file: {cookies_file}")
    print("="*50 + "\n")
    
    driver = None
    try:
        # Khởi tạo driver
        print("Đang khởi tạo Chrome driver...")
        driver = init_chrome_driver(headless=False)

        # Đăng nhập Google
        print("Đang mở trang đăng nhập Google...")
        driver.get('https://accounts.google.com')

        print("\nVui lòng đăng nhập thủ công trong trình duyệt...")
        print("Đang chờ đăng nhập thành công (tối đa 120 giây)...")

        # Chờ tự động cho đến khi user đăng nhập thành công
        # Kiểm tra xem user đã được chuyển hướng đến trang sau đăng nhập không
        max_wait = 120  # Chờ tối đa 120 giây
        wait_interval = 2  # Kiểm tra mỗi 2 giây
        elapsed = 0

        while elapsed < max_wait:
            try:
                # Kiểm tra xem user đã đăng nhập bằng cách kiểm tra URL
                current_url = driver.current_url
                # Nếu đã rời khỏi trang đăng nhập, có thể đã đăng nhập
                if 'accounts.google.com' not in current_url or elapsed > 10:
                    break
                time.sleep(wait_interval)
                elapsed += wait_interval
                print(f"  Chờ đăng nhập ({elapsed}s)...")
            except Exception as e:
                print(f"  Kiểm tra đăng nhập: {str(e)}")
                break

        print("✓ Đã phát hiện đăng nhập thành công")

        # Điều hướng đến YouTube để lấy cookies của YouTube
        print("\nĐang điều hướng đến YouTube để lấy cookies...")
        driver.get('https://www.youtube.com')
        time.sleep(5)  # Đợi trang YouTube load xong
        
        # Lưu cookies
        cookies = driver.get_cookies()
        cookies_dir = os.path.dirname(cookies_file)
        if cookies_dir and not os.path.exists(cookies_dir):
            os.makedirs(cookies_dir, exist_ok=True)
        
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Đã lưu cookies vào: {cookies_file}")
        
        # Cập nhật danh sách tài khoản nếu có account_name
        if account_name:
            update_accounts_list(account_name, cookies_file)
        
        return cookies_file
        
    except Exception as e:
        print(f"Lỗi khi đăng nhập: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if driver:
            try:
                print("\nTự động đóng trình duyệt...")
                time.sleep(2)  # Give user time to see the message
                driver.quit()
                print("✓ Trình duyệt đã đóng")
            except:
                pass


def update_accounts_list(account_name, cookies_file):
    """Cập nhật danh sách tài khoản vào config.json"""
    config_file = 'config.json'
    
    # Đọc config hiện tại
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {}
    except Exception:
        config = {}
    
    # Đảm bảo có key 'accounts'
    if 'accounts' not in config:
        config['accounts'] = []
    
    # Kiểm tra xem tài khoản đã tồn tại chưa
    account_exists = False
    for acc in config['accounts']:
        if acc.get('name') == account_name:
            # Cập nhật thông tin
            acc['cookies_file'] = cookies_file
            account_exists = True
            break
    
    # Nếu chưa tồn tại, thêm mới
    if not account_exists:
        new_account = {
            'name': account_name,
            'cookies_file': cookies_file,
            'channels': []  # Mỗi account có danh sách channels riêng
        }
        config['accounts'].append(new_account)
    else:
        # Đảm bảo account đã tồn tại có field 'channels'
        for acc in config['accounts']:
            if acc.get('name') == account_name:
                if 'channels' not in acc:
                    acc['channels'] = []
                break
    
    # Lưu lại vào config.json (merge với dữ liệu hiện có)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"Đã cập nhật danh sách tài khoản vào config.json: {account_name}")


def get_accounts_list():
    """Lấy danh sách các tài khoản đã lưu từ config.json"""
    config_file = 'config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('accounts', [])
        except Exception as e:
            print(f"Lỗi khi đọc danh sách tài khoản từ config.json: {str(e)}")
            return []
    return []


def list_accounts():
    """Hiển thị danh sách tài khoản"""
    accounts = get_accounts_list()
    if not accounts:
        print("Chưa có tài khoản nào được lưu.")
        return
    
    print("\n" + "="*50)
    print("DANH SÁCH TÀI KHOẢN:")
    print("="*50)
    for i, acc in enumerate(accounts, 1):
        print(f"{i}. {acc.get('name', 'Unknown')}")
        print(f"   Cookies file: {acc.get('cookies_file', 'N/A')}")
        channels_count = len(acc.get('channels', []))
        if channels_count > 0:
            total_videos = sum(len(ch.get('video_ids', [])) for ch in acc.get('channels', []))
            print(f"   Channels: {channels_count}, Video IDs: {total_videos}")
        print()
    return accounts


def select_account_interactive():
    """Hiển thị menu chọn tài khoản tương tác"""
    accounts = get_accounts_list()
    if not accounts:
        print("Chưa có tài khoản nào được lưu.")
        return None
    
    print("\n" + "="*50)
    print("CHỌN TÀI KHOẢN:")
    print("="*50)
    for i, acc in enumerate(accounts, 1):
        channels_count = len(acc.get('channels', []))
        total_videos = sum(len(ch.get('video_ids', [])) for ch in acc.get('channels', []))
        print(f"{i}. {acc.get('name', 'Unknown')} (Channels: {channels_count}, Videos: {total_videos})")
    
    print(f"{len(accounts) + 1}. Tạo tài khoản mới")
    print("0. Hủy")
    
    while True:
        try:
            choice = input(f"\nChọn tài khoản (0-{len(accounts) + 1}): ").strip()
            choice_num = int(choice)
            
            if choice_num == 0:
                return None
            elif choice_num == len(accounts) + 1:
                # Tạo tài khoản mới
                new_name = input("Nhập tên tài khoản mới: ").strip()
                if new_name:
                    return new_name
                else:
                    print("Tên tài khoản không được để trống!")
                    continue
            elif 1 <= choice_num <= len(accounts):
                return accounts[choice_num - 1].get('name')
            else:
                print(f"Lựa chọn không hợp lệ! Vui lòng chọn từ 0 đến {len(accounts) + 1}")
        except ValueError:
            print("Vui lòng nhập một số hợp lệ!")
        except KeyboardInterrupt:
            print("\nĐã hủy.")
            return None


def save_to_config(channel_url, video_ids, config_file='config.json', cookies_file=None, output_file=None):
    """
    Lưu video IDs vào config.json trong account tương ứng (luôn merge với video_ids cũ, tránh trùng lặp)
    
    Args:
        channel_url: URL của kênh YouTube
        video_ids: List các video IDs
        config_file: Đường dẫn file config
        cookies_file: Đường dẫn file cookies cho channel này (dùng để tìm account tương ứng)
        output_file: Đường dẫn file output cho channel này (tùy chọn)
    """
    try:
        # Đọc config hiện tại
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {}
        
        # Đảm bảo có field 'accounts'
        if 'accounts' not in config:
            config['accounts'] = []
        
        # Tìm account dựa trên cookies_file (chuẩn hóa path để so sánh)
        target_account = None
        if cookies_file:
            # Chuẩn hóa cookies_file path
            normalized_cookies_file = os.path.normpath(cookies_file).replace('\\', '/')
            for acc in config['accounts']:
                acc_cookies_file = acc.get('cookies_file', '')
                if acc_cookies_file:
                    # Chuẩn hóa path trong account để so sánh
                    normalized_acc_cookies = os.path.normpath(acc_cookies_file).replace('\\', '/')
                    if normalized_acc_cookies == normalized_cookies_file:
                        target_account = acc
                        break
        
        # Nếu không tìm thấy account, báo lỗi
        if not target_account:
            if cookies_file:
                print(f"\n⚠ Lỗi: Không tìm thấy account với cookies_file: {cookies_file}")
                print("  Channel sẽ không được lưu.")
                print("  Vui lòng đảm bảo account đã được tạo trước khi lưu channel.")
                print("  Chạy lại với --account-name để tạo account trước.")
            else:
                print(f"\n⚠ Lỗi: Không có cookies_file để xác định account.")
                print("  Channel sẽ không được lưu.")
                print("  Vui lòng chạy lại với --account-name để tạo account và lưu channel.")
            return False
        
        # Đảm bảo account có field 'channels'
        if 'channels' not in target_account:
            target_account['channels'] = []
        
        # Chuẩn hóa channel_url (loại bỏ /videos nếu có)
        normalized_url = channel_url.replace('/videos', '').rstrip('/')
        
        # Tìm channel trong danh sách channels của account
        channel_found = False
        for channel in target_account['channels']:
            if channel.get('url', '').replace('/videos', '').rstrip('/') == normalized_url:
                # Lưu số lượng video_ids cũ để hiển thị
                old_count = len(channel.get('video_ids', []))
                
                # Merge video_ids, tránh trùng lặp
                existing_ids = set(channel.get('video_ids', []))
                new_ids = [vid for vid in video_ids if vid not in existing_ids]
                channel['video_ids'].extend(new_ids)
                channel['video_ids'] = list(dict.fromkeys(channel['video_ids']))  # Loại bỏ trùng lặp
                new_count = len(new_ids)
                
                channel_found = True
                print(f"\nĐã cập nhật channel trong account '{target_account.get('name', 'Unknown')}': {normalized_url}")
                print(f"  - Video IDs cũ: {old_count}")
                print(f"  - Video IDs mới thêm: {new_count}")
                print(f"  - Tổng video IDs của channel: {len(channel['video_ids'])}")
                break
        
        # Nếu chưa có channel này, thêm mới vào account
        if not channel_found:
            new_channel = {
                'url': normalized_url,
                'video_ids': video_ids.copy()
            }
            # Thêm output_file nếu được cung cấp
            if output_file:
                new_channel['output_file'] = output_file
            target_account['channels'].append(new_channel)
            print(f"\nĐã thêm channel mới vào account '{target_account.get('name', 'Unknown')}': {normalized_url}")
            print(f"  - Video IDs: {len(video_ids)}")
            if output_file:
                print(f"  - Output file: {output_file}")
        else:
            # Cập nhật output_file nếu được cung cấp
            if output_file:
                channel['output_file'] = output_file
                print(f"  - Output file: {output_file}")
        
        # Lưu lại
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        # Thống kê
        account_name = target_account.get('name', 'Unknown')
        total_channels = len(target_account.get('channels', []))
        total_videos = sum(len(ch.get('video_ids', [])) for ch in target_account.get('channels', []))
        
        print(f"\n{'='*50}")
        print(f"Đã lưu vào {config_file}:")
        print(f"  - Account: {account_name}")
        print(f"  - Tổng số channels trong account: {total_channels}")
        print(f"  - Tổng số video IDs trong account: {total_videos}")
        print(f"{'='*50}")
        return True
        
    except Exception as e:
        print(f"Lỗi khi lưu config: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Lấy tất cả video IDs từ một kênh YouTube sử dụng yt-dlp và lưu vào config.json'
    )
    parser.add_argument(
        'channel_url',
        help='URL của kênh YouTube (ví dụ: https://www.youtube.com/@channelname)'
    )
    parser.add_argument(
        '--account-name',
        type=str,
        default=None,
        help='Tên tài khoản để đăng nhập và lưu cookies (khuyến nghị)'
    )
    parser.add_argument(
        '--cookies-file',
        type=str,
        default=None,
        help='Đường dẫn file cookies cho channel này (tùy chọn, sẽ tự tạo nếu có account-name)'
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default=None,
        help='Đường dẫn file output cho channel này (tùy chọn)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Chọn tài khoản tương tác từ danh sách đã lưu'
    )
    parser.add_argument(
        '--list-accounts',
        action='store_true',
        help='Hiển thị danh sách tài khoản đã lưu và thoát'
    )
    parser.add_argument(
        '--switch-account',
        type=str,
        default=None,
        help='Chuyển đổi sang tài khoản khác (tên tài khoản hoặc cookies_file)'
    )
    parser.add_argument(
        '--use-existing-cookies',
        action='store_true',
        help='Sử dụng cookies đã tồn tại thay vì đăng nhập lại'
    )
    
    args = parser.parse_args()
    
    # Nếu chỉ muốn liệt kê tài khoản
    if args.list_accounts:
        list_accounts()
        sys.exit(0)
    
    # Xử lý chọn tài khoản tương tác
    account_name = args.account_name
    if args.interactive and not account_name:
        selected_account = select_account_interactive()
        if selected_account:
            account_name = selected_account
            print(f"Đã chọn tài khoản: {account_name}")
        elif selected_account is None:
            print("Đã hủy chọn tài khoản.")
            sys.exit(1)
    
    # Xử lý chuyển đổi tài khoản
    cookies_json_file = args.cookies_file
    
    if args.switch_account:
        # Chuyển đổi tài khoản
        cookies_json_file = switch_account(account_name=args.switch_account, cookies_file=args.switch_account)
        if cookies_json_file:
            # Cập nhật account_name từ switch_account
            account_name = args.switch_account
        else:
            print("⚠ Không thể chuyển đổi tài khoản. Tiếp tục với tài khoản hiện tại hoặc đăng nhập mới.")
    
    # Xử lý load cookies hoặc đăng nhập
    if not cookies_json_file:
        # Thử load cookies nếu có account_name hoặc cookies_file
        if account_name or args.cookies_file:
            if args.use_existing_cookies or (args.cookies_file and os.path.exists(args.cookies_file)):
                # Load cookies đã tồn tại
                cookies_json_file = load_cookies(cookies_file=args.cookies_file, account_name=account_name)
                if not cookies_json_file:
                    print("⚠ Không thể load cookies. Cần đăng nhập lại.")
                    # Tiếp tục với đăng nhập
                    try:
                        cookies_json_file = login_and_save_cookies(
                            account_name=account_name,
                            cookies_file=args.cookies_file
                        )
                    except KeyboardInterrupt:
                        print("\nĐã hủy đăng nhập.")
                        sys.exit(1)
                    except Exception as e:
                        print(f"\nLỗi khi đăng nhập: {str(e)}")
                        response = input("Bạn có muốn tiếp tục mà không có cookies? (y/n): ").strip().lower()
                        if response != 'y':
                            sys.exit(1)
                        cookies_json_file = None
            else:
                # Đăng nhập mới
                try:
                    cookies_json_file = login_and_save_cookies(
                        account_name=account_name,
                        cookies_file=args.cookies_file
                    )
                except KeyboardInterrupt:
                    print("\nĐã hủy đăng nhập.")
                    sys.exit(1)
                except Exception as e:
                    print(f"\nLỗi khi đăng nhập: {str(e)}")
                    response = input("Bạn có muốn tiếp tục mà không có cookies? (y/n): ").strip().lower()
                    if response != 'y':
                        sys.exit(1)
                    cookies_json_file = None
        else:
            # Không có account_name và cookies_file
            print("⚠ Cảnh báo: Khuyến nghị sử dụng --account-name hoặc --interactive để quản lý tài khoản tốt hơn")
            print("   Ví dụ: python get_channel_videos.py \"URL\" --account-name \"MyAccount\"")
            print("   Hoặc: python get_channel_videos.py \"URL\" --interactive")
            response = input("\nBạn có muốn tiếp tục mà không có account-name? (y/n): ").strip().lower()
            if response != 'y':
                print("Đã hủy. Vui lòng chạy lại với --account-name hoặc --interactive")
                sys.exit(1)
    
    # Lấy video IDs (không cần cookies, chỉ dùng yt-dlp)
    print("\n" + "="*50)
    print("LẤY VIDEO IDs TỪ CHANNEL")
    print("="*50)
    video_ids = get_channel_video_ids(args.channel_url)
    
    if not video_ids:
        print("Không lấy được video IDs nào!")
        sys.exit(1)
    
    # Lưu vào config.json (luôn merge với video_ids cũ)
    print("\n" + "="*50)
    print("LƯU VÀO CONFIG.JSON")
    print("="*50)
    save_to_config(
        args.channel_url, 
        video_ids, 
        cookies_file=cookies_json_file,
        output_file=args.output_file
    )
    
    print("\n✓ Hoàn thành!")


if __name__ == '__main__':
    main()

