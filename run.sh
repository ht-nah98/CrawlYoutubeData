#!/bin/bash
# YouTube Analytics Scraper Launcher
# Always run from project root to avoid import issues

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to project root
cd "$SCRIPT_DIR"

# Run the application
python3 src/main.py
