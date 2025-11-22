@echo off
REM Fix ChromeDriver for Windows
REM This script clears the webdriver-manager cache and reinstalls it properly

echo ========================================
echo  ChromeDriver Windows Fix Script
echo ========================================
echo.

echo [1/4] Stopping any running Chrome processes...
taskkill /F /IM chrome.exe /T 2>nul
taskkill /F /IM chromedriver.exe /T 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [2/4] Clearing webdriver-manager cache...
if exist "%USERPROFILE%\.wdm" (
    echo Found cache directory: %USERPROFILE%\.wdm
    rmdir /S /Q "%USERPROFILE%\.wdm"
    echo Cache cleared successfully!
) else (
    echo No cache directory found.
)

echo.
echo [3/4] Uninstalling old webdriver-manager...
pip uninstall webdriver-manager -y

echo.
echo [4/4] Installing fresh webdriver-manager...
pip install webdriver-manager

echo.
echo ========================================
echo  Fix Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Close this window
echo 2. Restart your YouTube Analytics Scraper
echo 3. Try adding a new account
echo.
pause
