@echo off
REM YouTube Analytics Backend Server Startup Script
REM This script starts the backend server using the existing venv

echo ========================================
echo YouTube Analytics Backend Server
echo ========================================
echo.

REM Check if venv exists
if not exist "..\venv\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    echo Please run this from the backend directory
    pause
    exit /b 1
)

echo Starting server...
echo.
echo Server will be available at:
echo   - API: http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start the server
..\venv\Scripts\python.exe server.py

pause
