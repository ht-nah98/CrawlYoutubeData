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

# CRITICAL: Patch Tcl BEFORE any tkinter import to prevent segmentation fault
# This must happen before tkinter is imported
os.environ['TK_SILENCE_DEPRECATION'] = '1'

# Tcl patching is now handled inside YouTubeScraperGUI.__init__
# to ensure it applies to the actual application interpreter

# Import tkinter AFTER patching
import tkinter as tk

# Display test removed to prevent extra Tk instance creation
# The main app initialization will catch display errors if they occur

from src.gui.app import YouTubeScraperGUI


def main():
    """Main entry point for GUI application"""
    try:
        print("Starting YouTube Analytics Scraper...")
        app = YouTubeScraperGUI()
        app.run()
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
