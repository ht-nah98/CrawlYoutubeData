#!/usr/bin/env python3
"""
YouTube Analytics Scraper - GUI Entry Point

This is the main entry point for the GUI application.
Run this file to start the scraper with the graphical interface.

Usage:
    From project root: python3 src/main.py
    From src directory: python3 main.py
    Using launcher: ./run.sh
"""

import sys
import os

# Dynamically add project root to path
# Get the directory where this script is located (src/)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get parent directory (project root)
project_root = os.path.dirname(script_dir)
# Add to Python path
sys.path.insert(0, project_root)

# Change working directory to project root to fix relative paths
os.chdir(project_root)

print(f"Working directory: {os.getcwd()}")
print(f"Python path includes: {project_root}")

# Import tkinter AFTER setting up paths
import tkinter as tk

# Test if display is available
try:
    test_root = tk.Tk()
    test_root.withdraw()
    test_root.destroy()
    print("✓ Display connection successful")
except Exception as e:
    print(f"✗ Display error: {e}")
    print("\nPossible solutions:")
    print("1. Make sure you're running in a graphical environment")
    print("2. If using SSH, enable X11 forwarding: ssh -X user@host")
    print("3. Set DISPLAY variable: export DISPLAY=:0")
    sys.exit(1)

from src.gui.app import YouTubeScraperGUI


def main():
    """Main entry point for GUI application"""
    try:
        print("Starting YouTube Analytics Scraper...")
        app = YouTubeScraperGUI()
        app.root.mainloop()
    except KeyboardInterrupt:
        print("\n✓ Application closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error starting application: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
