"""
Main GUI Window
Simplified version demonstrating the new architecture
"""

import customtkinter as ctk
from tkinter import messagebox
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api_client.client import BackendAPIClient
from src.storage.config import config


class MainWindow(ctk.CTk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize API client
        self.api_client = BackendAPIClient(config.backend_url)
        
        # Configure window
        self.title("YouTube Analytics - GUI Client")
        self.geometry(config.window_size)
        
        # Set theme
        ctk.set_appearance_mode(config.theme)
        ctk.set_default_color_theme("blue")
        
        # Create UI
        self._create_ui()
        
        # Check backend connection
        self.after(500, self._check_backend)
    
    def _create_ui(self):
        """Create user interface"""
        # Main container
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Header
        self._create_header()
        
        # Content area (tabview)
        self._create_content()
        
        # Status bar
        self._create_status_bar()
    
    def _create_header(self):
        """Create header section"""
        header_frame = ctk.CTkFrame(self, height=80, corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            header_frame,
            text="📺 YouTube Analytics",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=20, sticky="w")
        
        # Backend status
        self.status_label = ctk.CTkLabel(
            header_frame,
            text="⚪ Connecting to backend...",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.grid(row=0, column=1, padx=20, pady=20, sticky="e")
        
        # Settings button
        settings_btn = ctk.CTkButton(
            header_frame,
            text="⚙️ Settings",
            width=100,
            command=self._show_settings
        )
        settings_btn.grid(row=0, column=2, padx=20, pady=20)
    
    def _create_content(self):
        """Create main content area"""
        # Create tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        
        # Add tabs
        self.tabview.add("📊 Dashboard")
        self.tabview.add("👤 Accounts")
        self.tabview.add("📺 Channels")
        self.tabview.add("🎥 Videos")
        self.tabview.add("📈 Analytics")
        
        # Dashboard tab
        self._create_dashboard_tab()
        
        # Accounts tab
        self._create_accounts_tab()
        
        # Other tabs (placeholder)
        for tab_name in ["📺 Channels", "🎥 Videos", "📈 Analytics"]:
            placeholder = ctk.CTkLabel(
                self.tabview.tab(tab_name),
                text=f"{tab_name}\n\nThis tab will be implemented in the full version.\nFor now, this demonstrates the new architecture.",
                font=ctk.CTkFont(size=14)
            )
            placeholder.pack(expand=True)
    
    def _create_dashboard_tab(self):
        """Create dashboard tab"""
        dashboard = self.tabview.tab("📊 Dashboard")
        
        # Welcome message
        welcome_frame = ctk.CTkFrame(dashboard)
        welcome_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        welcome_label = ctk.CTkLabel(
            welcome_frame,
            text="Welcome to YouTube Analytics GUI Client",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        welcome_label.pack(pady=(20, 10))
        
        info_label = ctk.CTkLabel(
            welcome_frame,
            text="This is the new modular GUI client that connects to the backend API.\n\n"
                 "✅ Backend server running independently\n"
                 "✅ Clean separation of concerns\n"
                 "✅ API-based communication\n"
                 "✅ Ready for Windows .exe build",
            font=ctk.CTkFont(size=14),
            justify="left"
        )
        info_label.pack(pady=10)
        
        # Connection test button
        test_btn = ctk.CTkButton(
            welcome_frame,
            text="🔄 Test Backend Connection",
            command=self._test_connection,
            height=40
        )
        test_btn.pack(pady=20)
        
        # Stats display
        self.stats_label = ctk.CTkLabel(
            welcome_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.stats_label.pack(pady=10)
    
    def _create_accounts_tab(self):
        """Create accounts tab"""
        accounts_tab = self.tabview.tab("👤 Accounts")
        
        # Toolbar
        toolbar = ctk.CTkFrame(accounts_tab, height=50)
        toolbar.pack(fill="x", padx=10, pady=10)
        
        refresh_btn = ctk.CTkButton(
            toolbar,
            text="🔄 Refresh",
            command=self._load_accounts,
            width=100
        )
        refresh_btn.pack(side="left", padx=5)
        
        # Accounts list
        self.accounts_text = ctk.CTkTextbox(accounts_tab, height=400)
        self.accounts_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Load accounts
        self._load_accounts()
    
    def _create_status_bar(self):
        """Create status bar"""
        status_frame = ctk.CTkFrame(self, height=30, corner_radius=0)
        status_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        
        self.status_text = ctk.CTkLabel(
            status_frame,
            text=f"Backend: {config.backend_url}",
            font=ctk.CTkFont(size=10)
        )
        self.status_text.pack(side="left", padx=10, pady=5)
    
    def _check_backend(self):
        """Check backend connection"""
        try:
            if self.api_client.health_check():
                self.status_label.configure(
                    text="🟢 Backend Connected",
                    text_color="green"
                )
                self._update_stats()
            else:
                self.status_label.configure(
                    text="🔴 Backend Disconnected",
                    text_color="red"
                )
                messagebox.showwarning(
                    "Backend Connection",
                    f"Cannot connect to backend server at {config.backend_url}\n\n"
                    "Please make sure the backend server is running:\n"
                    "  cd backend\n"
                    "  python server.py"
                )
        except Exception as e:
            self.status_label.configure(
                text="🔴 Connection Error",
                text_color="red"
            )
            messagebox.showerror("Connection Error", str(e))
    
    def _test_connection(self):
        """Test backend connection"""
        try:
            if self.api_client.health_check():
                info = self.api_client.get_api_info()
                messagebox.showinfo(
                    "Connection Test",
                    f"✅ Successfully connected to backend!\n\n"
                    f"API: {info.get('name', 'Unknown')}\n"
                    f"Version: {info.get('version', 'Unknown')}"
                )
                self._update_stats()
            else:
                messagebox.showerror(
                    "Connection Test",
                    "❌ Cannot connect to backend server"
                )
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
    
    def _update_stats(self):
        """Update statistics display"""
        try:
            accounts = self.api_client.get_accounts()
            channels = self.api_client.get_channels()
            videos = self.api_client.get_videos(limit=1000)
            
            stats_text = (
                f"📊 Current Statistics:\n\n"
                f"Accounts: {len(accounts)}\n"
                f"Channels: {len(channels)}\n"
                f"Videos: {len(videos)}"
            )
            self.stats_label.configure(text=stats_text)
        except Exception as e:
            self.stats_label.configure(text=f"Error loading stats: {e}")
    
    def _load_accounts(self):
        """Load accounts from backend"""
        try:
            accounts = self.api_client.get_accounts()
            
            self.accounts_text.delete("1.0", "end")
            
            if not accounts:
                self.accounts_text.insert("1.0", "No accounts found.\n\nCreate an account using the backend API or the original GUI.")
            else:
                self.accounts_text.insert("1.0", f"Found {len(accounts)} account(s):\n\n")
                
                for i, account in enumerate(accounts, 1):
                    account_info = (
                        f"{i}. {account.get('name', 'Unknown')}\n"
                        f"   ID: {account.get('id')}\n"
                        f"   Cookies: {account.get('cookies_file', 'N/A')}\n"
                        f"   Created: {account.get('created_at', 'N/A')}\n\n"
                    )
                    self.accounts_text.insert("end", account_info)
        except Exception as e:
            self.accounts_text.delete("1.0", "end")
            self.accounts_text.insert("1.0", f"Error loading accounts: {e}")
    
    def _show_settings(self):
        """Show settings dialog"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        
        # Backend URL
        url_label = ctk.CTkLabel(settings_window, text="Backend URL:")
        url_label.pack(pady=(20, 5))
        
        url_entry = ctk.CTkEntry(settings_window, width=300)
        url_entry.insert(0, config.backend_url)
        url_entry.pack(pady=5)
        
        # Theme
        theme_label = ctk.CTkLabel(settings_window, text="Theme:")
        theme_label.pack(pady=(20, 5))
        
        theme_var = ctk.StringVar(value=config.theme)
        theme_menu = ctk.CTkOptionMenu(
            settings_window,
            values=["dark", "light", "system"],
            variable=theme_var
        )
        theme_menu.pack(pady=5)
        
        # Save button
        def save_settings():
            config.backend_url = url_entry.get()
            config.theme = theme_var.get()
            ctk.set_appearance_mode(config.theme)
            self.api_client = BackendAPIClient(config.backend_url)
            settings_window.destroy()
            self._check_backend()
        
        save_btn = ctk.CTkButton(
            settings_window,
            text="Save Settings",
            command=save_settings
        )
        save_btn.pack(pady=20)


def main():
    """Main entry point"""
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
