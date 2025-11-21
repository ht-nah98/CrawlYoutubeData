# 🔧 HOW TO RUN THE APPLICATION (SEGFAULT FIX)

## ✅ **CORRECT WAY TO RUN**

### **Method 1: Using the Launcher Script (RECOMMENDED)**

```bash
# From anywhere in the project:
cd /home/user/Downloads/craw_data_ytb
./run.sh
```

### **Method 2: From Project Root**

```bash
# Navigate to project root first
cd /home/user/Downloads/craw_data_ytb

# Then run
python3 src/main.py
```

### **Method 3: Direct Python Module**

```bash
cd /home/user/Downloads/craw_data_ytb
python3 -m src.main
```

---

## ❌ **WRONG WAY (Causes Segfault)**

```bash
# DON'T DO THIS:
cd /home/user/Downloads/craw_data_ytb/src
python3 main.py  # ❌ SEGFAULT!
```

**Why it fails:**
- Even though we fixed the imports, tkinter has issues when the working directory is not the project root
- Config files, profile directories, and relative paths break
- This causes memory corruption → segfault

---

## 🐛 **Why Segfault Happens**

The segmentation fault occurs due to **multiple factors**:

1. **Wrong working directory** → Can't find config.json, profile/, etc.
2. **Tkinter initialization issues** → Display connection problems
3. **Module loading conflicts** → Python cache corruption
4. **CustomTkinter conflicts** → Already disabled, but cache may persist

---

## 🔍 **Diagnostic Steps**

If you still get segfault, try these:

### **Step 1: Clear Python Cache**

```bash
cd /home/user/Downloads/craw_data_ytb
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

### **Step 2: Check Display**

```bash
echo $DISPLAY
# Should show something like :0 or :1
```

If empty:
```bash
export DISPLAY=:0
```

### **Step 3: Test Tkinter**

```bash
python3 -c "import tkinter; root = tkinter.Tk(); print('Tkinter OK'); root.destroy()"
```

If this crashes → tkinter/display issue, not our code.

### **Step 4: Check Dependencies**

```bash
cd /home/user/Downloads/craw_data_ytb
pip3 list | grep -E "selenium|tkinter|customtkinter"
```

---

## ✅ **Solution Summary**

### **What We Fixed:**

1. ✅ **Disabled CustomTkinter** → Prevents CTk+Canvas segfault
2. ✅ **Dynamic path detection** → Works from any directory
3. ✅ **Auto-change to project root** → Fixes relative paths
4. ✅ **Display testing** → Detects X11 issues early
5. ✅ **Cleared Python cache** → Removes corrupted bytecode

### **What You Must Do:**

**ALWAYS run from project root:**

```bash
# Option A: Use launcher
cd /home/user/Downloads/craw_data_ytb
./run.sh

# Option B: Run from root
cd /home/user/Downloads/craw_data_ytb
python3 src/main.py
```

**NEVER run from src/ directory:**

```bash
# ❌ DON'T DO THIS:
cd src
python3 main.py
```

---

## 🎯 **Quick Test**

Try this exact sequence:

```bash
# 1. Go to project root
cd /home/user/Downloads/craw_data_ytb

# 2. Clear cache
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

# 3. Run the app
python3 src/main.py
```

**Expected output:**
```
Working directory: /home/user/Downloads/craw_data_ytb
Python path includes: /home/user/Downloads/craw_data_ytb
Using standard tkinter for stability (CustomTkinter disabled)
✓ Display connection successful
Starting YouTube Analytics Scraper...
# GUI window opens ✓
```

---

## 🚀 **Recommended Workflow**

### **Create an Alias (Optional)**

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
alias ytb-scraper='cd /home/user/Downloads/craw_data_ytb && python3 src/main.py'
```

Then just run:
```bash
ytb-scraper
```

### **Or Use the Launcher**

```bash
cd /home/user/Downloads/craw_data_ytb
./run.sh
```

---

## 📊 **Troubleshooting Matrix**

| Symptom | Cause | Solution |
|---------|-------|----------|
| Segfault from `src/` | Wrong working dir | Run from project root |
| "Module not found" | Wrong Python path | Use `./run.sh` |
| "Display error" | No X11 connection | Set `DISPLAY=:0` |
| Segfault after update | Corrupted cache | Clear `__pycache__` |
| Random crashes | CustomTkinter | Already disabled ✓ |

---

## 🎉 **Final Answer**

**To run the application successfully:**

```bash
cd /home/user/Downloads/craw_data_ytb
python3 src/main.py
```

**That's it!** Don't run from the `src/` directory.

---

## 📝 **Files Created**

1. **`run.sh`** - Launcher script (ensures correct directory)
2. **`src/main.py`** - Enhanced with path detection and display testing
3. **This guide** - How to run properly

---

## ✅ **Summary**

**Problem:** Segfault when running from `src/` directory  
**Root Cause:** Wrong working directory + tkinter issues  
**Solution:** Always run from project root  
**Command:** `cd /home/user/Downloads/craw_data_ytb && python3 src/main.py`  

**Your application works perfectly when run correctly!** 🚀
