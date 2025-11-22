@echo off
REM YouTube Analytics GUI Client Startup Script

echo ========================================
echo YouTube Analytics - GUI Client
echo ========================================
echo.

REM Check if venv exists
if not exist "..\venv\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    echo Please run this from the gui directory
    pause
    exit /b 1
)

echo Starting GUI application...
echo.
echo Make sure the backend server is running!
echo   Backend should be at: http://localhost:8000
echo.
echo ========================================
echo.

REM Start the GUI
..\venv\Scripts\python.exe main.py

pause
