#!/usr/bin/env python3
"""
YouTube Analytics GUI Client
Main entry point for the desktop application

This is the new modular GUI that connects to the backend API server.

Usage:
    python main.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.main_window import MainWindow


def main():
    """Start GUI application"""
    try:
        print("=" * 60)
        print("YouTube Analytics - GUI Client")
        print("=" * 60)
        print("Starting application...")
        print()
        
        app = MainWindow()
        app.mainloop()
        
    except KeyboardInterrupt:
        print("\n\n✓ Application closed by user")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n\n✗ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
