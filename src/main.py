#!/usr/bin/env python3
"""
YouTube Analytics Scraper - GUI Entry Point

This is the main entry point for the GUI application.
Run this file to start the scraper with the graphical interface.

Usage:
    python3 -m src.main
    or
    python3 src/main.py
"""

import sys
import tkinter as tk

# Add parent directory to path for imports
sys.path.insert(0, '/home/user/Downloads/craw_data_ytb')

from src.gui.app import YouTubeScraperGUI


def main():
    """Main entry point for GUI application"""
    try:
        root = tk.Tk()
        app = YouTubeScraperGUI(root)
        root.mainloop()
    except KeyboardInterrupt:
        print("\n✓ Application closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Error starting application: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
