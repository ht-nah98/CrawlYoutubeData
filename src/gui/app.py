"""
GUI Application for YouTube Channel Data Scraping
Ứng dụng GUI để cào dữ liệu kênh YouTube - Modern Design

Tác giả: YouTube Analytics Scraper
Ngày tạo: 2024
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, font as tkFont, simpledialog
from datetime import datetime
import threading
import json
import os
import time
import re
import sys
import signal

# Disable theme change events to prevent segmentation fault
# This is a known issue with Tkinter/CustomTkinter mixing
os.environ['TK_SILENCE_DEPRECATION'] = '1'

# Tcl patching is handled in main.py to prevent multiple Tk instances

# Import các module cần thiết
CUSTOM_TK_AVAILABLE = False
# try:
#     import customtkinter as ctk
#     CUSTOM_TK_AVAILABLE = True
# except ImportError:
#     pass

if not CUSTOM_TK_AVAILABLE:
    print("Using standard tkinter (CustomTkinter not found)")
else:
    print("Using CustomTkinter for modern UI")

# Import logic từ các file khác
from src.scraper.channel import (
    get_channel_video_ids,
    login_and_save_cookies,
    load_cookies,
    update_accounts_list,
    get_accounts_list,
    select_account_interactive,
    save_to_config
)
from src.scraper.youtube import YouTubeAnalyticsScraper, process_channel
from src.utils.scraping_tracker import ScrapingTracker
from src.database.writers import db_writer
from src.database.models import Account
from src.database.connection import db


class ModernColors:
    """Modern color palette - Professional & Clean (Dark Mode)"""
    # Primary colors
    PRIMARY = "#3B82F6"  # Bright Blue
    PRIMARY_DARK = "#1D4ED8"
    PRIMARY_LIGHT = "#60A5FA"
    
    # Accent colors
    ACCENT = "#60A5FA"  # Lighter Blue
    SUCCESS = "#10B981"  # Emerald
    WARNING = "#F59E0B"  # Amber
    ERROR = "#EF4444"  # Red
    INFO = "#06B6D4"  # Cyan
    
    # Background colors
    BG_DARK = "#0F172A"  # Slate 900 (Deep Blue/Black)
    BG_CARD = "#1E293B"  # Slate 800 (Card Background)
    BG_HOVER = "#334155"  # Slate 700
    BG_SELECTED = "#1E40AF"  # Blue 800
    
    # Text colors
    TEXT_PRIMARY = "#F8FAFC"  # Slate 50
    TEXT_SECONDARY = "#94A3B8"  # Slate 400
    TEXT_MUTED = "#64748B"  # Slate 500
    TEXT_WHITE = "#FFFFFF"
    
    # Border colors
    BORDER = "#334155"  # Slate 700
    BORDER_DARK = "#1E293B"  # Slate 800
    
    # Special
    SHADOW = "#00000040"  # Stronger shadow for dark mode
    YOUTUBE_RED = "#FF0000"  # YouTube brand color
    
    # Backward compatibility
    SECONDARY = "#334155"  # Slate 700


class YouTubeScraperGUI:
    def __init__(self):
        # Khởi tạo giao diện - Dark theme
        if CUSTOM_TK_AVAILABLE:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.root = ctk.CTk()
            self.root.configure(fg_color=ModernColors.BG_DARK)
        else:
            self.root = tk.Tk()
            self.root.configure(bg=ModernColors.BG_DARK)

        # CRITICAL: Apply Tcl patch - DISABLED for debugging
        # try:
        #     self.root.eval("""
        #     # Disable all ttk theme change callbacks
        #     proc ttk::ThemeChanged args {
        #         # Silently ignore theme change events to prevent segfault
        #         return
        #     }
        #
        #     # Also patch the style command to prevent theme operations
        #     proc ttk::style {args} {
        #         # Safely handle style operations
        #         return
        #     }
        #     """)
        # except Exception as e:
        #     print(f"Warning: Failed to patch Tcl: {e}")

        # Prevent Tkinter theme event errors on shutdown - REMOVED to fix segfault
        # try:
        #     self.root.withdraw()  # Hide window temporarily during initialization
        #     self.root.update()
        # except:
        #     pass

        # Khởi tạo các biến logic nghiệp vụ
        self.scraper = None  # YouTubeAnalyticsScraper instance
        self.current_account_name = None
        self.current_cookies_file = None
        self.current_channel_url = None
        self.current_video_ids = []
        self.scraping_thread = None
        self.auto_scraping_thread = None
        self.is_scraping = False
        self.is_auto_scraping = False
        self.auto_scraping_interval = 5  # phút

        # Settings cho login
        self.auto_continue = True  # Tự động tiếp tục sau đăng nhập
        self.wait_time = 60  # Thời gian chờ (giây)
        
        # Scraping tracker để tránh cào lại video đã cào gần đây
        self.scraping_tracker = ScrapingTracker()
        self.min_scrape_interval_hours = 24  # Chỉ cào lại video đã cào cách đây >= 24 giờ

        # === MULTI-ACCOUNT SUPPORT VARIABLES ===
        # StringVar for account and channel selection
        self.account_var = tk.StringVar(value="")
        self.channel_var = tk.StringVar(value="")
        self.channel_mode_var = tk.StringVar(value="existing")  # "existing" or "new"

        # UI component references
        self.account_dropdown = None
        self.channel_dropdown = None

        # === BATCH SCRAPING VARIABLES ===
        self.selected_accounts = {}  # {account_name: BooleanVar}
        self.batch_scraping_widgets = {}  # Store toggle widgets for updates
        self.account_status_label = None
        self.url_entry = None
        self.max_results_entry = None
        self.existing_channel_frame = None
        self.new_channel_frame = None
        self.account_selector_card = None
        
        # === NEW WORKFLOW VARIABLES ===
        self.pending_channels = []  # List of channel URLs to fetch for selected account
        self.pending_channels_widgets = []  # UI widgets for pending channels list
        self.channel_management_frame = None  # Frame that appears after selecting account
        self.accounts_overview_frame = None  # Reference to accounts overview card

        self.root.title("🎥 YouTube Analytics Scraper")
        
        # Configure icon (optional) - DISABLED to prevent Linux segfault
        # try:
        #     self.root.iconbitmap(default="")  # Add icon path if available
        # except:
        #     pass
        
        # Cho phép responsive (resize)
        self.root.resizable(True, True)
        
        # Đặt kích thước tối thiểu và tối đa
        self.root.minsize(900, 650)
        # Không giới hạn maxsize để có thể fullscreen
        
        # Lấy kích thước màn hình ngay từ đầu
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Đặt geometry = fullscreen ngay từ đầu
        self.root.geometry(f'{screen_width}x{screen_height}+0+0')
        
        # Tạo giao diện
        self.create_widgets()
        # label = tk.Label(self.root, text="SAFE MODE: If you see this, the app core is working.", font=("Arial", 14))
        # label.pack(expand=True, fill='both', padx=50, pady=50)

        # Cố gắng maximize (nếu có thể)
        # self.root.after(50, self.maximize_window)

        # Khởi tạo logic nghiệp vụ
    # self.init_business_logic() - DISABLED FOR DEBUGGING
        
    def center_window(self):
        """Căn giữa cửa sổ ban đầu"""
        self.root.update_idletasks()
        width = 1000
        height = 750
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def maximize_window(self):
        """Maximize cửa sổ để fullscreen - Simplified for Linux stability"""
        try:
            # Just set a large size instead of forcing maximized state
            # This is safer on Linux to avoid segfaults
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            # Use 90% of screen size
            w = int(screen_width * 0.9)
            h = int(screen_height * 0.9)
            x = int((screen_width - w) / 2)
            y = int((screen_height - h) / 2)
            self.root.geometry(f'{w}x{h}+{x}+{y}')
        except:
            pass
        
    def create_widgets(self):
        """Tạo các widget cho giao diện"""
        
        parent = None
        
        if CUSTOM_TK_AVAILABLE:
            # Use CTkScrollableFrame for modern scrolling without segfaults
            # This avoids the Canvas + Frame issues
            self.main_frame = ctk.CTkScrollableFrame(
                self.root,
                fg_color=ModernColors.BG_DARK,
                corner_radius=0
            )
            self.main_frame.pack(fill="both", expand=True)
            
            # Add some padding for the content inside
            # We create a container frame inside the scrollable frame
            content_container = ctk.CTkFrame(
                self.main_frame, 
                fg_color=ModernColors.BG_DARK
            )
            content_container.pack(fill="both", expand=True, padx=25, pady=25)
            
            # For compatibility, main_frame should be the container where widgets are added
            self.scrollable_frame = self.main_frame # Keep reference
            self.main_frame = content_container
            parent = self.main_frame
            
        else:
            # Tạo canvas với scrollbar để có thể cuộn (Standard Tkinter)
            canvas_container = tk.Frame(self.root, bg=ModernColors.BG_DARK)
            canvas_container.pack(fill="both", expand=True, side="top")
            
            # Canvas để chứa nội dung có thể cuộn
            canvas = tk.Canvas(
                canvas_container,
                bg=ModernColors.BG_DARK,
                highlightthickness=0
            )
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(
                canvas_container,
                orient="vertical",
                command=canvas.yview
            )
            
            # Cấu hình canvas và scrollbar
            canvas.configure(yscrollcommand=scrollbar.set)
            
            # Pack scrollbar và canvas
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            
            # Tạo frame padding bên trong canvas (dùng để tạo padding)
            padding_frame = tk.Frame(canvas, bg=ModernColors.BG_DARK)
            
            # Main container (bên trong padding_frame, có padding)
            main_frame = tk.Frame(padding_frame, bg=ModernColors.BG_DARK)
            main_frame.pack(fill="both", expand=True, padx=25, pady=25)
            
            # Tạo window trong canvas để chứa padding_frame
            canvas_window = canvas.create_window((0, 0), window=padding_frame, anchor="nw")
            
            # Hàm để cập nhật scroll region khi nội dung thay đổi
            def configure_scroll_region(event=None):
                canvas.update_idletasks()
                bbox = canvas.bbox("all")
                if bbox:
                    canvas.config(scrollregion=bbox)
                # Cập nhật width của canvas window để fit với canvas
                canvas_width = canvas.winfo_width()
                if canvas_width > 1:
                    # Trừ đi space cho scrollbar (khoảng 20px)
                    canvas.itemconfig(canvas_window, width=canvas_width - 20)
            
            # Bind events để cập nhật scroll region
            padding_frame.bind("<Configure>", configure_scroll_region)
            main_frame.bind("<Configure>", configure_scroll_region)
            canvas.bind("<Configure>", configure_scroll_region)
            
            # Cho phép cuộn bằng mouse wheel
            def on_mousewheel(event):
                # Kiểm tra nếu widget là text widget (có scroll riêng) thì không cuộn canvas
                widget = event.widget
                if isinstance(widget, (tk.Text, scrolledtext.ScrolledText)):
                    # Text widget tự xử lý scrolling
                    return
                # Cuộn canvas
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
            # Hàm xử lý mouse wheel cho Linux
            def on_linux_mousewheel(event, direction):
                widget = event.widget
                if isinstance(widget, (tk.Text, scrolledtext.ScrolledText)):
                    return
                canvas.yview_scroll(direction, "units")
            
            # Bind mouse wheel (Windows/Mac)
            try:
                self.root.bind_all("<MouseWheel>", on_mousewheel)
            except:
                pass
            # Linux mouse wheel
            try:
                self.root.bind_all("<Button-4>", lambda e: on_linux_mousewheel(e, -1))
                self.root.bind_all("<Button-5>", lambda e: on_linux_mousewheel(e, 1))
            except:
                pass
            
            self.main_canvas = canvas
            self.main_frame = main_frame
            parent = main_frame
            
            # Cập nhật scroll region lần đầu
            self.root.after(100, configure_scroll_region)
        
        # Header với gradient effect (simulated)
        self.create_header(parent)
        
        # Instructions card - Modern design
        self.create_instructions_card(parent)

        # === NEW WORKFLOW: Accounts Overview at TOP ===
        self.create_accounts_overview_card(parent)

        # === Account selector - Select which account to manage ===
        self.create_account_selector_card(parent)

        # === Channel Management - Add channels to selected account ===
        self.create_channel_management_card(parent)

        # Login settings card - Cài đặt đăng nhập
        self.create_login_settings_card(parent)

        # Control buttons - Modern buttons
        self.create_control_section(parent)
        
        # Progress section - Animated
        self.create_progress_section(parent)
        
        # Log section - Console style
        self.create_log_section(parent)
        
        # Status bar - Minimal
        self.create_status_bar()
        
    def create_header(self, parent):
        """Tạo header đẹp với modern design"""
        if CUSTOM_TK_AVAILABLE:
            header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        else:
            header_frame = tk.Frame(parent, bg=ModernColors.BG_DARK)
        header_frame.pack(fill="x", pady=(0, 30))
        
        # Title Container for alignment
        if CUSTOM_TK_AVAILABLE:
            title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
            title_container.pack()
            
            # Main Title
            title_label = ctk.CTkLabel(
                title_container,
                text="🎥 YouTube Analytics Scraper",
                font=ctk.CTkFont(size=32, weight="bold", family="Segoe UI"),
                text_color=ModernColors.TEXT_WHITE
            )
            title_label.pack(side="left", padx=(0, 10))
            
            # PRO Badge
            badge = ctk.CTkLabel(
                title_container,
                text=" PRO ",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#FFFFFF",
                fg_color=ModernColors.PRIMARY,
                corner_radius=6,
                height=24
            )
            badge.pack(side="left", pady=5)
            
        else:
            title_label = tk.Label(
                header_frame,
                text="🎥 YouTube Analytics Scraper",
                font=("Segoe UI", 32, "bold"),
                fg=ModernColors.PRIMARY,
                bg=ModernColors.BG_DARK
            )
            title_label.pack()
        
        # Subtitle với better spacing
        if CUSTOM_TK_AVAILABLE:
            subtitle = ctk.CTkLabel(
                header_frame,
                text="Professional YouTube Analytics Scraping Tool • Version 2.0",
                font=ctk.CTkFont(size=14),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            subtitle = tk.Label(
                header_frame,
                text="Professional YouTube Analytics Scraping Tool • Version 2.0",
                font=("Segoe UI", 13),
                fg=ModernColors.TEXT_SECONDARY,
                bg=ModernColors.BG_DARK
            )
        subtitle.pack(pady=(5, 0))
        
    def create_instructions_card(self, parent):
        """Tạo card hướng dẫn với design hiện đại"""
        if CUSTOM_TK_AVAILABLE:
            card = ctk.CTkFrame(
                parent,
                fg_color=ModernColors.BG_CARD,
                corner_radius=12,
                border_width=1,
                border_color=ModernColors.BORDER
            )
        else:
            card = tk.Frame(
                parent,
                bg=ModernColors.BG_CARD,
                relief=tk.FLAT,
                bd=1,
                highlightbackground=ModernColors.BORDER,
                highlightthickness=1
            )
        card.pack(fill="x", pady=(0, 20))
        
        # Card padding
        card_content = tk.Frame(card, bg=ModernColors.BG_CARD)
        card_content.pack(fill="both", padx=20, pady=20)
        
        # Warning icon và title
        title_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        title_frame.pack(fill="x", pady=(0, 15))
        
        if CUSTOM_TK_AVAILABLE:
            warning_icon = ctk.CTkLabel(
                title_frame,
                text="⚠️",
                font=ctk.CTkFont(size=24)
            )
            warning_icon.pack(side="left", padx=(0, 10))
            
            title_text = ctk.CTkLabel(
                title_frame,
                text="Important Requirements",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=ModernColors.WARNING
            )
            title_text.pack(side="left")
        else:
            warning_icon = tk.Label(
                title_frame,
                text="⚠️",
                font=("Arial", 20),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.WARNING
            )
            warning_icon.pack(side="left", padx=(0, 10))
            
            title_text = tk.Label(
                title_frame,
                text="Important Requirements",
                font=("Segoe UI", 16, "bold"),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.WARNING
            )
            title_text.pack(side="left")
        
        # Instructions với bullet points đẹp
        instructions = [
            ("IMPORTANT", "You must have management access to the YouTube channel to scrape data!", ModernColors.ERROR),
            ("Step 1", "Enter YouTube channel link (supports: @channelname, /c/channel, /channel/UC...)", ModernColors.TEXT_PRIMARY),
            ("Step 2", "Click 'Get Video List' to scan all videos in the channel", ModernColors.TEXT_PRIMARY),
            ("Step 3", "Click 'Start Scraping' to collect analytics data", ModernColors.TEXT_PRIMARY),
            ("Step 4", "Login to YouTube when prompted (first time only)", ModernColors.TEXT_PRIMARY),
            ("Note", "The process may take a few minutes depending on the number of videos", ModernColors.TEXT_SECONDARY)
        ]
        
        for i, (label, text, color) in enumerate(instructions):
            item_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
            item_frame.pack(fill="x", pady=8)
            
            # Bullet point
            if CUSTOM_TK_AVAILABLE:
                bullet = ctk.CTkLabel(
                    item_frame,
                    text="•" if i > 0 else "⚠",
                    font=ctk.CTkFont(size=16),
                    text_color=color,
                    width=20
                )
            else:
                bullet = tk.Label(
                    item_frame,
                    text="•" if i > 0 else "⚠",
                    font=("Arial", 14),
                    bg=ModernColors.BG_CARD,
                    fg=color,
                    width=2
                )
            bullet.pack(side="left")
            
            # Text
            if CUSTOM_TK_AVAILABLE:
                label_widget = ctk.CTkLabel(
                    item_frame,
                    text=f"<{label}> {text}",
                    font=ctk.CTkFont(size=12),
                    text_color=color,
                    anchor="w",
                    justify="left"
                )
            else:
                label_widget = tk.Label(
                    item_frame,
                    text=f"<{label}> {text}",
                    font=("Segoe UI", 11),
                    bg=ModernColors.BG_CARD,
                    fg=color,
                    anchor="w",
                    justify="left"
                )
            label_widget.pack(side="left", fill="x", expand=True)

    def create_account_selector_card(self, parent):
        """
        Tạo card chọn tài khoản - hiển thị danh sách tài khoản đã lưu
        Cho phép chuyển đổi tài khoản mà không cần đăng nhập lại
        """
        if CUSTOM_TK_AVAILABLE:
            card = ctk.CTkFrame(
                parent,
                fg_color=ModernColors.BG_CARD,
                corner_radius=12,
                border_width=1,
                border_color=ModernColors.BORDER
            )
        else:
            card = tk.Frame(
                parent,
                bg=ModernColors.BG_CARD,
                relief=tk.FLAT,
                bd=1,
                highlightbackground=ModernColors.BORDER,
                highlightthickness=1
            )
        card.pack(fill="x", pady=(0, 20))

        card_content = tk.Frame(card, bg=ModernColors.BG_CARD)
        card_content.pack(fill="both", padx=20, pady=20)

        # === TITLE ===
        if CUSTOM_TK_AVAILABLE:
            title = ctk.CTkLabel(
                card_content,
                text="👤 Google Account",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            title = tk.Label(
                card_content,
                text="👤 Google Account",
                font=("Segoe UI", 16, "bold"),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY
            )
        title.pack(anchor="w", pady=(0, 15))

        # === ACCOUNT SELECTOR FRAME ===
        selector_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        selector_frame.pack(fill="x", pady=(0, 10))

        # Label for account dropdown
        if CUSTOM_TK_AVAILABLE:
            account_label = ctk.CTkLabel(
                selector_frame,
                text="Select Account:",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            account_label = tk.Label(
                selector_frame,
                text="Select Account:",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        account_label.pack(side="left", padx=(0, 10))

        # Account dropdown
        if CUSTOM_TK_AVAILABLE:
            self.account_dropdown = ctk.CTkComboBox(
                selector_frame,
                variable=self.account_var,
                values=self.get_account_names(),
                command=self.on_account_changed,
                height=35,
                font=ctk.CTkFont(size=12),
                corner_radius=8,
                state="readonly"
            )
        else:
            self.account_dropdown = ttk.Combobox(
                selector_frame,
                textvariable=self.account_var,
                values=self.get_account_names(),
                font=("Segoe UI", 11),
                state="readonly",
                width=30
            )
            self.account_dropdown.bind("<<ComboboxSelected>>",
                                       lambda e: self.on_account_changed(None))

        self.account_dropdown.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # === ADD NEW ACCOUNT BUTTON ===
        if CUSTOM_TK_AVAILABLE:
            add_account_btn = ctk.CTkButton(
                selector_frame,
                text="➕ New Account",
                command=self.on_add_new_account,
                font=ctk.CTkFont(size=12),
                fg_color=ModernColors.SUCCESS,
                hover_color=ModernColors.PRIMARY_DARK,
                height=35,
                corner_radius=8
            )
        else:
            add_account_btn = tk.Button(
                selector_frame,
                text="➕ New Account",
                command=self.on_add_new_account,
                font=("Segoe UI", 11),
                bg=ModernColors.SUCCESS,
                fg="white",
                padx=12,
                pady=6,
                relief=tk.FLAT,
                bd=0
            )
        add_account_btn.pack(side="right")

        # === SESSION STATUS ===
        status_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        status_frame.pack(fill="x", pady=(10, 0))

        if CUSTOM_TK_AVAILABLE:
            self.account_status_label = ctk.CTkLabel(
                status_frame,
                text="Status: No account selected",
                font=ctk.CTkFont(size=11),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            self.account_status_label = tk.Label(
                status_frame,
                text="Status: No account selected",
                font=("Segoe UI", 10),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        self.account_status_label.pack(anchor="w")

        # Store reference to this card for later updates
        self.account_selector_card = card_content

    def create_batch_account_selector_card(self, parent):
        """
        Tạo card chọn tài khoản cần cào hôm nay
        Hiển thị danh sách toggle switches cho từng tài khoản
        """
        try:
            if CUSTOM_TK_AVAILABLE:
                card = ctk.CTkFrame(
                    parent,
                    fg_color=ModernColors.BG_CARD,
                    corner_radius=12,
                    border_width=1,
                    border_color=ModernColors.BORDER
                )
            else:
                card = tk.Frame(
                    parent,
                    bg=ModernColors.BG_CARD,
                    relief=tk.FLAT,
                    bd=1,
                    highlightbackground=ModernColors.BORDER,
                    highlightthickness=1
                )
            card.pack(fill="x", pady=(0, 20))

            card_content = tk.Frame(card, bg=ModernColors.BG_CARD)
            card_content.pack(fill="both", padx=20, pady=20)

            # === TITLE ===
            if CUSTOM_TK_AVAILABLE:
                title = ctk.CTkLabel(
                    card_content,
                    text="📋 Select Accounts to Scrape Today",
                    font=ctk.CTkFont(size=18, weight="bold"),
                    text_color=ModernColors.TEXT_PRIMARY
                )
            else:
                title = tk.Label(
                    card_content,
                    text="📋 Select Accounts to Scrape Today",
                    font=("Segoe UI", 16, "bold"),
                    bg=ModernColors.BG_CARD,
                    fg=ModernColors.TEXT_PRIMARY
                )
            title.pack(anchor="w", pady=(0, 15))

            # === ACCOUNTS FRAME ===
            accounts_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
            accounts_frame.pack(fill="x", pady=(0, 15))

            # Create a frame to hold all account toggles
            accounts_list_frame = tk.Frame(accounts_frame, bg=ModernColors.BG_CARD)
            accounts_list_frame.pack(fill="x")

            # Load accounts from config
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    accounts = config.get('accounts', [])

                    if accounts:
                        # Create toggle for each account
                        for account in accounts:
                            account_name = account.get('name', 'Unknown')
                            channels = account.get('channels', [])
                            total_videos = sum(len(ch.get('video_ids', [])) for ch in channels)

                            # Create toggle variable
                            if account_name not in self.selected_accounts:
                                self.selected_accounts[account_name] = tk.BooleanVar(value=True)

                            # Create account row frame - use grid for better layout
                            account_row = tk.Frame(accounts_list_frame, bg=ModernColors.BG_CARD)
                            account_row.pack(fill="x", pady=(0, 10))

                            # Toggle checkbox - use grid instead of side=left
                            toggle = tk.Checkbutton(
                                account_row,
                                text=f"✓ {account_name} ({len(channels)} kênh, {total_videos} video)",
                                variable=self.selected_accounts[account_name],
                                font=("Segoe UI", 11),
                                bg=ModernColors.BG_CARD,
                                fg=ModernColors.TEXT_PRIMARY,
                                activebackground=ModernColors.BG_CARD,
                                activeforeground=ModernColors.TEXT_PRIMARY,
                                selectcolor=ModernColors.BG_CARD
                            )
                            toggle.pack(anchor="w")
                            self.batch_scraping_widgets[account_name] = toggle

                    else:
                        no_accounts = tk.Label(
                            accounts_list_frame,
                            text="No accounts found. Please add a new account.",
                            font=("Segoe UI", 10),
                            bg=ModernColors.BG_CARD,
                            fg=ModernColors.TEXT_SECONDARY
                        )
                        no_accounts.pack(anchor="w")
            else:
                no_config = tk.Label(
                    accounts_list_frame,
                    text="config.json not found",
                    font=("Segoe UI", 10),
                    bg=ModernColors.BG_CARD,
                    fg=ModernColors.TEXT_SECONDARY
                )
                no_config.pack(anchor="w")

            # === SELECT ALL / DESELECT ALL BUTTONS ===
            button_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
            button_frame.pack(fill="x", pady=(0, 10))

            select_all_btn = tk.Button(
                button_frame,
                text="✓ Select All",
                command=self.select_all_accounts,
                font=("Segoe UI", 11),
                bg=ModernColors.ACCENT,
                fg="white",
                padx=12,
                pady=6,
                relief=tk.FLAT,
                bd=0
            )
            select_all_btn.pack(side="left", padx=(0, 10))

            deselect_all_btn = tk.Button(
                button_frame,
                text="✗ Bỏ chọn tất cả",
                command=self.deselect_all_accounts,
                font=("Segoe UI", 11),
                bg="#6C757D",
                fg="white",
                padx=12,
                pady=6,
                relief=tk.FLAT,
                bd=0
            )
            deselect_all_btn.pack(side="left")

            # Store reference
            self.batch_selector_card = card_content

        except Exception as e:
            print(f"Error creating batch account selector card: {str(e)}")
            import traceback
            traceback.print_exc()

    def refresh_batch_account_selector(self):
        """
        Refresh the batch account selector card to show updated accounts
        Called after adding new account to show it in the selector
        """
        try:
            # Remove old card if it exists
            if hasattr(self, 'batch_selector_card') and self.batch_selector_card:
                self.batch_selector_card.destroy()

            # Clear account widgets and variables
            self.batch_scraping_widgets.clear()
            self.selected_accounts.clear()

            # Find the parent frame where batch selector was
            # Need to recreate in the right position
            if hasattr(self, 'main_frame'):
                # Recreate the batch selector with updated accounts from config
                self.create_batch_account_selector_card(self.main_frame)

                # Update the view
                self.root.update()
                self.log_message("✓ Đã làm mới danh sách tài khoản", "INFO")
            else:
                self.log_message("⚠ Không tìm thấy main_frame để làm mới selector", "WARNING")
        except Exception as e:
            self.log_message(f"Lỗi làm mới danh sách tài khoản: {str(e)}", "ERROR")

    def update_text_widget(self, text_widget, content):
        """Helper function to update disabled text widget"""
        try:
            text_widget.configure(state=tk.NORMAL)
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", content)
            text_widget.configure(state=tk.DISABLED)
        except:
            pass

    def select_all_accounts(self):
        """Chọn tất cả tài khoản"""
        for account_var in self.selected_accounts.values():
            account_var.set(True)
        self.log_message("✓ Đã chọn tất cả tài khoản", "INFO")

    def deselect_all_accounts(self):
        """Bỏ chọn tất cả tài khoản"""
        for account_var in self.selected_accounts.values():
            account_var.set(False)
        self.log_message("✗ Đã bỏ chọn tất cả tài khoản", "INFO")

    # ==================== NEW WORKFLOW METHODS ====================
    
    def create_accounts_overview_card(self, parent):
        """
        Create accounts overview card at the top
        Shows all accounts with their channels and videos
        Allows selection for scraping
        """
        if CUSTOM_TK_AVAILABLE:
            card = ctk.CTkFrame(
                parent,
                fg_color=ModernColors.BG_CARD,
                corner_radius=12,
                border_width=1,
                border_color=ModernColors.BORDER
            )
        else:
            card = tk.Frame(
                parent,
                bg=ModernColors.BG_CARD,
                relief=tk.FLAT,
                bd=1,
                highlightbackground=ModernColors.BORDER,
                highlightthickness=1
            )
        card.pack(fill="x", pady=(0, 20))

        card_content = tk.Frame(card, bg=ModernColors.BG_CARD)
        card_content.pack(fill="both", padx=20, pady=20)

        # === TITLE ===
        if CUSTOM_TK_AVAILABLE:
            title = ctk.CTkLabel(
                card_content,
                text="📊 ACCOUNTS OVERVIEW",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            title = tk.Label(
                card_content,
                text="📊 ACCOUNTS OVERVIEW",
                font=("Segoe UI", 16, "bold"),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY
            )
        title.pack(anchor="w", pady=(0, 15))

        # === ACCOUNTS LIST FRAME ===
        accounts_list_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        accounts_list_frame.pack(fill="x", pady=(0, 15))

        # Load and display accounts
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    accounts = config.get('accounts', [])

                    if accounts:
                        for account in accounts:
                            account_name = account.get('name', 'Unknown')
                            channels = account.get('channels', [])
                            total_videos = sum(len(ch.get('video_ids', [])) for ch in channels)

                            # Create toggle variable if not exists
                            if account_name not in self.selected_accounts:
                                self.selected_accounts[account_name] = tk.BooleanVar(value=True)

                            # Account row frame
                            account_row = tk.Frame(accounts_list_frame, bg=ModernColors.BG_CARD)
                            account_row.pack(fill="x", pady=(0, 10))

                            # Checkbox for account
                            account_checkbox = tk.Checkbutton(
                                account_row,
                                text=f"☑️ {account_name} ({len(channels)} channels, {total_videos} videos)",
                                variable=self.selected_accounts[account_name],
                                font=("Segoe UI", 12, "bold"),
                                bg=ModernColors.BG_CARD,
                                fg=ModernColors.TEXT_PRIMARY,
                                activebackground=ModernColors.BG_CARD,
                                activeforeground=ModernColors.TEXT_PRIMARY,
                                selectcolor=ModernColors.BG_CARD
                            )
                            account_checkbox.pack(anchor="w")

                            # Channels list (indented)
                            if channels:
                                channels_frame = tk.Frame(account_row, bg=ModernColors.BG_CARD)
                                channels_frame.pack(fill="x", padx=(30, 0))

                                for channel in channels:
                                    channel_url = channel.get('url', 'Unknown')
                                    video_ids = channel.get('video_ids', [])
                                    
                                    # Extract channel name from URL
                                    channel_name = channel_url.split('/')[-1] if channel_url != 'Unknown' else 'Unknown'
                                    
                                    channel_label = tk.Label(
                                        channels_frame,
                                        text=f"  ├─ {channel_name} ({len(video_ids)} videos)",
                                        font=("Segoe UI", 10),
                                        bg=ModernColors.BG_CARD,
                                        fg=ModernColors.TEXT_SECONDARY,
                                        anchor="w"
                                    )
                                    channel_label.pack(anchor="w")

                            self.batch_scraping_widgets[account_name] = account_checkbox

                    else:
                        no_accounts = tk.Label(
                            accounts_list_frame,
                            text="Không có tài khoản nào. Vui lòng tạo tài khoản mới bên dưới.",
                            font=("Segoe UI", 11),
                            bg=ModernColors.BG_CARD,
                            fg=ModernColors.TEXT_SECONDARY
                        )
                        no_accounts.pack(anchor="w")
            else:
                no_config = tk.Label(
                    accounts_list_frame,
                    text="Không tìm thấy config.json. Hệ thống sẽ tạo tự động khi bạn thêm tài khoản.",
                    font=("Segoe UI", 11),
                    bg=ModernColors.BG_CARD,
                    fg=ModernColors.TEXT_SECONDARY
                )
                no_config.pack(anchor="w")

        except Exception as e:
            error_label = tk.Label(
                accounts_list_frame,
                text=f"Lỗi khi load accounts: {str(e)}",
                font=("Segoe UI", 10),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.ERROR
            )
            error_label.pack(anchor="w")

        # === BUTTONS FRAME ===
        buttons_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        buttons_frame.pack(fill="x", pady=(0, 10))

        # Select All button
        select_all_btn = tk.Button(
            buttons_frame,
            text="✓ Select All",
            command=self.select_all_accounts,
            font=("Segoe UI", 11),
            bg=ModernColors.ACCENT,
            fg="white",
            padx=15,
            pady=8,
            relief=tk.FLAT,
            bd=0
        )
        select_all_btn.pack(side="left", padx=(0, 10))

        # Deselect All button
        deselect_all_btn = tk.Button(
            buttons_frame,
            text="✗ Deselect All",
            command=self.deselect_all_accounts,
            font=("Segoe UI", 11),
            bg="#6C757D",
            fg="white",
            padx=15,
            pady=8,
            relief=tk.FLAT,
            bd=0
        )
        deselect_all_btn.pack(side="left", padx=(0, 15))

        # Scrape Selected button - LARGER and more prominent
        scrape_selected_btn = tk.Button(
            buttons_frame,
            text="🚀 Scrape Selected Accounts",
            command=self.start_batch_scraping,
            font=("Segoe UI", 14, "bold"),
            bg=ModernColors.SUCCESS,
            fg="white",
            padx=30,
            pady=15,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2"
        )
        scrape_selected_btn.pack(side="left")

        # Store reference
        self.accounts_overview_frame = card_content

    def create_channel_management_card(self, parent):
        """
        Create channel management card
        Allows adding multiple channels to selected account before fetching
        """
        if CUSTOM_TK_AVAILABLE:
            card = ctk.CTkFrame(
                parent,
                fg_color=ModernColors.BG_CARD,
                corner_radius=12,
                border_width=1,
                border_color=ModernColors.BORDER
            )
        else:
            card = tk.Frame(
                parent,
                bg=ModernColors.BG_CARD,
                relief=tk.FLAT,
                bd=1,
                highlightbackground=ModernColors.BORDER,
                highlightthickness=1
            )
        card.pack(fill="x", pady=(0, 20))

        card_content = tk.Frame(card, bg=ModernColors.BG_CARD)
        card_content.pack(fill="both", padx=20, pady=20)

        # === TITLE ===
        if CUSTOM_TK_AVAILABLE:
            title = ctk.CTkLabel(
                card_content,
                text="📹 ADD CHANNELS",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            title = tk.Label(
                card_content,
                text="📹 ADD CHANNELS",
                font=("Segoe UI", 16, "bold"),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY
            )
        title.pack(anchor="w", pady=(0, 15))

        # === STATUS LABEL (shows which account we're adding to) ===
        self.channel_management_status = tk.Label(
            card_content,
            text="Please select an account above first",
            font=("Segoe UI", 11, "italic"),
            bg=ModernColors.BG_CARD,
            fg=ModernColors.TEXT_SECONDARY
        )
        self.channel_management_status.pack(anchor="w", pady=(0, 15))

        # === INPUT FRAME ===
        input_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        input_frame.pack(fill="x", pady=(0, 15))

        # Channel URL label
        url_label = tk.Label(
            input_frame,
            text="Channel URL:",
            font=("Segoe UI", 11),
            bg=ModernColors.BG_CARD,
            fg=ModernColors.TEXT_SECONDARY
        )
        url_label.pack(anchor="w", pady=(0, 8))

        # Channel URL entry
        if CUSTOM_TK_AVAILABLE:
            self.channel_url_entry = ctk.CTkEntry(
                input_frame,
                placeholder_text="https://www.youtube.com/@channelname",
                height=42,
                font=ctk.CTkFont(size=13),
                border_width=2,
                corner_radius=8
            )
        else:
            self.channel_url_entry = tk.Entry(
                input_frame,
                font=("Segoe UI", 12),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY,
                relief=tk.FLAT,
                bd=10,
                highlightthickness=2,
                highlightbackground=ModernColors.BORDER
            )
        self.channel_url_entry.pack(fill="x", pady=(0, 10))

        # Add Channel button
        add_channel_btn = tk.Button(
            input_frame,
            text="➕ Add to Account",
            command=self.add_channel_to_pending,
            font=("Segoe UI", 11, "bold"),
            bg=ModernColors.ACCENT,
            fg="white",
            padx=15,
            pady=8,
            relief=tk.FLAT,
            bd=0
        )
        add_channel_btn.pack(anchor="w")

        # === PENDING CHANNELS LIST ===
        pending_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        pending_frame.pack(fill="x", pady=(15, 0))

        pending_title = tk.Label(
            pending_frame,
            text="Channels to fetch:",
            font=("Segoe UI", 11, "bold"),
            bg=ModernColors.BG_CARD,
            fg=ModernColors.TEXT_PRIMARY
        )
        pending_title.pack(anchor="w", pady=(0, 10))

        # Scrollable frame for pending channels
        self.pending_channels_list_frame = tk.Frame(pending_frame, bg=ModernColors.BG_CARD)
        self.pending_channels_list_frame.pack(fill="x")

        # Get All Videos button - LARGER and more prominent
        self.get_all_videos_btn = tk.Button(
            card_content,
            text="📥 Get All Videos",
            command=self.fetch_all_pending_channels,
            font=("Segoe UI", 14, "bold"),
            bg=ModernColors.SUCCESS,
            fg="white",
            padx=30,
            pady=15,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            state=tk.DISABLED  # Disabled until channels are added
        )
        self.get_all_videos_btn.pack(anchor="w", pady=(20, 0))

        # Store reference
        self.channel_management_frame = card_content
        
        # Update status based on selected account
        self.update_channel_management_status()

    def update_channel_management_status(self):
        """Update the status label in channel management card"""
        selected_account = self.account_var.get()
        if selected_account and selected_account != "":
            self.channel_management_status.config(
                text=f"Adding channels to: {selected_account}",
                fg=ModernColors.SUCCESS,
                font=("Segoe UI", 11, "bold")
            )
        else:
            self.channel_management_status.config(
                text="Please select an account above first",
                fg=ModernColors.TEXT_SECONDARY,
                font=("Segoe UI", 11, "italic")
            )

    def add_channel_to_pending(self):
        """Add channel URL to pending list"""
        channel_url = self.channel_url_entry.get().strip()
        
        if not channel_url:
            self.log_message("⚠ Please enter a channel URL", "WARNING")
            return
        
        # Check if account is selected
        selected_account = self.account_var.get()
        if not selected_account or selected_account == "":
            self.log_message("⚠ Please select an account first", "WARNING")
            return
        
        # Check if already in pending list
        if channel_url in self.pending_channels:
            self.log_message(f"⚠ Channel already in pending list: {channel_url}", "WARNING")
            return
        
        # Add to pending list
        self.pending_channels.append(channel_url)
        self.log_message(f"✓ Added to pending list: {channel_url}", "SUCCESS")
        
        # Update UI
        self.refresh_pending_channels_list()
        
        # Clear input
        self.channel_url_entry.delete(0, tk.END)
        
        # Enable "Get All Videos" button
        if len(self.pending_channels) > 0:
            self.get_all_videos_btn.config(state=tk.NORMAL)

    def remove_pending_channel(self, channel_url):
        """Remove channel from pending list"""
        if channel_url in self.pending_channels:
            self.pending_channels.remove(channel_url)
            self.log_message(f"✓ Removed from pending list: {channel_url}", "INFO")
            self.refresh_pending_channels_list()
            
            # Disable button if no pending channels
            if len(self.pending_channels) == 0:
                self.get_all_videos_btn.config(state=tk.DISABLED)

    def refresh_pending_channels_list(self):
        """Refresh the pending channels list UI"""
        # Clear existing widgets
        for widget in self.pending_channels_list_frame.winfo_children():
            widget.destroy()
        
        # Display pending channels
        if len(self.pending_channels) == 0:
            no_channels = tk.Label(
                self.pending_channels_list_frame,
                text="No channels added yet",
                font=("Segoe UI", 10),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
            no_channels.pack(anchor="w")
        else:
            for channel_url in self.pending_channels:
                channel_row = tk.Frame(self.pending_channels_list_frame, bg=ModernColors.BG_CARD)
                channel_row.pack(fill="x", pady=(0, 5))
                
                # Channel URL label
                channel_label = tk.Label(
                    channel_row,
                    text=f"  • {channel_url}",
                    font=("Segoe UI", 10),
                    bg=ModernColors.BG_CARD,
                    fg=ModernColors.TEXT_PRIMARY,
                    anchor="w"
                )
                channel_label.pack(side="left", fill="x", expand=True)
                
                # Remove button
                remove_btn = tk.Button(
                    channel_row,
                    text="🗑️",
                    command=lambda url=channel_url: self.remove_pending_channel(url),
                    font=("Segoe UI", 10),
                    bg=ModernColors.ERROR,
                    fg="white",
                    padx=8,
                    pady=2,
                    relief=tk.FLAT,
                    bd=0
                )
                remove_btn.pack(side="right")
        
        # Update count in button text
        count = len(self.pending_channels)
        self.get_all_videos_btn.config(
            text=f"📥 Get All Videos ({count} channel{'s' if count != 1 else ''})"
        )

    def fetch_all_pending_channels(self):
        """Fetch videos for all pending channels"""
        if len(self.pending_channels) == 0:
            self.log_message("⚠ No channels to fetch", "WARNING")
            return
        
        selected_account = self.account_var.get()
        if not selected_account or selected_account == "":
            self.log_message("⚠ Please select an account first", "WARNING")
            return
        
        self.log_message(f"🚀 Starting to fetch videos for {len(self.pending_channels)} channels...", "INFO")
        
        # Start fetching in a thread
        def fetch_thread():
            try:
                total = len(self.pending_channels)
                for i, channel_url in enumerate(self.pending_channels, 1):
                    self.log_message(f"📥 Fetching channel {i}/{total}: {channel_url}", "INFO")
                    
                    # Update progress
                    progress = (i / total) * 100
                    self.update_progress(progress, f"Fetching channel {i}/{total}...")
                    
                    # Fetch video IDs using existing function
                    try:
                        from src.scraper.channel import get_channel_video_ids, save_to_config
                        
                        video_ids = get_channel_video_ids(channel_url)
                        
                        if video_ids:
                            self.log_message(f"✓ Found {len(video_ids)} videos in {channel_url}", "SUCCESS")
                            
                            # Get cookies file for this account (sanitize name)
                            safe_account_name = re.sub(r'[^\w\-_]', '_', selected_account)
                            cookies_file = f"profile/youtube_cookies_{safe_account_name}.json"
                            
                            # Save to config
                            save_to_config(
                                channel_url=channel_url,
                                video_ids=video_ids,
                                cookies_file=cookies_file
                            )
                            
                            self.log_message(f"✓ Saved to account: {selected_account}", "SUCCESS")
                        else:
                            self.log_message(f"⚠ No videos found in {channel_url}", "WARNING")
                    
                    except Exception as e:
                        self.log_message(f"✗ Error fetching {channel_url}: {str(e)}", "ERROR")
                
                # Clear pending list
                self.pending_channels.clear()
                self.root.after(0, self.refresh_pending_channels_list)
                
                # Refresh accounts overview
                self.root.after(0, self.refresh_accounts_overview)
                
                # Reset progress
                self.update_progress(100, "All channels fetched!")
                self.log_message("✓ All channels fetched successfully!", "SUCCESS")
                
            except Exception as e:
                self.log_message(f"✗ Error in fetch thread: {str(e)}", "ERROR")
                import traceback
                traceback.print_exc()
        
        # Start thread
        import threading
        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()

    def refresh_accounts_overview(self):
        """Refresh the accounts overview card"""
        try:
            # Destroy old overview
            if self.accounts_overview_frame:
                parent = self.accounts_overview_frame.master
                parent.destroy()
            
            # Recreate at the same position
            # Find position in main_frame
            if hasattr(self, 'main_frame'):
                # Recreate the overview card
                self.create_accounts_overview_card(self.main_frame)
                
                # Force update
                self.root.update()
                self.log_message("✓ Refreshed accounts overview", "INFO")
        except Exception as e:
            self.log_message(f"⚠ Error refreshing overview: {str(e)}", "WARNING")

    def start_batch_scraping(self):
        """Start scraping for selected accounts"""
        # Get selected accounts
        selected = [name for name, var in self.selected_accounts.items() if var.get()]
        
        if not selected:
            self.log_message("⚠ No accounts selected for scraping", "WARNING")
            return
        
        self.log_message(f"🚀 Starting batch scraping for {len(selected)} account(s)...", "INFO")
        
        # Use existing scraping logic
        # This will be implemented using the existing start_scraping method
        # For now, just log
        for account_name in selected:
            self.log_message(f"  → {account_name}", "INFO")
        
        self.log_message("ℹ Batch scraping will be implemented using existing scraping logic", "INFO")



    def create_input_card(self, parent):
        """Tạo card nhập liệu - MODIFIED cho multi-account support"""
        if CUSTOM_TK_AVAILABLE:
            card = ctk.CTkFrame(
                parent,
                fg_color=ModernColors.BG_CARD,
                corner_radius=12,
                border_width=1,
                border_color=ModernColors.BORDER
            )
        else:
            card = tk.Frame(
                parent,
                bg=ModernColors.BG_CARD,
                relief=tk.FLAT,
                bd=1,
                highlightbackground=ModernColors.BORDER,
                highlightthickness=1
            )
        card.pack(fill="x", pady=(0, 20))

        card_content = tk.Frame(card, bg=ModernColors.BG_CARD)
        card_content.pack(fill="both", padx=20, pady=20)

        # Title
        if CUSTOM_TK_AVAILABLE:
            title = ctk.CTkLabel(
                card_content,
                text="🔗 Kênh YouTube",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            title = tk.Label(
                card_content,
                text="🔗 Kênh YouTube",
                font=("Segoe UI", 16, "bold"),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY
            )
        title.pack(anchor="w", pady=(0, 15))

        # === MODE SELECTION: Select from existing vs Add new ===
        if CUSTOM_TK_AVAILABLE:
            mode_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
            mode_frame.pack(fill="x", pady=(0, 15))

            existing_radio = ctk.CTkRadioButton(
                mode_frame,
                text="Chọn từ kênh đã lưu",
                variable=self.channel_mode_var,
                value="existing",
                command=self.on_channel_mode_changed,
                font=ctk.CTkFont(size=12)
            )
            existing_radio.pack(side="left", padx=(0, 20))

            new_radio = ctk.CTkRadioButton(
                mode_frame,
                text="Thêm kênh mới",
                variable=self.channel_mode_var,
                value="new",
                command=self.on_channel_mode_changed,
                font=ctk.CTkFont(size=12)
            )
            new_radio.pack(side="left")

        # === SECTION 1: SELECT FROM EXISTING CHANNELS ===
        self.existing_channel_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        self.existing_channel_frame.pack(fill="x", pady=(0, 10))

        if CUSTOM_TK_AVAILABLE:
            channel_label = ctk.CTkLabel(
                self.existing_channel_frame,
                text="Kênh:",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            channel_label = tk.Label(
                self.existing_channel_frame,
                text="Kênh:",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        channel_label.pack(side="left", padx=(0, 10))

        if CUSTOM_TK_AVAILABLE:
            self.channel_dropdown = ctk.CTkComboBox(
                self.existing_channel_frame,
                variable=self.channel_var,
                values=[],
                command=self.on_channel_changed,
                height=35,
                font=ctk.CTkFont(size=12),
                corner_radius=8,
                state="readonly"
            )
        else:
            self.channel_dropdown = ttk.Combobox(
                self.existing_channel_frame,
                textvariable=self.channel_var,
                values=[],
                font=("Segoe UI", 11),
                state="readonly",
                width=50
            )
            self.channel_dropdown.bind("<<ComboboxSelected>>",
                                       lambda e: self.on_channel_changed(None))

        self.channel_dropdown.pack(side="left", fill="x", expand=True)

        # === SECTION 2: ADD NEW CHANNEL ===
        self.new_channel_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        # Initially hidden

        if CUSTOM_TK_AVAILABLE:
            url_label = ctk.CTkLabel(
                self.new_channel_frame,
                text="Link kênh:",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            url_label = tk.Label(
                self.new_channel_frame,
                text="Link kênh:",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        url_label.pack(anchor="w", pady=(0, 8))

        if CUSTOM_TK_AVAILABLE:
            self.url_entry = ctk.CTkEntry(
                self.new_channel_frame,
                placeholder_text="https://www.youtube.com/@channelname",
                height=42,
                font=ctk.CTkFont(size=13),
                border_width=2,
                corner_radius=8,
                fg_color=ModernColors.BG_CARD,
                border_color=ModernColors.BORDER,
                text_color=ModernColors.TEXT_PRIMARY,
                placeholder_text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            self.url_entry = tk.Entry(
                self.new_channel_frame,
                font=("Segoe UI", 12),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY,
                insertbackground=ModernColors.TEXT_PRIMARY,
                relief=tk.FLAT,
                bd=10,
                highlightthickness=2,
                highlightbackground=ModernColors.BORDER,
                highlightcolor=ModernColors.PRIMARY
            )

        self.url_entry.pack(fill="x", pady=(0, 10))

        # Example formats
        if CUSTOM_TK_AVAILABLE:
            example = ctk.CTkLabel(
                self.new_channel_frame,
                text="💡 Định dạng: @channelname, /c/channelname, /channel/UCxxxxx",
                font=ctk.CTkFont(size=11),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            example = tk.Label(
                self.new_channel_frame,
                text="💡 Định dạng: @channelname, /c/channelname, /channel/UCxxxxx",
                font=("Segoe UI", 10),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        example.pack(anchor="w", pady=(0, 15))

        # === MAX RESULTS (for both modes) ===
        options_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        options_frame.pack(fill="x")

        if CUSTOM_TK_AVAILABLE:
            max_label = ctk.CTkLabel(
                options_frame,
                text="Giới hạn số video (tùy chọn):",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY
            )
            max_label.pack(side="left")

            self.max_results_entry = ctk.CTkEntry(
                options_frame,
                width=120,
                height=35,
                placeholder_text="Để trống = tất cả",
                font=ctk.CTkFont(size=12),
                corner_radius=8
            )
            self.max_results_entry.pack(side="right")
        else:
            max_label = tk.Label(
                options_frame,
                text="Giới hạn số video (tùy chọn):",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
            max_label.pack(side="left")

            self.max_results_entry = tk.Entry(
                options_frame,
                width=15,
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY,
                relief=tk.FLAT,
                bd=8
            )
            self.max_results_entry.pack(side="right")

        # Show "existing" mode by default
        self.on_channel_mode_changed()

    def create_channel_info_card(self, parent):
        """Tạo card hiển thị thông tin kênh và danh sách video"""
        if CUSTOM_TK_AVAILABLE:
            card = ctk.CTkFrame(
                parent,
                fg_color=ModernColors.BG_CARD,
                corner_radius=12,
                border_width=1,
                border_color=ModernColors.BORDER
            )
        else:
            card = tk.Frame(
                parent,
                bg=ModernColors.BG_CARD,
                relief=tk.FLAT,
                bd=1,
                highlightbackground=ModernColors.BORDER,
                highlightthickness=1
            )
        card.pack(fill="x", pady=(0, 20))
        
        card_content = tk.Frame(card, bg=ModernColors.BG_CARD)
        card_content.pack(fill="both", padx=20, pady=20)
        
        # Title
        if CUSTOM_TK_AVAILABLE:
            title = ctk.CTkLabel(
                card_content,
                text="📺 Thông tin kênh đã chọn",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            title = tk.Label(
                card_content,
                text="📺 Thông tin kênh đã chọn",
                font=("Segoe UI", 16, "bold"),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY
            )
        title.pack(anchor="w", pady=(0, 15))
        
        # Channel URL display
        if CUSTOM_TK_AVAILABLE:
            self.channel_url_label = ctk.CTkLabel(
                card_content,
                text="Kênh: Chưa chọn kênh",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY,
                anchor="w",
                justify="left"
            )
        else:
            self.channel_url_label = tk.Label(
                card_content,
                text="Kênh: Chưa chọn kênh",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY,
                anchor="w",
                justify="left"
            )
        self.channel_url_label.pack(fill="x", pady=(0, 8))
        
        # Video count display
        if CUSTOM_TK_AVAILABLE:
            self.video_count_label = ctk.CTkLabel(
                card_content,
                text="Số lượng video: 0",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY,
                anchor="w",
                justify="left"
            )
        else:
            self.video_count_label = tk.Label(
                card_content,
                text="Số lượng video: 0",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY,
                anchor="w",
                justify="left"
            )
        self.video_count_label.pack(fill="x", pady=(0, 10))
        
        # Thông tin kênh đã cấu hình
        info_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        info_frame.pack(fill="x", pady=(0, 10))
        
        if CUSTOM_TK_AVAILABLE:
            info_title = ctk.CTkLabel(
                info_frame,
                text="Thông tin kênh đã cấu hình:",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            info_title = tk.Label(
                info_frame,
                text="Thông tin kênh đã cấu hình:",
                font=("Segoe UI", 10, "bold"),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY
            )
        info_title.pack(anchor="w", pady=(0, 8))
        
        # Hiển thị thông tin kênh chi tiết
        if CUSTOM_TK_AVAILABLE:
            self.channel_info_text = ctk.CTkTextbox(
                info_frame,
                height=100,
                font=ctk.CTkFont(size=11),
                fg_color=ModernColors.SECONDARY,
                text_color=ModernColors.TEXT_PRIMARY,
                corner_radius=8,
                border_width=2,
                border_color=ModernColors.BORDER,
                wrap="word"
            )
        else:
            text_container = tk.Frame(info_frame, bg=ModernColors.BG_CARD)
            text_container.pack(fill="both", expand=True)
            
            self.channel_info_text = scrolledtext.ScrolledText(
                text_container,
                height=5,
                font=("Segoe UI", 10),
                wrap=tk.WORD,
                bg=ModernColors.SECONDARY,
                fg=ModernColors.TEXT_PRIMARY,
                insertbackground=ModernColors.TEXT_PRIMARY,
                selectbackground=ModernColors.PRIMARY,
                relief=tk.FLAT,
                bd=10,
                highlightthickness=2,
                highlightbackground=ModernColors.BORDER,
                highlightcolor=ModernColors.BORDER,
                state=tk.DISABLED  # FIX: Make read-only
            )
        self.channel_info_text.pack(fill="both", expand=True)
            
    def create_auto_scraping_card(self, parent):
        """Tạo card chế độ tự động cào dữ liệu"""
        if CUSTOM_TK_AVAILABLE:
            card = ctk.CTkFrame(
                parent,
                fg_color=ModernColors.BG_CARD,
                corner_radius=12,
                border_width=1,
                border_color=ModernColors.BORDER
            )
        else:
            card = tk.Frame(
                parent,
                bg=ModernColors.BG_CARD,
                relief=tk.FLAT,
                bd=1,
                highlightbackground=ModernColors.BORDER,
                highlightthickness=1
            )
        card.pack(fill="x", pady=(0, 20))
        
        card_content = tk.Frame(card, bg=ModernColors.BG_CARD)
        card_content.pack(fill="both", padx=20, pady=20)
        
        # Title
        if CUSTOM_TK_AVAILABLE:
            title = ctk.CTkLabel(
                card_content,
                text="⏰ Chế độ tự động cào dữ liệu",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            title = tk.Label(
                card_content,
                text="⏰ Chế độ tự động cào dữ liệu",
                font=("Segoe UI", 16, "bold"),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY
            )
        title.pack(anchor="w", pady=(0, 15))
        
        # Checkbox và controls frame
        controls_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        controls_frame.pack(fill="x")
        
        # Checkbox để bật/tắt (mặc định bật)
        if CUSTOM_TK_AVAILABLE:
            self.auto_scraping_var = tk.BooleanVar(value=True)
            self.auto_scraping_checkbox = ctk.CTkCheckBox(
                controls_frame,
                text="Bật chế độ tự động",
                variable=self.auto_scraping_var,
                command=self.toggle_auto_scraping,
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            self.auto_scraping_var = tk.BooleanVar(value=True)
            self.auto_scraping_checkbox = tk.Checkbutton(
                controls_frame,
                text="Bật chế độ tự động",
                variable=self.auto_scraping_var,
                command=self.toggle_auto_scraping,
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY,
                activebackground=ModernColors.BG_CARD,
                activeforeground=ModernColors.TEXT_PRIMARY,
                selectcolor=ModernColors.BG_CARD
            )
        self.auto_scraping_checkbox.pack(side="left", padx=(0, 20))
        
        # Interval input
        interval_frame = tk.Frame(controls_frame, bg=ModernColors.BG_CARD)
        interval_frame.pack(side="left", padx=(0, 20))
        
        if CUSTOM_TK_AVAILABLE:
            interval_label = ctk.CTkLabel(
                interval_frame,
                text="Cào mỗi:",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            interval_label = tk.Label(
                interval_frame,
                text="Cào mỗi:",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        interval_label.pack(side="left", padx=(0, 8))
        
        if CUSTOM_TK_AVAILABLE:
            self.auto_interval_entry = ctk.CTkEntry(
                interval_frame,
                width=80,
                height=35,
                placeholder_text="30",
                font=ctk.CTkFont(size=12),
                corner_radius=8
            )
            self.auto_interval_entry.insert(0, "30")
        else:
            self.auto_interval_entry = tk.Entry(
                interval_frame,
                width=10,
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY,
                relief=tk.FLAT,
                bd=8
            )
            self.auto_interval_entry.insert(0, "30")
        self.auto_interval_entry.pack(side="left", padx=(0, 8))
        
        if CUSTOM_TK_AVAILABLE:
            minutes_label = ctk.CTkLabel(
                interval_frame,
                text="phút",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            minutes_label = tk.Label(
                interval_frame,
                text="phút",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        minutes_label.pack(side="left")
        
        # Min interval input (chỉ cào lại video đã cào cách đây >= X giờ)
        interval_hours_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        interval_hours_frame.pack(fill="x", pady=(10, 0))
        
        if CUSTOM_TK_AVAILABLE:
            interval_hours_label = ctk.CTkLabel(
                interval_hours_frame,
                text="Chỉ cào lại video đã cào cách đây ≥",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            interval_hours_label = tk.Label(
                interval_hours_frame,
                text="Chỉ cào lại video đã cào cách đây ≥",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        interval_hours_label.pack(side="left", padx=(0, 8))
        
        if CUSTOM_TK_AVAILABLE:
            self.min_interval_hours_entry = ctk.CTkEntry(
                interval_hours_frame,
                width=60,
                height=35,
                placeholder_text="24",
                font=ctk.CTkFont(size=12),
                corner_radius=8
            )
            self.min_interval_hours_entry.insert(0, "24")
        else:
            self.min_interval_hours_entry = tk.Entry(
                interval_hours_frame,
                width=8,
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY,
                relief=tk.FLAT,
                bd=8
            )
            self.min_interval_hours_entry.insert(0, "24")
        self.min_interval_hours_entry.pack(side="left", padx=(0, 8))
        
        if CUSTOM_TK_AVAILABLE:
            hours_label = ctk.CTkLabel(
                interval_hours_frame,
                text="giờ (0 = cào tất cả)",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            hours_label = tk.Label(
                interval_hours_frame,
                text="giờ (0 = cào tất cả)",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        hours_label.pack(side="left")
        
        # Status label để hiển thị thời gian chạy tiếp theo
        if CUSTOM_TK_AVAILABLE:
            self.auto_status_label = ctk.CTkLabel(
                card_content,
                text="Trạng thái: Tắt",
                font=ctk.CTkFont(size=12),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            self.auto_status_label = tk.Label(
                card_content,
                text="Trạng thái: Tắt",
                font=("Segoe UI", 10),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        self.auto_status_label.pack(anchor="w", pady=(10, 0))

    def create_login_settings_card(self, parent):
        """Tạo card cài đặt đăng nhập Google"""
        if CUSTOM_TK_AVAILABLE:
            card = ctk.CTkFrame(
                parent,
                fg_color=ModernColors.BG_CARD,
                corner_radius=12,
                border_width=1,
                border_color=ModernColors.BORDER
            )
        else:
            card = tk.Frame(
                parent,
                bg=ModernColors.BG_CARD,
                relief=tk.FLAT,
                bd=1,
                highlightbackground=ModernColors.BORDER,
                highlightthickness=1
            )
        card.pack(fill="x", pady=(0, 20))

        card_content = tk.Frame(card, bg=ModernColors.BG_CARD)
        card_content.pack(fill="both", padx=20, pady=20)

        # Title
        if CUSTOM_TK_AVAILABLE:
            title = ctk.CTkLabel(
                card_content,
                text="🔐 Google Login Settings",
                font=ctk.CTkFont(size=18, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            title = tk.Label(
                card_content,
                text="🔐 Google Login Settings",
                font=("Segoe UI", 16, "bold"),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY
            )
        title.pack(anchor="w", pady=(0, 15))

        # Checkbox và controls frame
        controls_frame = tk.Frame(card_content, bg=ModernColors.BG_CARD)
        controls_frame.pack(fill="x")

        # Checkbox để bật/tắt auto continue
        if CUSTOM_TK_AVAILABLE:
            self.auto_continue_var = tk.BooleanVar(value=self.auto_continue)
            self.auto_continue_checkbox = ctk.CTkCheckBox(
                controls_frame,
                text="Auto-continue after login",
                variable=self.auto_continue_var,
                command=self.toggle_auto_continue,
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            self.auto_continue_var = tk.BooleanVar(value=self.auto_continue)
            self.auto_continue_checkbox = tk.Checkbutton(
                controls_frame,
                text="Auto-continue after login",
                variable=self.auto_continue_var,
                command=self.toggle_auto_continue,
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY,
                activebackground=ModernColors.BG_CARD,
                activeforeground=ModernColors.TEXT_PRIMARY,
                selectcolor=ModernColors.BG_CARD
            )
        self.auto_continue_checkbox.pack(side="left", padx=(0, 20))

        # Wait time input
        wait_frame = tk.Frame(controls_frame, bg=ModernColors.BG_CARD)
        wait_frame.pack(side="left", padx=(0, 20))

        if CUSTOM_TK_AVAILABLE:
            wait_label = ctk.CTkLabel(
                wait_frame,
                text="Wait time:",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            wait_label = tk.Label(
                wait_frame,
                text="Wait time:",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        wait_label.pack(side="left", padx=(0, 8))

        if CUSTOM_TK_AVAILABLE:
            self.wait_time_entry = ctk.CTkEntry(
                wait_frame,
                width=80,
                height=35,
                placeholder_text="30",
                font=ctk.CTkFont(size=12),
                corner_radius=8
            )
            self.wait_time_entry.insert(0, str(self.wait_time))
        else:
            self.wait_time_entry = tk.Entry(
                wait_frame,
                width=10,
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY,
                relief=tk.FLAT,
                bd=8
            )
            self.wait_time_entry.insert(0, str(self.wait_time))
        self.wait_time_entry.pack(side="left", padx=(0, 8))

        if CUSTOM_TK_AVAILABLE:
            seconds_label = ctk.CTkLabel(
                wait_frame,
                text="seconds",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            seconds_label = tk.Label(
                wait_frame,
                text="seconds",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        seconds_label.pack(side="left")

        # Description
        if CUSTOM_TK_AVAILABLE:
            desc_label = ctk.CTkLabel(
                card_content,
                text="When enabled, script will auto-continue after wait time instead of asking to press Enter",
                font=ctk.CTkFont(size=12),
                text_color=ModernColors.TEXT_SECONDARY,
                wraplength=600
            )
        else:
            desc_label = tk.Label(
                card_content,
                text="When enabled, script will auto-continue after wait time instead of asking to press Enter",
                font=("Segoe UI", 10),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY,
                wraplength=600,
                justify=tk.LEFT
            )
        desc_label.pack(anchor="w", pady=(10, 0))

    def toggle_auto_continue(self):
        """Bật/tắt chế độ tự động tiếp tục sau đăng nhập"""
        self.auto_continue = self.auto_continue_var.get()
        try:
            self.wait_time = int(self.wait_time_entry.get())
        except ValueError:
            self.wait_time = 30
            self.wait_time_entry.delete(0, tk.END)
            self.wait_time_entry.insert(0, "30")

        status = "On" if self.auto_continue else "Off"
        self.log_message(f"Auto-continue after login: {status} (wait {self.wait_time}s)", "INFO")

    def show_login_dialog(self, account_name=None, cookies_file=None):
        """Hiển thị dialog đăng nhập YouTube thay vì dùng terminal"""
        # Tạo dialog modal
        login_dialog = tk.Toplevel(self.root)
        login_dialog.title("Đăng nhập YouTube")
        login_dialog.geometry("500x350")
        login_dialog.resizable(False, False)
        login_dialog.transient(self.root)
        login_dialog.grab_set()

        # Center dialog
        login_dialog.geometry("+{}+{}".format(
            self.root.winfo_x() + (self.root.winfo_width() // 2) - 250,
            self.root.winfo_y() + (self.root.winfo_height() // 2) - 175
        ))

        # Nội dung dialog
        tk.Label(login_dialog, text="🔐 Đăng nhập YouTube", font=("Arial", 16, "bold")).pack(pady=10)

        info_frame = tk.Frame(login_dialog)
        info_frame.pack(fill="x", padx=20, pady=5)

        if account_name:
            tk.Label(info_frame, text=f"Tài khoản: {account_name}", font=("Arial", 11)).pack(anchor="w")
        if cookies_file:
            tk.Label(info_frame, text=f"File cookies: {cookies_file}", font=("Arial", 11)).pack(anchor="w")

        # Hướng dẫn
        instructions = tk.Text(login_dialog, height=10, wrap=tk.WORD, font=("Arial", 10))
        instructions.pack(fill="x", padx=20, pady=10)
        instructions.insert("1.0", """Hướng dẫn đăng nhập:

1. Trình duyệt Chrome sẽ mở trang đăng nhập Google
2. Đăng nhập tài khoản Google của bạn
3. Sau khi đăng nhập thành công, quay lại đây
4. Nhấn nút "✅ Đã đăng nhập xong" để tiếp tục

⚠️ Lưu ý: 
- Đảm bảo đăng nhập đúng tài khoản có quyền truy cập kênh YouTube
- Không đóng trình duyệt Chrome cho đến khi hoàn thành
- Nếu gặp lỗi, nhấn "❌ Hủy" và thử lại""")
        instructions.config(state="disabled")

        # Button frame
        button_frame = tk.Frame(login_dialog)
        button_frame.pack(fill="x", padx=20, pady=20)

        result = {"completed": False}

        def on_login_complete():
            result["completed"] = True
            login_dialog.destroy()

        def on_cancel():
            login_dialog.destroy()

        tk.Button(button_frame, text="✅ Đã đăng nhập xong", command=on_login_complete,
                 font=("Arial", 11, "bold"), bg="#28A745", fg="white", padx=20).pack(side="left", padx=5)
        tk.Button(button_frame, text="❌ Hủy", command=on_cancel,
                 font=("Arial", 11), padx=20).pack(side="right", padx=5)

        # Wait for dialog
        self.root.wait_window(login_dialog)
        return result["completed"]

    def gui_login_and_save_cookies(self, account_name=None, cookies_file=None):
        """Phiên bản GUI của login_and_save_cookies - không dùng terminal"""
        import selenium.webdriver as webdriver
        from selenium.webdriver.chrome.options import Options
        import tempfile
        import subprocess

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
            self.log_message(f"Cookies file đã tồn tại: {cookies_file}", "INFO")

        self.log_message(f"Đang chuẩn bị đăng nhập cho tài khoản: {account_name or 'mặc định'}", "INFO")
        self.log_message(f"File cookies sẽ lưu: {cookies_file}", "INFO")

        driver = None
        try:
            # Khởi tạo driver
            self.log_message("Đang khởi tạo Chrome driver...", "INFO")
            driver = self.init_chrome_driver_for_login(headless=False)

            # Đăng nhập Google
            self.log_message("Đang mở trang đăng nhập Google...", "INFO")
            driver.get('https://accounts.google.com')

            # Hiển thị dialog hướng dẫn đăng nhập
            login_completed = self.show_login_dialog(account_name, cookies_file)
            if not login_completed:
                self.log_message("Đăng nhập đã bị hủy bởi người dùng", "WARNING")
                return None

            # Điều hướng đến YouTube để lấy cookies của YouTube
            self.log_message("Đang điều hướng đến YouTube để lấy cookies...", "INFO")
            driver.get('https://www.youtube.com')
            time.sleep(5)  # Đợi trang YouTube load xong

            # Lưu cookies
            cookies = driver.get_cookies()
            cookies_dir = os.path.dirname(cookies_file)
            if cookies_dir and not os.path.exists(cookies_dir):
                os.makedirs(cookies_dir, exist_ok=True)

            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)

            self.log_message(f"✓ Đã lưu cookies vào: {cookies_file}", "SUCCESS")

            # FIX: Update config.json with new account to ensure persistence
            if account_name:
                update_accounts_list(account_name, cookies_file)
                self.log_message(f"✓ Tài khoản '{account_name}' đã được lưu vào config.json", "SUCCESS")
                
                # NEW: Save to database
                try:
                    with db.session_scope() as session:
                        account = session.query(Account).filter(Account.name == account_name).first()
                        if not account:
                            account = Account(name=account_name, cookies_file=cookies_file)
                            session.add(account)
                            self.log_message(f"✓ Tài khoản '{account_name}' đã được lưu vào database", "SUCCESS")
                        else:
                             # Update cookies file if changed
                             if account.cookies_file != cookies_file:
                                 account.cookies_file = cookies_file
                                 self.log_message(f"✓ Cập nhật cookies cho tài khoản '{account_name}' trong database", "SUCCESS")
                except Exception as e:
                    self.log_message(f"⚠ Lỗi lưu tài khoản vào database: {str(e)}", "WARNING")

            return cookies_file

        except Exception as e:
            self.log_message(f"✗ Lỗi khi đăng nhập: {str(e)}", "ERROR")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def init_chrome_driver_for_login(self, headless=False):
        """Khởi tạo Chrome driver cho đăng nhập"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        import tempfile

        options = Options()

        # Các tham số cơ bản để tránh crash
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')

        # Tham số để tránh conflict với Chrome đang chạy
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-plugins-discovery')

        # Sử dụng profile tạm thời để tránh conflict
        temp_profile_dir = tempfile.mkdtemp(prefix='chrome_profile_')
        options.add_argument(f'--user-data-dir={temp_profile_dir}')

        # Tham số để chạy ổn định trên Windows
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')

        if headless:
            options.add_argument('--headless')
        else:
            options.add_argument('--window-size=1200,800')

        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Thêm experimental options để tránh crash
        options.add_experimental_option("useAutomationExtension", False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        driver = None
        try:
            self.log_message("Đang khởi tạo Chrome driver với các tham số tối ưu...", "INFO")

            # Thử khởi tạo Chrome driver
            try:
                driver = webdriver.Chrome(options=options)
            except Exception as chrome_error:
                self.log_message(f"Không thể khởi tạo Chrome driver thông thường, thử với Service: {str(chrome_error)}", "WARNING")

                # Thử với Service để chỉ định path chromedriver
                try:
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                    self.log_message("✓ Đã tự động download và sử dụng ChromeDriver mới", "SUCCESS")
                except ImportError:
                    self.log_message("⚠ webdriver-manager không có sẵn, hãy cài đặt: pip install webdriver-manager", "WARNING")
                    # Thử một lần nữa với Chrome driver mặc định
                    driver = webdriver.Chrome(options=options)
                except Exception as wm_error:
                    self.log_message(f"Lỗi với webdriver-manager: {str(wm_error)}", "ERROR")
                    raise chrome_error  # Raise lỗi ban đầu

            # Thực hiện một số lệnh để đảm bảo driver hoạt động
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                '''
            })

            self.log_message("✓ Chrome driver khởi tạo thành công", "SUCCESS")
            return driver

        except Exception as e:
            # Cleanup nếu có lỗi
            if driver:
                try:
                    driver.quit()
                except:
                    pass

            # Xóa profile tạm thời
            try:
                import shutil
                if os.path.exists(temp_profile_dir):
                    shutil.rmtree(temp_profile_dir, ignore_errors=True)
            except:
                pass

            self.log_message(f"Lỗi khởi tạo Chrome driver: {str(e)}", "ERROR")
            raise

    def create_control_section(self, parent):
        """Tạo section điều khiển với buttons đẹp"""
        if CUSTOM_TK_AVAILABLE:
            control_frame = ctk.CTkFrame(parent, fg_color="transparent")
        else:
            control_frame = tk.Frame(parent, bg=ModernColors.BG_DARK)
        control_frame.pack(fill="x", pady=(0, 20))
        
        # Buttons container với grid layout
        if CUSTOM_TK_AVAILABLE:
            buttons_container = ctk.CTkFrame(control_frame, fg_color="transparent")
        else:
            buttons_container = tk.Frame(control_frame, bg=ModernColors.BG_DARK)
        buttons_container.pack()
        
        # Button style function
        def create_button(parent, text, command, bg_color, hover_color, width=180, text_color="#FFFFFF"):
            if CUSTOM_TK_AVAILABLE:
                btn = ctk.CTkButton(
                    parent,
                    text=text,
                    command=command,
                    height=48,
                    width=width,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    fg_color=bg_color,
                    hover_color=hover_color,
                    corner_radius=10,
                    border_width=0,
                    text_color=text_color
                )
            else:
                btn = tk.Button(
                    parent,
                    text=text,
                    command=command,
                    font=("Segoe UI", 12, "bold"),
                    bg=bg_color,
                    fg=text_color,
                    activebackground=hover_color,
                    activeforeground=text_color,
                    relief=tk.FLAT,
                    bd=0,
                    padx=25,
                    pady=12,
                    cursor="hand2"
                )
            return btn
        
        # Row 1: Video retrieval button
        if CUSTOM_TK_AVAILABLE:
            row1 = ctk.CTkFrame(buttons_container, fg_color="transparent")
        else:
            row1 = tk.Frame(buttons_container, bg=ModernColors.BG_DARK)
        row1.pack(pady=5)

        get_videos_btn = create_button(
            row1,
            "📹 Get Video List",
            self.get_channel_videos,
            ModernColors.ACCENT,
            "#357ABD",
            200
        )
        get_videos_btn.pack(side="left", padx=8)

        self.start_btn = create_button(
            row1,
            "🚀 Scrape Selected Accounts",
            self.start_batch_scraping,
            ModernColors.SUCCESS,
            "#00CC66",
            200
        )
        self.start_btn.pack(side="left", padx=8)

        # Row 2: Control buttons
        if CUSTOM_TK_AVAILABLE:
            row2 = ctk.CTkFrame(buttons_container, fg_color="transparent")
        else:
            row2 = tk.Frame(buttons_container, bg=ModernColors.BG_DARK)
        row2.pack(pady=5)

        self.stop_btn = create_button(
            row2,
            "⏹️ Stop",
            self.stop_process,
            ModernColors.ERROR,
            "#CC0000",
            150
        )
        self.stop_btn.pack(side="left", padx=8)
        self.stop_btn.configure(state="disabled")

        clear_btn = create_button(
            row2,
            "🗑️ Clear Log",
            self.clear_log,
            "#6C757D",
            "#5A6268",
            150,
            "#FFFFFF"
        )
        clear_btn.pack(side="left", padx=8)
        
        
    def create_progress_section(self, parent):
        """Tạo section progress đẹp"""
        if CUSTOM_TK_AVAILABLE:
            progress_frame = ctk.CTkFrame(
                parent,
                fg_color=ModernColors.BG_CARD,
                corner_radius=12,
                border_width=1,
                border_color=ModernColors.BORDER
            )
        else:
            progress_frame = tk.Frame(
                parent,
                bg=ModernColors.BG_CARD,
                relief=tk.FLAT,
                bd=1,
                highlightbackground=ModernColors.BORDER,
                highlightthickness=1
            )
        progress_frame.pack(fill="x", pady=(0, 20))
        
        content = tk.Frame(progress_frame, bg=ModernColors.BG_CARD)
        content.pack(fill="both", padx=20, pady=18)
        
        # Title
        if CUSTOM_TK_AVAILABLE:
            title = ctk.CTkLabel(
                content,
                text="📊 Progress",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            title = tk.Label(
                content,
                text="📊 Progress",
                font=("Segoe UI", 14, "bold"),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY
            )
        title.pack(anchor="w", pady=(0, 12))
        
        # Progress bar
        if CUSTOM_TK_AVAILABLE:
            self.progress_var = tk.DoubleVar()
            self.progress_bar = ctk.CTkProgressBar(
                content,
                height=20,
                corner_radius=10,
                fg_color=ModernColors.SECONDARY,
                progress_color=ModernColors.PRIMARY
            )
            self.progress_bar.set(0)
        else:
            self.progress_var = tk.DoubleVar()
            style = ttk.Style()
            style.theme_use('clam')
            style.configure(
                "Modern.Horizontal.TProgressbar",
                background=ModernColors.PRIMARY,
                troughcolor=ModernColors.SECONDARY,
                borderwidth=0,
                lightcolor=ModernColors.PRIMARY,
                darkcolor=ModernColors.PRIMARY,
                thickness=20
            )
            self.progress_bar = ttk.Progressbar(
                content,
                variable=self.progress_var,
                maximum=100,
                style="Modern.Horizontal.TProgressbar",
                mode='determinate'
            )
        self.progress_bar.pack(fill="x", pady=(0, 10))
        
        # Progress label
        if CUSTOM_TK_AVAILABLE:
            self.progress_label = ctk.CTkLabel(
                content,
                text="Ready...",
                font=ctk.CTkFont(size=13),
                text_color=ModernColors.TEXT_SECONDARY
            )
        else:
            self.progress_label = tk.Label(
                content,
                text="Ready...",
                font=("Segoe UI", 11),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY
            )
        self.progress_label.pack()
        
    def create_log_section(self, parent):
        """Tạo section log với console style"""
        if CUSTOM_TK_AVAILABLE:
            log_frame = ctk.CTkFrame(
                parent,
                fg_color=ModernColors.BG_CARD,
                corner_radius=12,
                border_width=1,
                border_color=ModernColors.BORDER
            )
        else:
            log_frame = tk.Frame(
                parent,
                bg=ModernColors.BG_CARD,
                relief=tk.FLAT,
                bd=1,
                highlightbackground=ModernColors.BORDER,
                highlightthickness=1
            )
        log_frame.pack(fill="both", expand=True)
        
        # Header
        header = tk.Frame(log_frame, bg=ModernColors.BG_CARD)
        header.pack(fill="x", padx=20, pady=(18, 12))
        
        if CUSTOM_TK_AVAILABLE:
            title = ctk.CTkLabel(
                header,
                text="📝 Activity Log",
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=ModernColors.TEXT_PRIMARY
            )
        else:
            title = tk.Label(
                header,
                text="📝 Activity Log",
                font=("Segoe UI", 14, "bold"),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY
            )
        title.pack(side="left")
        
        # Log text area với console style
        if CUSTOM_TK_AVAILABLE:
            self.log_text = ctk.CTkTextbox(
                log_frame,
                height=180,
                font=ctk.CTkFont(size=11, family="Consolas"),
                fg_color=ModernColors.BG_DARK,
                text_color=ModernColors.TEXT_PRIMARY,
                corner_radius=8,
                border_width=2,
                border_color=ModernColors.BORDER
            )
        else:
            text_container = tk.Frame(log_frame, bg=ModernColors.BG_CARD)
            text_container.pack(fill="both", expand=True, padx=20, pady=(0, 18))
            
            self.log_text = scrolledtext.ScrolledText(
                text_container,
                height=12,
                font=("Consolas", 10),
                wrap=tk.WORD,
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_PRIMARY,
                insertbackground=ModernColors.TEXT_PRIMARY,
                selectbackground=ModernColors.PRIMARY,
                relief=tk.FLAT,
                bd=10,
                highlightthickness=2,
                highlightbackground=ModernColors.BORDER,
                highlightcolor=ModernColors.BORDER,
                state=tk.DISABLED  # FIX: Make read-only but allow programmatic updates
            )
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        
    def create_status_bar(self):
        """Tạo status bar minimal"""
        if CUSTOM_TK_AVAILABLE:
            self.status_bar = ctk.CTkLabel(
                self.root,
                text="● Ready | YouTube Analytics Scraper v1.0",
                height=30,
                font=ctk.CTkFont(size=11),
                text_color=ModernColors.TEXT_SECONDARY,
                anchor="w",
                padx=15
            )
        else:
            status_container = tk.Frame(self.root, bg=ModernColors.BG_CARD, height=30)
            status_container.pack(side=tk.BOTTOM, fill=tk.X)
            status_container.pack_propagate(False)
            
            self.status_bar = tk.Label(
                status_container,
                text="● Ready | YouTube Analytics Scraper v1.0",
                font=("Segoe UI", 10),
                bg=ModernColors.BG_CARD,
                fg=ModernColors.TEXT_SECONDARY,
                anchor="w",
                padx=15
            )
            self.status_bar.pack(fill="x", side="left")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # === MULTI-ACCOUNT SUPPORT HELPER METHODS ===

    def get_account_names(self):
        """
        Lấy danh sách tên các tài khoản từ config.json
        Trả về list: ['Account A', 'Account B', 'Account C']
        """
        try:
            config_file = 'config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    accounts = config.get('accounts', [])
                    account_names = [acc.get('name', 'Unknown') for acc in accounts]
                    return account_names
        except Exception as e:
            self.log_message(f"Lỗi lấy danh sách tài khoản: {str(e)}", "ERROR")
        return []

    def on_account_changed(self, value=None):
        """
        Xử lý sự kiện khi người dùng chọn account khác
        - Load cookies cho account mới
        - Cập nhật danh sách channels
        - Cập nhật trạng thái session
        """
        selected_account = self.account_var.get()

        if not selected_account:
            self.account_status_label.configure(text="⚠ Chưa chọn tài khoản")
            if self.channel_dropdown:
                self.channel_dropdown.configure(values=[])
            return

        # Lấy thông tin account từ config
        try:
            config_file = 'config.json'
            if not os.path.exists(config_file):
                self.log_message(f"Không tìm thấy config.json", "ERROR")
                return

            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            accounts = config.get('accounts', [])
            selected_account_obj = None

            for acc in accounts:
                if acc.get('name') == selected_account:
                    selected_account_obj = acc
                    break

            if not selected_account_obj:
                self.log_message(f"Không tìm thấy tài khoản: {selected_account}", "ERROR")
                return

            # === Update current account variables ===
            self.current_account_name = selected_account
            self.current_cookies_file = selected_account_obj.get('cookies_file')
            self.current_channel_url = None  # Reset
            self.current_video_ids = []  # Reset

            # === Load cookies for this account ===
            cookies_loaded = False
            if self.current_cookies_file and os.path.exists(self.current_cookies_file):
                try:
                    cookies_loaded = True
                    self.log_message(f"✓ Đã tải cookies cho tài khoản: {selected_account}", "SUCCESS")
                except Exception as e:
                    self.log_message(f"⚠ Lỗi tải cookies: {str(e)}", "WARNING")
            else:
                self.log_message(f"⚠ Chưa có cookies cho tài khoản: {selected_account}", "WARNING")

            # === Update channel dropdown ===
            if self.channel_dropdown:
                channels = selected_account_obj.get('channels', [])
                channel_display_list = [f"{ch.get('url')} ({len(ch.get('video_ids', []))} videos)"
                                       for ch in channels]

                self.channel_dropdown.configure(values=channel_display_list)

                if channel_display_list:
                    # Handle both CTkComboBox (set) and ttk.Combobox (current)
                    try:
                        # Try CTkComboBox method first
                        if hasattr(self.channel_dropdown, 'set'):
                            self.channel_dropdown.set(channel_display_list[0])
                        else:
                            # Fallback to ttk.Combobox method
                            self.channel_dropdown.current(0)
                    except Exception as e:
                        self.log_message(f"⚠ Lỗi cập nhật dropdown: {str(e)}", "WARNING")
                    self.on_channel_changed()

            # === Update status label ===
            channel_count = len(selected_account_obj.get('channels', []))
            total_videos = sum(len(ch.get('video_ids', [])) for ch in selected_account_obj.get('channels', []))

            status_text = f"✓ {selected_account} ({channel_count} kênh, {total_videos} videos)"
            if cookies_loaded:
                status_text += " • Cookies hợp lệ"
            else:
                status_text += " • ⚠ Chưa có cookies (cần đăng nhập)"

            self.account_status_label.configure(text=status_text)
            self.log_message(f"Đã chuyển sang tài khoản: {selected_account}", "INFO")
            
            # === Update channel management status (NEW WORKFLOW) ===
            if hasattr(self, 'update_channel_management_status'):
                self.update_channel_management_status()

        except Exception as e:
            self.log_message(f"Lỗi xử lý thay đổi tài khoản: {str(e)}", "ERROR")

    def on_channel_changed(self, value=None):
        """
        Xử lý sự kiện khi người dùng chọn channel khác
        - Cập nhật current_channel_url
        - Cập nhật thông tin channel (số video, lần cào cuối)
        """
        try:
            mode = self.channel_mode_var.get() if hasattr(self, 'channel_mode_var') else "existing"

            if mode == "existing":
                selected_text = self.channel_var.get()

                if not selected_text:
                    return

                # Extract URL from display text: "URL (N videos)"
                channel_url = selected_text.split(' (')[0] if ' (' in selected_text else selected_text

                # Get video_ids for this channel
                config_file = 'config.json'
                if not os.path.exists(config_file):
                    return

                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                accounts = config.get('accounts', [])

                for acc in accounts:
                    if acc.get('name') == self.current_account_name:
                        for ch in acc.get('channels', []):
                            if ch.get('url') == channel_url:
                                self.current_channel_url = channel_url
                                self.current_video_ids = ch.get('video_ids', [])
                                self.log_message(
                                    f"Đã chọn: {channel_url} ({len(self.current_video_ids)} videos)",
                                    "INFO"
                                )
                                return
        except Exception as e:
            self.log_message(f"Lỗi xử lý thay đổi channel: {str(e)}", "ERROR")

    def on_channel_mode_changed(self, value=None):
        """Chuyển đổi giữa 'Chọn từ kênh đã lưu' và 'Thêm kênh mới'"""
        try:
            mode = self.channel_mode_var.get()

            if mode == "existing":
                if self.existing_channel_frame:
                    self.existing_channel_frame.pack(fill="x", pady=(0, 10))
                if self.new_channel_frame:
                    self.new_channel_frame.pack_forget()
            else:
                if self.existing_channel_frame:
                    self.existing_channel_frame.pack_forget()
                if self.new_channel_frame:
                    self.new_channel_frame.pack(fill="x", pady=(0, 10))
        except Exception as e:
            self.log_message(f"Lỗi thay đổi chế độ channel: {str(e)}", "ERROR")

    def on_add_new_account(self):
        """
        Xử lý nút 'Tài khoản mới'
        - Hỏi tên account
        - Mở Chrome để đăng nhập
        - Lưu cookies
        - Cập nhật dropdown
        """
        try:
            account_name = simpledialog.askstring(
                "Tài khoản mới",
                "Nhập tên cho tài khoản mới:\n(ví dụ: Account A, YouTube Channel 1)"
            )

            if not account_name:
                return

            self.log_message(f"Đang thiết lập tài khoản mới: {account_name}...", "INFO")

            # Mở Chrome để đăng nhập (dùng phiên bản GUI không yêu cầu terminal)
            try:
                cookies_file = self.gui_login_and_save_cookies(account_name)

                if cookies_file:
                    self.log_message(f"✓ Tài khoản mới đã được tạo: {account_name}", "SUCCESS")

                    # Refresh account dropdown
                    account_names = self.get_account_names()
                    if CUSTOM_TK_AVAILABLE:
                        self.account_dropdown.configure(values=account_names)
                    else:
                        self.account_dropdown.configure(values=account_names)

                    self.account_var.set(account_name)
                    self.on_account_changed()

                    # Refresh batch account selector to show new account
                    self.refresh_batch_account_selector()
                else:
                    self.log_message(f"✗ Lỗi tạo tài khoản: {account_name}", "ERROR")
            except Exception as e:
                self.log_message(f"✗ Lỗi: {str(e)}", "ERROR")
        except Exception as e:
            self.log_message(f"✗ Lỗi tạo tài khoản mới: {str(e)}", "ERROR")

    def init_business_logic(self):
        """Khởi tạo logic nghiệp vụ"""
        try:
            # Tự động load config và chuẩn bị dữ liệu
            self.auto_load_config_on_startup()

            # === MODIFIED: Load first account as default for multi-account support ===
            account_names = self.get_account_names()
            if account_names:
                # Select first account as default
                self.account_var.set(account_names[0])
                self.on_account_changed()
                self.log_message(
                    f"✓ Tải tài khoản mặc định: {account_names[0]}",
                    "SUCCESS"
                )
            else:
                self.log_message(
                    "⚠ Chưa có tài khoản nào. Vui lòng tạo tài khoản mới.",
                    "WARNING"
                )
        except Exception as e:
            self.log_message(f"Lỗi khởi tạo logic nghiệp vụ: {str(e)}", "ERROR")

    def auto_load_config_on_startup(self):
        """Tự động load config.json và chuẩn bị dữ liệu khi khởi động phần mềm"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Hiển thị thông tin accounts
                accounts = config.get('accounts', [])
                if accounts:
                    account_info = f"Tự động load {len(accounts)} tài khoản từ config.json"
                    self.log_message(account_info, "SUCCESS")

                    # Hiển thị chi tiết từng account
                    for acc in accounts:
                        name = acc.get('name', 'Unknown')
                        channels = acc.get('channels', [])
                        total_videos = sum(len(ch.get('video_ids', [])) for ch in channels)
                        self.log_message(f"  - Tài khoản '{name}': {len(channels)} kênh, {total_videos} video", "INFO")

                    # Tự động load tất cả accounts và video IDs
                    all_video_ids = []
                    video_account_mapping = {}  # Mapping video_id -> account_name

                    for account in accounts:
                        account_name = account.get('name')
                        channels = account.get('channels', [])

                        for channel in channels:
                            video_ids = channel.get('video_ids', [])
                            for video_id in video_ids:
                                all_video_ids.append(video_id)
                                video_account_mapping[video_id] = account_name

                    if all_video_ids:
                        self.current_video_ids = list(set(all_video_ids))  # Loại bỏ trùng lặp
                        self.current_channel_url = accounts[0].get('channels', [{}])[0].get('url', '')  # URL của channel đầu tiên

                        self.log_message(f"✓ Đã tự động load {len(self.current_video_ids)} video IDs từ {len(accounts)} tài khoản", "SUCCESS")

                        # Hiển thị thông tin trong UI
                        self.display_accounts_in_ui(accounts)
                        self.update_channel_info(self.current_channel_url, self.current_video_ids)

                        # Cập nhật status bar
                        self.status_bar.configure(text=f"● Sẵn sàng | {len(accounts)} Accounts | {len(self.current_video_ids)} Videos")

                        # Thông báo về chế độ tự động
                        if self.is_auto_scraping:
                            self.log_message("💡 Chế độ tự động đang chạy - sẽ bao gồm tất cả tài khoản hiện tại", "INFO")

                        # Tự động bật chế độ tự động nếu được cấu hình
                        auto_scraping_enabled = config.get('auto_scraping_enabled', False)
                        if auto_scraping_enabled:
                            self.log_message("Tự động bật chế độ tự động cào dữ liệu đa tài khoản...", "INFO")
                            self.auto_scraping_var.set(True)
                            self.toggle_auto_scraping()
                    else:
                        self.log_message("Không có video IDs nào trong các tài khoản", "WARNING")
                        self.display_accounts_in_ui(accounts)

                    # Load các settings khác từ config
                    self.auto_scraping_interval = config.get('auto_scraping_interval', 30)
                    # Only update auto_interval_entry if it exists and is created
                    if hasattr(self, 'auto_interval_entry') and self.auto_interval_entry:
                        try:
                            self.auto_interval_entry.delete(0, tk.END)
                            self.auto_interval_entry.insert(0, str(self.auto_scraping_interval))
                        except Exception as e:
                            self.log_message(f"⚠ Không thể cập nhật interval entry: {str(e)}", "WARNING")

                else:
                    self.log_message("Chưa có tài khoản nào được cấu hình trong config.json", "WARNING")
                    self.display_accounts_in_ui([])
            else:
                self.log_message("File config.json chưa tồn tại - Vui lòng tạo config trước", "WARNING")
                self.display_accounts_in_ui([])

        except Exception as e:
            self.log_message(f"Lỗi khi tự động load config: {str(e)}", "ERROR")
            self.display_accounts_in_ui([])

    def display_config_info(self):
        """Hiển thị thông tin config hiện có mà không thực hiện hành động tự động"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Hiển thị thông tin accounts
                accounts = config.get('accounts', [])
                if accounts:
                    account_info = f"Tìm thấy {len(accounts)} tài khoản đã lưu"
                    self.log_message(account_info, "INFO")

                    # Hiển thị chi tiết từng account
                    for acc in accounts:
                        name = acc.get('name', 'Unknown')
                        channels = acc.get('channels', [])
                        total_videos = sum(len(ch.get('video_ids', [])) for ch in channels)
                        self.log_message(f"  - Tài khoản '{name}': {len(channels)} kênh, {total_videos} video", "INFO")

                    # Hiển thị trong channel info text area
                    self.display_accounts_in_ui(accounts)
                else:
                    self.log_message("Chưa có tài khoản nào được cấu hình", "WARNING")
                    self.display_accounts_in_ui([])
            else:
                self.log_message("File config.json chưa tồn tại", "WARNING")
                self.display_accounts_in_ui([])

        except Exception as e:
            self.log_message(f"Lỗi khi load config: {str(e)}", "ERROR")
            self.display_accounts_in_ui([])

    def display_accounts_in_ui(self, accounts):
        """Hiển thị danh sách accounts trong UI"""
        try:
            if accounts:
                # Hiển thị trong channel info text area
                info_text = "DANH SÁCH TÀI KHOẢN ĐÃ LƯU:\n\n"
                for i, acc in enumerate(accounts, 1):
                    name = acc.get('name', 'Unknown')
                    cookies_file = acc.get('cookies_file', 'N/A')
                    channels = acc.get('channels', [])
                    total_videos = sum(len(ch.get('video_ids', [])) for ch in channels)

                    info_text += f"{i}. {name}\n"
                    info_text += f"   Cookies: {cookies_file}\n"
                    info_text += f"   Channels: {len(channels)}, Videos: {total_videos}\n\n"

                # Cập nhật channel_info_text - FIX: Use helper for disabled widget
                if hasattr(self, 'channel_info_text'):
                    self.update_text_widget(self.channel_info_text, info_text)
            else:
                info_text = "Chưa có tài khoản nào được lưu.\n\n"
                info_text += "Để bắt đầu:\n"
                info_text += "1. Nhấn '🔐 Đăng nhập YouTube'\n"
                info_text += "2. Nhập URL kênh YouTube\n"
                info_text += "3. Nhấn '📹 Lấy danh sách video'\n"
                info_text += "4. Nhấn '🚀 Bắt đầu cào dữ liệu'\n"

                # FIX: Use helper for disabled widget
                if hasattr(self, 'channel_info_text'):
                    self.update_text_widget(self.channel_info_text, info_text)

        except Exception as e:
            self.log_message(f"Lỗi khi hiển thị accounts trong UI: {str(e)}", "ERROR")


    def get_channel_videos(self):
        """Lấy danh sách video IDs từ kênh YouTube - MODIFIED cho multi-account"""

        # === VALIDATE ACCOUNT SELECTION ===
        if not self.current_account_name:
            messagebox.showwarning(
                "Lỗi",
                "Vui lòng chọn hoặc tạo tài khoản trước khi thêm kênh!"
            )
            return

        # === GET CHANNEL URL based on mode ===
        mode = self.channel_mode_var.get() if hasattr(self, 'channel_mode_var') else "existing"

        if mode == "new":
            channel_url = self.url_entry.get().strip()

            if not channel_url:
                messagebox.showerror("Lỗi", "Vui lòng nhập URL kênh YouTube!")
                return

            # Normalize URL
            if not channel_url.startswith('http'):
                channel_url = f"https://www.youtube.com/{channel_url}"
        else:
            # If selecting from existing, skip download - user will click "Start Scraping" directly
            self.log_message("Sử dụng kênh đã chọn từ dropdown", "INFO")
            return

        def get_videos_thread():
            try:
                self.log_message(f"Bắt đầu lấy video IDs từ kênh: {channel_url}", "INFO")
                self.update_progress(10, "Đang chuẩn bị...")

                # Lấy max results nếu có
                max_results = None
                max_results_text = self.max_results_entry.get().strip()
                if max_results_text:
                    try:
                        max_results = int(max_results_text)
                    except ValueError:
                        max_results = None

                self.update_progress(30, "Đang quét kênh YouTube...")

                # Lấy video IDs
                video_ids = get_channel_video_ids(channel_url)

                if video_ids:
                    # Giới hạn số lượng nếu cần
                    if max_results and len(video_ids) > max_results:
                        video_ids = video_ids[:max_results]
                        self.log_message(f"Đã giới hạn xuống {max_results} video đầu tiên", "INFO")

                    self.current_channel_url = channel_url
                    self.current_video_ids = video_ids

                    self.update_progress(60, f"Tìm thấy {len(video_ids)} video")

                    # Kiểm tra xem có account nào chưa
                    has_account = bool(self.current_account_name or self.current_cookies_file)

                    if not has_account:
                        # Hỏi người dùng có muốn tạo tài khoản mới không
                        create_new_account = messagebox.askyesno(
                            "Tạo tài khoản mới",
                            f"Đã tìm thấy {len(video_ids)} video từ kênh {channel_url}.\n\n" +
                            "Bạn chưa chọn tài khoản. Có muốn tạo tài khoản mới để lưu kênh này không?\n\n" +
                            "Điều này sẽ:\n" +
                            "• Khởi tạo trình duyệt Chrome\n" +
                            "• Đăng nhập Google/YouTube\n" +
                            "• Lưu cookies để cào dữ liệu\n" +
                            "• Lưu kênh vào config.json"
                        )

                        if create_new_account:
                            self.update_progress(70, "Đang tạo tài khoản mới...")

                            # Hỏi người dùng có muốn đặt tên tài khoản không
                            want_custom_name = messagebox.askyesno(
                                "Tên tài khoản",
                                "Bạn có muốn đặt tên cho tài khoản không?\n\n" +
                                "• Có: Nhập tên tùy chỉnh\n" +
                                "• Không: Tự động tạo tên (account_timestamp)"
                            )

                            if want_custom_name:
                                # Tạo dialog an toàn để nhập tên
                                name_dialog = tk.Toplevel(self.root)
                                name_dialog.title("Nhập tên tài khoản")
                                name_dialog.geometry("300x120")
                                name_dialog.resizable(False, False)

                                # Center dialog
                                name_dialog.transient(self.root)
                                name_dialog.grab_set()

                                tk.Label(name_dialog, text="Nhập tên tài khoản:", font=("Arial", 10)).pack(pady=10)

                                name_var = tk.StringVar()
                                name_entry = tk.Entry(name_dialog, textvariable=name_var, font=("Arial", 10))
                                name_entry.pack(pady=5, padx=20, fill="x")
                                name_entry.focus()

                                result = {"name": None, "submitted": False}

                                def on_ok():
                                    name = name_var.get().strip()
                                    if name:
                                        result["name"] = name
                                        result["submitted"] = True
                                        name_dialog.destroy()
                                    else:
                                        messagebox.showwarning("Cảnh báo", "Tên tài khoản không được để trống!")

                                def on_cancel():
                                    result["submitted"] = True
                                    name_dialog.destroy()

                                # Buttons
                                button_frame = tk.Frame(name_dialog)
                                button_frame.pack(pady=10)

                                tk.Button(button_frame, text="OK", command=on_ok, width=8).pack(side="left", padx=5)
                                tk.Button(button_frame, text="Hủy", command=on_cancel, width=8).pack(side="left", padx=5)

                                # Bind Enter key
                                name_entry.bind("<Return>", lambda e: on_ok())
                                name_entry.bind("<Escape>", lambda e: on_cancel())

                                # Wait for dialog
                                self.root.wait_window(name_dialog)

                                if result["submitted"] and result["name"]:
                                    account_name = result["name"]
                                    self.log_message(f"Đang tạo tài khoản tùy chỉnh: {account_name}", "INFO")
                                else:
                                    # Người dùng hủy hoặc để trống
                                    account_name = f"account_{int(time.time())}"
                                    self.log_message(f"Đã hủy đặt tên, tạo tài khoản tự động: {account_name}", "INFO")
                            else:
                                # Tự động tạo tên
                                account_name = f"account_{int(time.time())}"
                                self.log_message(f"Đang tạo tài khoản tự động: {account_name}", "INFO")

                            # Tạo cookies
                            try:
                                self.log_message(f"Đang tạo tài khoản '{account_name}'...", "INFO")
                                self.update_progress(80, "Đang khởi tạo trình duyệt...")

                                cookies_file = self.gui_login_and_save_cookies(account_name=account_name)
                                if cookies_file:
                                    self.current_cookies_file = cookies_file
                                    self.current_account_name = account_name
                                    has_account = True

                                    self.log_message(f"✓ Đã tạo cookies thành công cho tài khoản: {account_name}", "SUCCESS")

                                    # Cập nhật danh sách tài khoản vào config.json
                                    update_accounts_list(account_name, cookies_file)

                                    # Thông báo về chế độ tự động
                                    if self.is_auto_scraping:
                                        self.log_message("💡 Tài khoản mới sẽ được bao gồm trong chế độ tự động", "INFO")
                                else:
                                    self.log_message("✗ Không thể tạo cookies. Kênh sẽ được lưu tạm thời.", "WARNING")
                                    has_account = False

                            except Exception as e:
                                self.log_message(f"Lỗi khi tạo tài khoản: {str(e)}", "ERROR")
                                has_account = False
                        else:
                            self.log_message("Bỏ qua tạo tài khoản. Kênh sẽ được lưu tạm thời.", "INFO")

                    # Lưu vào config nếu có account
                    if has_account and (self.current_account_name or self.current_cookies_file):
                        self.update_progress(90, "Đang lưu vào config.json...")
                        self.log_message(f"Đang lưu kênh vào tài khoản: {self.current_account_name}...", "INFO")

                        # CRITICAL FIX: Pass cookies_file to ensure proper account-channel linking
                        success = save_to_config(
                            channel_url=channel_url,
                            video_ids=video_ids,
                            cookies_file=self.current_cookies_file  # ✓ This links channel to correct account
                        )
                        if success:
                            self.log_message("✓ Đã lưu vào config.json", "SUCCESS")
                            # CRITICAL FIX: Refresh account selector to show newly saved account
                            self.log_message("Đang làm mới danh sách tài khoản...", "INFO")
                            self.refresh_batch_account_selector()
                        else:
                            self.log_message("⚠ Không thể lưu vào config.json", "WARNING")
                    elif not has_account:
                        self.log_message("ℹ Kênh đã được load nhưng chưa lưu vào config (không có tài khoản)", "INFO")

                    # Cập nhật UI
                    self.update_channel_info(channel_url, video_ids)
                    self.update_progress(100, f"Hoàn thành! Tìm thấy {len(video_ids)} video")
                    self.log_message(f"✓ Hoàn thành! Tìm thấy {len(video_ids)} video IDs", "SUCCESS")

                    # Hiển thị vài video đầu tiên
                    for i, vid in enumerate(video_ids[:10], 1):
                        self.log_message(f"  {i}. {vid}", "INFO")
                    if len(video_ids) > 10:
                        self.log_message(f"  ... và {len(video_ids) - 10} video khác", "INFO")

                else:
                    self.update_progress(0, "Không tìm thấy video nào")
                    self.log_message("✗ Không tìm thấy video IDs nào trong kênh này", "ERROR")

            except Exception as e:
                self.log_message(f"Lỗi khi lấy video IDs: {str(e)}", "ERROR")
                self.update_progress(0, "Lỗi")

        # Chạy trong thread riêng
        thread = threading.Thread(target=get_videos_thread, daemon=True)
        thread.start()

    def update_channel_info(self, channel_url, video_ids):
        """Cập nhật thông tin kênh trong UI"""
        # Cập nhật labels
        self.channel_url_label.configure(text=f"Kênh: {channel_url}")
        self.video_count_label.configure(text=f"Số lượng video: {len(video_ids)}")

        # Cập nhật text area
        info_text = f"URL: {channel_url}\n"
        info_text += f"Tổng số video: {len(video_ids)}\n\n"

        if video_ids:
            info_text += "DANH SÁCH VIDEO IDs:\n"
            for i, vid in enumerate(video_ids[:20], 1):  # Hiển thị tối đa 20 video
                info_text += f"{i:2d}. {vid}\n"
            if len(video_ids) > 20:
                info_text += f"... và {len(video_ids) - 20} video khác\n"

        # FIX: Use helper for disabled widget
        self.update_text_widget(self.channel_info_text, info_text)

    def start_batch_scraping(self):
        """Bắt đầu cào dữ liệu cho các tài khoản đã chọn - Sequential mode"""
        # Check which accounts are selected
        selected_accounts = [
            acc_name for acc_name, acc_var in self.selected_accounts.items()
            if acc_var.get()
        ]

        if not selected_accounts:
            messagebox.showerror("Lỗi", "Vui lòng chọn ít nhất một tài khoản để cào!")
            return

        # Load config to get account details
        try:
            if not os.path.exists('config.json'):
                messagebox.showerror("Lỗi", "Không tìm thấy file config.json")
                return

            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                accounts = config.get('accounts', [])

            # Filter to only selected accounts
            accounts_to_scrape = [
                acc for acc in accounts
                if acc.get('name') in selected_accounts
            ]

            if not accounts_to_scrape:
                messagebox.showerror("Lỗi", "Không tìm thấy thông tin tài khoản được chọn")
                return

            # FIX: Enable stop button before starting scraping
            self.stop_btn.configure(state="normal")

            # Start batch scraping in a thread
            self.scraping_thread = threading.Thread(
                target=self.batch_scraping_worker,
                args=(accounts_to_scrape,),
                daemon=True
            )
            self.scraping_thread.start()

        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi load config.json: {str(e)}")
            self.log_message(f"✗ Lỗi: {str(e)}", "ERROR")

    def batch_scraping_worker(self, accounts_to_scrape):
        """Worker thread để cào dữ liệu tuần tự cho từng tài khoản"""
        try:
            total_accounts = len(accounts_to_scrape)
            self.is_scraping = True

            self.log_message(f"\n{'='*60}", "INFO")
            self.log_message(f"🎬 BẮT ĐẦU CÀO DỮ LIỆU - {total_accounts} TÀI KHOẢN", "SUCCESS")
            self.log_message(f"{'='*60}\n", "INFO")

            all_results = []

            for account_idx, account in enumerate(accounts_to_scrape, 1):
                if not self.is_scraping:
                    break

                account_name = account.get('name', 'Unknown')
                cookies_file = account.get('cookies_file')
                channels = account.get('channels', [])

                self.log_message(f"\n[{account_idx}/{total_accounts}] 🔄 Cào tài khoản: {account_name}", "INFO")
                self.log_message(f"👤 Cookies: {cookies_file if cookies_file else 'N/A'}", "INFO")
                self.log_message(f"📹 Số kênh: {len(channels)}", "INFO")

                # Collect all video IDs from all channels for this account
                # CRITICAL: Each channel is explicitly linked to this account
                all_video_ids = []
                for channel_idx, channel in enumerate(channels, 1):
                    channel_url = channel.get('url', 'Unknown')
                    video_ids = channel.get('video_ids', [])
                    all_video_ids.extend(video_ids)
                    self.log_message(f"   ├─ Kênh {channel_idx}: {channel_url} ({len(video_ids)} videos)", "INFO")

                total_videos = len(all_video_ids)
                if total_videos == 0:
                    self.log_message(f"⚠ Tài khoản {account_name} không có video nào để cào", "WARNING")
                    continue

                self.log_message(f"Số video cần cào: {total_videos}", "INFO")

                # Initialize scraper for this account
                # CRITICAL FIX: Use this account's cookies for this account's channels
                scraper_instance = None
                try:
                    self.log_message(f"✓ Sử dụng cookies của {account_name}: {cookies_file}", "SUCCESS")

                    scraper_instance = YouTubeAnalyticsScraper(
                        cookies_file=cookies_file,
                        account_name=account_name,
                        auto_continue=self.auto_continue,
                        wait_time=self.wait_time
                    )

                    self.update_progress(0, f"[{account_idx}/{total_accounts}] Khởi tạo scraper cho {account_name}...")
                    scraper_instance.init_driver(headless=False)

                    # Load cookies
                    self.update_progress(10, f"[{account_idx}/{total_accounts}] Load cookies...")
                    if not scraper_instance.load_cookies(headless=False):
                        self.log_message(f"✗ Không thể load cookies cho {account_name}", "ERROR")
                        if scraper_instance:
                            try:
                                scraper_instance.close()
                            except Exception as close_err:
                                pass
                        continue

                    # Scrape videos for this account
                    results = []
                    for video_idx, video_id in enumerate(all_video_ids, 1):
                        if not self.is_scraping:
                            break

                        # FIX: Calculate progress correctly including video progress
                        # Progress = (completed_accounts + (current_videos / total_videos_in_account)) / total_accounts
                        account_progress = (account_idx - 1) / total_accounts  # Completed accounts
                        current_account_progress = (video_idx / total_videos) / total_accounts  # Current account progress
                        overall_progress = (account_progress + current_account_progress) * 100

                        self.update_progress(
                            overall_progress,
                            f"[{account_idx}/{total_accounts}] Cào {account_name} - Video {video_idx}/{total_videos}: {video_id}"
                        )

                        self.log_message(f"  → Video {video_idx}/{total_videos}: {video_id}", "INFO")

                        try:
                            data = scraper_instance.get_video_analytics(video_id, headless=False)
                            results.append(data)
                        except Exception as e:
                            self.log_message(f"    ✗ Lỗi: {str(e)}", "ERROR")
                            results.append({
                                'video_id': video_id,
                                'error': str(e),
                                'crawl_datetime': datetime.now().strftime('%d/%m/%Y')
                            })

                        # Sleep between videos
                        if self.is_scraping:
                            time.sleep(2)

                    # Save results for this account
                    if self.is_scraping and results:
                        self.update_progress(90, f"Đang lưu kết quả cho {account_name}...")
                        try:
                            output_file = f'analytics_results_{account_name}.json'
                            scraper_instance.save_results(results, output_file=output_file)

                            success_count = len([r for r in results if 'error' not in r])
                            error_count = len([r for r in results if 'error' in r])

                            self.log_message(f"✓ Tài khoản {account_name} hoàn thành!", "SUCCESS")
                            self.log_message(f"  Thành công: {success_count}/{total_videos}, Lỗi: {error_count}", "INFO")
                            self.log_message(f"  Kết quả lưu tại: {output_file}", "INFO")

                            all_results.extend(results)
                        except Exception as e:
                            self.log_message(f"✗ Lỗi lưu kết quả: {str(e)}", "ERROR")

                except Exception as e:
                    self.log_message(f"✗ Lỗi xử lý tài khoản {account_name}: {str(e)}", "ERROR")
                finally:
                    # Always close driver for this account, even if error occurred
                    if scraper_instance:
                        try:
                            scraper_instance.close()
                        except Exception as close_err:
                            pass

            # Show summary
            if self.is_scraping:
                self.update_progress(100, "Hoàn thành!")
                self.log_message(f"\n{'='*60}", "INFO")
                self.log_message(f"✓ HOÀN THÀNH CÀO DỮ LIỆU", "SUCCESS")
                self.log_message(f"Tổng cộng: {len(all_results)} video từ {total_accounts} tài khoản", "INFO")
                self.log_message(f"{'='*60}\n", "INFO")
            else:
                self.log_message("\n⚠ Quá trình cào dữ liệu đã bị dừng", "WARNING")

        except Exception as e:
            self.log_message(f"✗ Lỗi trong quá trình cào: {str(e)}", "ERROR")
        finally:
            self.is_scraping = False
            self.update_progress(0, "Sẵn sàng...")
            # FIX: Disable stop button when scraping finishes
            self.stop_btn.configure(state="disabled")

    def start_full_process(self):
        """Bắt đầu toàn bộ quá trình: lấy video IDs + cào dữ liệu"""
        channel_url = self.url_entry.get().strip()

        if not channel_url:
            messagebox.showerror("Lỗi", "Vui lòng nhập URL kênh YouTube!")
            return

        # Nếu chưa có video IDs hoặc kênh khác, lấy lại
        if not self.current_video_ids or self.current_channel_url != channel_url:
            self.log_message("Chưa có thông tin kênh hoặc kênh mới. Đang lấy video IDs trước...", "INFO")
            self.get_channel_videos()
            # Đợi một chút rồi bắt đầu cào
            self.root.after(2000, self.start_scraping_process)
        else:
            self.start_scraping_process()


    def start_scraping_process(self):
        """Bắt đầu quá trình cào dữ liệu analytics với tài khoản hiện tại"""
        if not self.current_video_ids:
            messagebox.showerror("Lỗi", "Vui lòng lấy danh sách video IDs trước!")
            return

        if not self.current_account_name or not self.current_cookies_file:
            # Bỏ thông báo lỗi, chỉ kiểm tra logic
            # messagebox.showerror("Lỗi", "Vui lòng chọn tài khoản trước!\n\n" +
            #                    "Cách chọn tài khoản:\n" +
            #                    "1. Quét kênh YouTube và tạo tài khoản mới\n" +
            #                    "2. Tài khoản sẽ được tự động chọn sau khi tạo")
            return

        # Bỏ kiểm tra is_scraping để cho phép chạy nhiều quá trình cùng lúc

        # Cho phép chạy cùng chế độ tự động
        def scraping_thread():
            try:
                # Bỏ set_buttons_state(False) để nút luôn bật
                # self.set_buttons_state(False)

                self.log_message(f"Bắt đầu cào dữ liệu analytics cho {len(self.current_video_ids)} video...", "INFO")
                self.log_message(f"Sử dụng tài khoản: {self.current_account_name}", "INFO")

                self.update_progress(10, "Đang khởi tạo scraper...")

                # Khởi tạo scraper với cookies đã có
                scraper_instance = YouTubeAnalyticsScraper(
                    cookies_file=self.current_cookies_file,
                    account_name=self.current_account_name,
                    auto_continue=self.auto_continue,
                    wait_time=self.wait_time
                )
                self.scraper = scraper_instance

                # Khởi tạo driver
                self.update_progress(10, "Đang khởi tạo Chrome driver...")
                try:
                    scraper_instance.init_driver(headless=False)
                except Exception as e:
                    self.log_message(f"✗ Lỗi khởi tạo Chrome driver: {str(e)}", "ERROR")
                    self.update_progress(0, "Lỗi Chrome driver")
                    return

                # Load cookies
                self.update_progress(15, "Đang load cookies...")
                try:
                    if not scraper_instance.load_cookies(headless=False):
                        self.log_message("✗ Không thể load cookies.", "ERROR")
                        self.update_progress(0, "Lỗi cookies")
                        return
                except Exception as e:
                    self.log_message(f"✗ Lỗi load cookies: {str(e)}", "ERROR")
                    self.update_progress(0, "Lỗi cookies")
                    return

                # Cào dữ liệu
                results = []
                total_videos = len(self.current_video_ids)

                for i, video_id in enumerate(self.current_video_ids, 1):
                    if not self.is_scraping:  # Kiểm tra nếu bị dừng
                        break

                    progress = 15 + (i / total_videos) * 80
                    self.update_progress(progress, f"Đang cào video {i}/{total_videos}: {video_id}")

                    self.log_message(f"Đang cào video {i}/{total_videos}: {video_id}", "INFO")

                    try:
                        # Cào dữ liệu cho video này
                        data = scraper_instance.get_video_analytics(video_id, headless=False)
                        results.append(data)
                    except Exception as e:
                        self.log_message(f"✗ Lỗi cào video {video_id}: {str(e)}", "ERROR")
                        # Tiếp tục với video tiếp theo
                        results.append({
                            'video_id': video_id,
                            'error': str(e),
                            'crawl_datetime': datetime.now().strftime('%d/%m/%Y')
                        })

                    # Nghỉ giữa các video
                    if self.is_scraping:
                        time.sleep(2)

                if self.is_scraping:  # Chỉ lưu nếu không bị dừng
                    # Lưu kết quả
                    self.update_progress(95, "Đang lưu kết quả...")
                    try:
                        output_file = f'analytics_results_{self.current_account_name or "default"}.json'
                        scraper_instance.save_results(results, output_file=output_file)

                        self.update_progress(100, "Hoàn thành!")
                        self.log_message(f"✓ Hoàn thành! Đã cào {len(results)}/{total_videos} video", "SUCCESS")
                        self.log_message(f"Kết quả lưu tại: {output_file}", "INFO")

                        # Hiển thị thống kê
                        self.show_scraping_results(results)
                    except Exception as e:
                        self.log_message(f"✗ Lỗi lưu kết quả: {str(e)}", "ERROR")
                        self.update_progress(0, "Lỗi lưu file")

                else:
                    self.log_message("⚠ Quá trình cào dữ liệu đã bị dừng", "WARNING")

            except Exception as e:
                self.log_message(f"Lỗi khi cào dữ liệu: {str(e)}", "ERROR")
                self.update_progress(0, "Lỗi")
            finally:
                # Bỏ set_buttons_state(True) để nút luôn bật
                # self.is_scraping = False
                # self.set_buttons_state(True)
                if scraper_instance:
                    try:
                        scraper_instance.close()
                    except:
                        pass

        # Chạy trong thread riêng
        self.scraping_thread = threading.Thread(target=scraping_thread, daemon=True)
        self.scraping_thread.start()

    def show_scraping_results(self, results):
        """Hiển thị kết quả cào dữ liệu"""
        if not results:
            return

        success_count = len([r for r in results if 'error' not in r])
        error_count = len([r for r in results if 'error' in r])

        self.log_message(f"\n{'='*50}", "INFO")
        self.log_message("KẾT QUẢ CÀO DỮ LIỆU:", "INFO")
        self.log_message(f"{'='*50}", "INFO")
        self.log_message(f"Tổng số video: {len(results)}", "INFO")
        self.log_message(f"Thành công: {success_count}", "SUCCESS")
        self.log_message(f"Lỗi: {error_count}", "ERROR")
        self.log_message(f"{'='*50}\n", "INFO")

        # Hiển thị chi tiết cho một vài video đầu tiên
        for i, result in enumerate(results[:5], 1):
            video_id = result.get('video_id', 'Unknown')
            if 'error' in result:
                self.log_message(f"Video {i}: {video_id} - LỖI: {result['error']}", "ERROR")
            else:
                views = result.get('impressions_data', {}).get('Views', 'N/A')
                self.log_message(f"Video {i}: {video_id} - Views: {views}", "SUCCESS")

    def stop_process(self):
        """Dừng quá trình cào dữ liệu"""
        if self.is_scraping:
            self.is_scraping = False
            self.log_message("Đang dừng quá trình cào dữ liệu...", "WARNING")
            self.update_progress(0, "Đã dừng")
        else:
            self.log_message("Không có quá trình nào đang chạy", "INFO")

    # Auto-scraping methods removed - using manual batch scraping instead

    def start_auto_scraping_deprecated(self):
        """Bắt đầu chế độ tự động cào dữ liệu (tự động load từ config.json)"""
        if self.is_auto_scraping:
            return

        self.is_auto_scraping = True
        self.log_message(f"Chế độ tự động đã bật - Cào mỗi {self.auto_scraping_interval} phút", "SUCCESS")

        if CUSTOM_TK_AVAILABLE:
            self.auto_status_label.configure(text=f"Trạng thái: Đang chạy (mỗi {self.auto_scraping_interval} phút)")
        else:
            self.auto_status_label.configure(text=f"Trạng thái: Đang chạy (mỗi {self.auto_scraping_interval} phút)")

        def auto_scraping_loop():
            while self.is_auto_scraping:
                try:
                    # Tự động load từ config.json
                    self.log_message("Tự động load config và cào dữ liệu đa tài khoản...", "INFO")

                    # Load config.json
                    try:
                        if os.path.exists('config.json'):
                            with open('config.json', 'r', encoding='utf-8') as f:
                                config = json.load(f)

                            accounts = config.get('accounts', [])
                            if not accounts:
                                self.log_message("Không có tài khoản nào trong config.json", "ERROR")
                                time.sleep(300)  # Đợi 5 phút rồi thử lại
                                continue

                            # Tạo video_account_mapping cho chế độ parallel
                            all_video_ids = []
                            video_account_mapping = {}

                            for account in accounts:
                                account_name = account.get('name')
                                channels = account.get('channels', [])

                                for channel in channels:
                                    video_ids = channel.get('video_ids', [])
                                    for video_id in video_ids:
                                        all_video_ids.append(video_id)
                                        video_account_mapping[video_id] = account_name

                            if all_video_ids:
                                all_video_ids_unique = list(set(all_video_ids))  # Loại bỏ trùng lặp
                                
                                # Lấy min interval từ UI
                                try:
                                    min_interval_text = self.min_interval_hours_entry.get().strip()
                                    min_interval_hours = int(min_interval_text) if min_interval_text else 24
                                except ValueError:
                                    min_interval_hours = 24
                                
                                # Filter videos cần cào (chỉ cào video chưa cào hoặc đã cào cách đây >= min_interval_hours)
                                if min_interval_hours > 0:
                                    videos_to_scrape = self.scraping_tracker.filter_videos_to_scrape(
                                        all_video_ids_unique, 
                                        min_interval_hours=min_interval_hours
                                    )
                                    self.current_video_ids = videos_to_scrape
                                    skipped_count = len(all_video_ids_unique) - len(videos_to_scrape)
                                    if skipped_count > 0:
                                        self.log_message(f"⏭️ Bỏ qua {skipped_count} video đã cào gần đây (cách đây < {min_interval_hours}h)", "INFO")
                                else:
                                    # min_interval_hours = 0: cào tất cả
                                    self.current_video_ids = all_video_ids_unique
                                
                                if self.current_video_ids:
                                    self.log_message(f"✓ Đã load {len(self.current_video_ids)} video IDs cần cào từ {len(accounts)} tài khoản", "SUCCESS")
                                    self.log_message(f"   Sẽ chạy {len(accounts)} Chrome driver song song", "INFO")
                                else:
                                    self.log_message(f"⚠ Tất cả {len(all_video_ids_unique)} video đã được cào gần đây, không có video nào cần cào", "WARNING")
                                    time.sleep(300)  # Đợi 5 phút rồi thử lại
                                    continue

                                # Hiển thị thông tin trong UI
                                self.display_accounts_in_ui(accounts)
                                self.update_channel_info("", self.current_video_ids)
                            else:
                                self.log_message("Không có video IDs nào trong các tài khoản", "WARNING")
                                time.sleep(300)
                                continue
                        else:
                            self.log_message("Không tìm thấy file config.json", "ERROR")
                            time.sleep(300)
                            continue

                    except Exception as e:
                        self.log_message(f"Lỗi khi load config.json: {str(e)}", "ERROR")
                        time.sleep(300)
                        continue

                    # Thực hiện cào dữ liệu đa tài khoản song song
                    # Chỉ chạy nếu không có scraping thủ công nào đang chạy
                    if not self.is_scraping:
                        # Kiểm tra chế độ headless từ config
                        auto_headless = config.get('auto_scraping_headless', True)
                        if auto_headless:
                            self.log_message("🔒 Chế độ headless: Chrome sẽ chạy ẩn (không hiển thị cửa sổ)", "INFO")
                        else:
                            self.log_message("🖥️ Chế độ hiển thị: Chrome sẽ hiển thị cửa sổ", "INFO")

                        # Filter video_account_mapping chỉ giữ lại videos cần cào
                        filtered_mapping = {
                            vid: acc for vid, acc in video_account_mapping.items() 
                            if vid in self.current_video_ids
                        }
                        
                        if filtered_mapping:
                            self.start_parallel_scraping(filtered_mapping, headless=auto_headless)
                        else:
                            self.log_message("⚠ Không có video nào cần cào sau khi filter", "WARNING")
                    else:
                        self.log_message("Bỏ qua vòng cào tự động vì đang có scraping thủ công", "INFO")
                        # Đợi một chút rồi kiểm tra lại
                        time.sleep(60)
                        continue

                    # Đợi đến lần cào tiếp theo
                    wait_time = self.auto_scraping_interval * 60  # chuyển sang giây
                    for remaining in range(wait_time, 0, -1):
                        if not self.is_auto_scraping:
                            break
                        minutes = remaining // 60
                        seconds = remaining % 60
                        status_text = f"Trạng thái: Đang chạy (cào tiếp theo sau {minutes:02d}:{seconds:02d})"

                        if CUSTOM_TK_AVAILABLE:
                            self.auto_status_label.configure(text=status_text)
                        else:
                            self.auto_status_label.configure(text=status_text)

                        time.sleep(1)

                except Exception as e:
                    self.log_message(f"Lỗi trong chế độ tự động: {str(e)}", "ERROR")
                    time.sleep(60)  # Đợi 1 phút rồi thử lại

        # Chạy trong thread riêng
        self.auto_scraping_thread = threading.Thread(target=auto_scraping_loop, daemon=True)
        self.auto_scraping_thread.start()

    def start_parallel_scraping(self, video_account_mapping, headless=False):
        """Bắt đầu cào dữ liệu song song với nhiều tài khoản"""
        if not self.current_video_ids:
            self.log_message("Không có video IDs để cào", "ERROR")
            return

        # Bỏ kiểm tra is_scraping để cho phép chạy nhiều quá trình cùng lúc
        # if self.is_scraping:
        #     self.log_message("Đang có quá trình cào dữ liệu đang chạy", "WARNING")
        #     return

        # Cho phép chạy cùng chế độ tự động (auto scraping chạy ngầm)
        # Chỉ chặn khi có scraping thủ công đang chạy

        def parallel_scraping_thread():
            scraper_instance = None
            try:
                # Bỏ set_buttons_state(False) để nút luôn bật
                # self.is_scraping = True
                # self.set_buttons_state(False)

                self.log_message(f"Bắt đầu cào dữ liệu song song cho {len(self.current_video_ids)} video với {len(set(video_account_mapping.values()))} tài khoản", "INFO")

                # Khởi tạo scraper chính để sử dụng chế độ parallel
                scraper_instance = YouTubeAnalyticsScraper(
                    account_name="parallel_mode",  # Không sử dụng account cụ thể
                    auto_continue=self.auto_continue,
                    wait_time=self.wait_time
                )

                # Sử dụng chế độ parallel để chạy nhiều Chrome driver
                results = scraper_instance.scrape_multiple_videos_parallel(
                    video_ids=self.current_video_ids,
                    video_account_mapping=video_account_mapping,
                    max_workers=len(set(video_account_mapping.values())),  # Số worker = số account
                    headless=headless,
                    auto_continue=self.auto_continue,
                    wait_time=self.wait_time
                )

                # Lưu kết quả
                self.update_progress(95, "Đang lưu kết quả...")
                try:
                    # Sử dụng file cố định thay vì tạo file mới mỗi lần
                    output_file = 'analytics_results_parallel.json'
                    scraper_instance.save_results(results, output_file=output_file)
                    
                    # Mark videos as scraped trong tracker
                    from datetime import datetime
                    scraped_video_ids = [r.get('video_id') for r in results if r.get('video_id') and 'error' not in r]
                    if scraped_video_ids:
                        self.scraping_tracker.mark_multiple_scraped(scraped_video_ids, datetime.now())
                        self.scraping_tracker.save()
                        self.log_message(f"✓ Đã đánh dấu {len(scraped_video_ids)} video đã cào trong tracker", "SUCCESS")

                    self.update_progress(100, "Hoàn thành!")
                    success_count = len([r for r in results if 'error' not in r])
                    self.log_message(f"✓ Hoàn thành! Đã cào {success_count}/{len(results)} video", "SUCCESS")
                    self.log_message(f"Kết quả lưu tại: {output_file}", "INFO")

                    # Hiển thị thống kê
                    self.show_parallel_results(results)

                except Exception as e:
                    self.log_message(f"✗ Lỗi lưu kết quả: {str(e)}", "ERROR")
                    self.update_progress(0, "Lỗi lưu file")

            except Exception as e:
                self.log_message(f"Lỗi khi cào dữ liệu song song: {str(e)}", "ERROR")
                self.update_progress(0, "Lỗi")
            finally:
                # Bỏ set_buttons_state(True) để nút luôn bật
                # self.is_scraping = False
                # self.set_buttons_state(True)
                if scraper_instance:
                    try:
                        scraper_instance.close()
                    except:
                        pass

        # Chạy trong thread riêng
        self.scraping_thread = threading.Thread(target=parallel_scraping_thread, daemon=True)
        self.scraping_thread.start()

    def show_parallel_results(self, results):
        """Hiển thị kết quả cào dữ liệu song song"""
        if not results:
            return

        success_count = len([r for r in results if 'error' not in r])
        error_count = len([r for r in results if 'error' in r])

        self.log_message(f"\n{'='*60}", "INFO")
        self.log_message("KẾT QUẢ CÀO DỮ LIỆU SONG SONG:", "INFO")
        self.log_message(f"{'='*60}", "INFO")
        self.log_message(f"Tổng số video: {len(results)}", "INFO")
        self.log_message(f"Thành công: {success_count}", "SUCCESS")
        self.log_message(f"Lỗi: {error_count}", "ERROR")
        self.log_message(f"{'='*60}\n", "INFO")

    def log_message(self, message, level="INFO"):
        """Ghi log message với màu sắc"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Print to console first (always safe)
        print(f"[{timestamp}] {level}: {message}")

        # Check if UI log widget exists
        if not hasattr(self, 'log_text') or not self.log_text:
            return

        # Color coding
        colors = {
            "INFO": ModernColors.TEXT_PRIMARY,
            "SUCCESS": ModernColors.SUCCESS,
            "WARNING": ModernColors.WARNING,
            "ERROR": ModernColors.ERROR
        }
        color = colors.get(level, ModernColors.TEXT_PRIMARY)

        log_entry = f"[{timestamp}] {level}: {message}\n"

        try:
            if CUSTOM_TK_AVAILABLE:
                self.log_text.insert("end", log_entry)
            else:
                self.log_text.configure(state=tk.NORMAL)
                self.log_text.insert(tk.END, log_entry)
                
                # Apply color tag to the inserted line
                # Get the line we just inserted (it's the one before "end")
                # "end-1c" is the last char, "end-1c linestart" is start of last line
                # But since we added \n, the last line is empty. So we want the line before that.
                start = self.log_text.index("end-2l linestart")
                end = self.log_text.index("end-2l lineend")
                
                tag_name = f"tag_{level}"
                self.log_text.tag_add(tag_name, start, end)
                self.log_text.tag_config(tag_name, foreground=color)
                
                self.log_text.configure(state=tk.DISABLED)

            # Auto scroll
            self.log_text.see("end")
            self.root.update_idletasks()
        except Exception as e:
            print(f"Error updating log UI: {e}")
        
    def clear_log(self):
        """Xóa log"""
        if CUSTOM_TK_AVAILABLE:
            self.log_text.delete("0.0", "end")
        else:
            # FIX: Enable widget temporarily to clear
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.log_message("Log đã được xóa")
        
    def update_progress(self, value, text=""):
        """Cập nhật tiến trình"""
        if CUSTOM_TK_AVAILABLE:
            self.progress_bar.set(value / 100)
        else:
            self.progress_var.set(value)
            
        if text:
            self.progress_label.configure(text=text)
            
        self.root.update_idletasks()
        
    def set_buttons_state(self, enabled=True):
        """Đặt trạng thái các nút"""
        # Luôn giữ nút start ở trạng thái "normal" để có thể chạy nhiều quá trình cùng lúc
        state = "normal" if enabled else "disabled"

        if CUSTOM_TK_AVAILABLE:
            # Nút start luôn bật
            self.start_btn.configure(state="normal")
            if enabled:
                self.stop_btn.configure(state="disabled")
            else:
                self.stop_btn.configure(state="normal")
        else:
            # Nút start luôn bật
            self.start_btn.configure(state="normal")
            if enabled:
                self.stop_btn.configure(state="disabled")
            else:
                self.stop_btn.configure(state="normal")
    
    # Thêm nút để lấy video IDs riêng biệt
    def add_get_videos_button(self):
        """Thêm nút lấy video IDs vào giao diện"""
        # Thêm nút này vào control section
        # Tìm button frame và thêm nút mới
        pass
        
    def run(self):
        """Chạy ứng dụng"""
        # Show the window if it was hidden during initialization - REMOVED
        # try:
        #     self.root.deiconify()
        # except:
        #     pass

        self.log_message("Ứng dụng YouTube Analytics Scraper đã khởi động", "SUCCESS")
        self.log_message("Sẵn sàng để sử dụng!")

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Xử lý khi đóng ứng dụng"""
        try:
            # Safely close any open dialogs or threads
            if hasattr(self, 'scraper') and self.scraper:
                self.scraper = None
            # Destroy the root window
            self.root.quit()
            self.root.destroy()
        except Exception as e:
            print(f"Error during shutdown: {e}")
            try:
                self.root.quit()
            except:
                pass


def main():
    """Hàm main"""
    try:
        app = YouTubeScraperGUI()
        app.run()
    except Exception as e:
        print(f"Lỗi khi khởi động ứng dụng: {e}")
        messagebox.showerror("Lỗi", f"Không thể khởi động ứng dụng:\n{e}")


if __name__ == "__main__":
    main()
