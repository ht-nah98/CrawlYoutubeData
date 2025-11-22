# 🪟 Windows Setup Guide - YouTube Analytics Scraper

## ✅ Quick Fix for ChromeDriver Error

If you're seeing the error: `[WinError 193] %1 is not a valid Win32 application`, follow these steps:

### **Option 1: Automatic Fix (Recommended)**

1. **Run the fix script:**
   ```cmd
   fix_chromedriver_windows.bat
   ```
   
2. **Wait for completion** (this will clear cache and reinstall webdriver-manager)

3. **Restart the application:**
   ```cmd
   .\venv\Scripts\activate
   python src/main.py
   ```

### **Option 2: Manual Fix**

1. **Close the application** if it's running

2. **Open Command Prompt** in the project directory

3. **Activate virtual environment:**
   ```cmd
   .\venv\Scripts\activate
   ```

4. **Clear webdriver-manager cache:**
   ```cmd
   rmdir /S /Q "%USERPROFILE%\.wdm"
   ```

5. **Reinstall webdriver-manager:**
   ```cmd
   pip uninstall webdriver-manager -y
   pip install webdriver-manager
   ```

6. **Restart the application:**
   ```cmd
   python src/main.py
   ```

---

## 🔧 What Was Fixed?

The application was originally developed on **Ubuntu Linux**, and the webdriver-manager cached a **Linux version of ChromeDriver**. When running on Windows, this causes the error because Windows cannot execute Linux binaries.

### **Changes Made:**

1. **Platform Detection** - The code now detects Windows vs Linux
2. **Cache Clearing** - Automatically clears old Linux ChromeDriver cache on Windows
3. **Proper Download** - Downloads the correct Windows ChromeDriver
4. **Better Error Messages** - Shows helpful instructions if something goes wrong

---

## 📋 System Requirements for Windows

### **Required Software:**

✅ **Windows 10/11** (64-bit)  
✅ **Python 3.8+** (Python 3.10+ recommended)  
✅ **PostgreSQL 12+** (for database)  
✅ **Google Chrome** (latest version)  
✅ **At least 2GB RAM** and **500MB disk space**

### **Check Your Setup:**

```cmd
# Check Python version
python --version

# Check pip
pip --version

# Check PostgreSQL
psql --version

# Check Chrome (open Chrome and go to: chrome://version/)
```

---

## 🚀 Complete Windows Installation

### **Step 1: Install Python**

1. Download from [python.org](https://www.python.org/downloads/)
2. **✅ IMPORTANT:** Check "Add Python to PATH" during installation
3. Verify: `python --version`

### **Step 2: Install PostgreSQL**

1. Download from [postgresql.org](https://www.postgresql.org/download/windows/)
2. During installation:
   - Set password for `postgres` user (remember this!)
   - Use default port `5432`
   - Check "Add PostgreSQL to PATH"
3. Verify: `psql --version`

### **Step 3: Install Google Chrome**

1. Download from [google.com/chrome](https://www.google.com/chrome/)
2. Install normally
3. **Note:** ChromeDriver will be auto-downloaded by the app

### **Step 4: Clone/Download Project**

```cmd
git clone https://gitlab.com/hg-media/crawl-data.git
cd crawl-data
```

Or download ZIP and extract.

### **Step 5: Create Virtual Environment**

```cmd
python -m venv venv
.\venv\Scripts\activate
```

You should see `(venv)` at the start of your command prompt.

### **Step 6: Install Dependencies**

```cmd
pip install -r requirements.txt
```

**If you get errors**, try:
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### **Step 7: Configure Environment**

1. **Copy environment template:**
   ```cmd
   copy .env.example .env
   ```

2. **Edit `.env` file** (use Notepad or VS Code):
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   DB_NAME=youtube_analytics
   DB_ECHO=false
   
   API_HOST=0.0.0.0
   API_PORT=8000
   API_DEBUG=false
   ```

### **Step 8: Initialize Database**

```cmd
python scripts/setup/init_db.py
```

You should see: `✓ Database tables created successfully`

### **Step 9: Run the Application**

**Option A: GUI Application**
```cmd
python src/main.py
```

**Option B: API Server**
```cmd
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Option C: Both (use 2 terminals)**
- Terminal 1: `python -m uvicorn src.api.main:app --reload`
- Terminal 2: `python src/main.py`

---

## 🐛 Common Windows Issues

### **Issue: "Python not found"**

**Solution:**
- Reinstall Python with "Add to PATH" checked
- Or manually add Python to PATH:
  1. Search "Environment Variables" in Windows
  2. Edit PATH variable
  3. Add: `C:\Users\YourName\AppData\Local\Programs\Python\Python3XX`

### **Issue: "pip not found"**

**Solution:**
```cmd
python -m ensurepip --upgrade
python -m pip install --upgrade pip
```

### **Issue: "PostgreSQL connection failed"**

**Solution:**
- Check PostgreSQL is running (Services → postgresql-x64-XX)
- Verify credentials in `.env` file
- Test connection: `psql -U postgres -d youtube_analytics`

### **Issue: "Module not found"**

**Solution:**
```cmd
# Make sure venv is activated
.\venv\Scripts\activate

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### **Issue: "Chrome driver session not created"**

**Solution:**
1. Run `fix_chromedriver_windows.bat`
2. Or manually clear cache and reinstall (see Quick Fix above)

### **Issue: "Access Denied" when deleting cache**

**Solution:**
- Close all Chrome windows
- Run Command Prompt as Administrator
- Try again

---

## 🎯 Windows-Specific Tips

### **1. Use PowerShell or CMD**
Both work fine. PowerShell is recommended for better Unicode support.

### **2. Activate Virtual Environment**
Always activate before running:
```cmd
.\venv\Scripts\activate
```

To deactivate:
```cmd
deactivate
```

### **3. Check Firewall**
If API doesn't work, allow Python through Windows Firewall:
- Settings → Windows Security → Firewall
- Allow Python through firewall

### **4. Antivirus**
Some antivirus software may block ChromeDriver. Add exception for:
- Project folder
- `%USERPROFILE%\.wdm` folder

### **5. Long Path Support**
If you get "path too long" errors:
```cmd
# Run as Administrator
reg add HKLM\SYSTEM\CurrentControlSet\Control\FileSystem /v LongPathsEnabled /t REG_DWORD /d 1 /f
```

---

## 📁 Windows File Paths

The application uses these directories on Windows:

```
C:\Users\YourName\OneDrive\Máy tính\Crawl-Data\
├── data\
│   └── cookies\
│       └── profile\          # YouTube cookies
├── venv\                     # Virtual environment
├── src\                      # Source code
└── .env                      # Configuration
```

**Cache locations:**
- ChromeDriver: `C:\Users\YourName\.wdm\`
- Temp files: `C:\Users\YourName\AppData\Local\Temp\`

---

## 🔄 Updating the Application

```cmd
# Activate venv
.\venv\Scripts\activate

# Pull latest changes
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart application
python src/main.py
```

---

## 📞 Getting Help

If you're still having issues:

1. **Check the logs** in the GUI application
2. **Look for error messages** in Command Prompt
3. **Verify all requirements** are installed
4. **Try the fix script** again
5. **Check PostgreSQL** is running

---

## ✅ Verification Checklist

Before using the application, verify:

- [ ] Python 3.8+ installed and in PATH
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list`)
- [ ] PostgreSQL installed and running
- [ ] Database created and initialized
- [ ] `.env` file configured correctly
- [ ] Google Chrome installed
- [ ] ChromeDriver cache cleared (if migrating from Linux)
- [ ] No antivirus blocking the application

---

## 🎉 You're Ready!

Once everything is set up:

1. **Start the GUI:** `python src/main.py`
2. **Add a YouTube account** using the "➕ Tài khoản mới" button
3. **Add channels** to your account
4. **Fetch videos** from channels
5. **Scrape analytics** data

Enjoy your YouTube Analytics Scraper on Windows! 🚀
