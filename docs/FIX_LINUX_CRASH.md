# 🐧 Linux Segmentation Fault Fix

## Issue
The application was crashing with a segmentation fault on Linux.

## Root Cause Analysis
1.  **System Tkinter**: Verified to be working correctly using a minimal test script.
2.  **CustomTkinter**: Identified as a potential source of instability on this specific Linux environment.
3.  **Tcl Patching**: The code intended to patch Tcl/Tk for CustomTkinter stability was actually **causing** crashes when used with standard Tkinter or applied incorrectly.

## Applied Fixes

### 1. Switched to Standard Tkinter
Disabled `CustomTkinter` to ensure maximum stability.
```python
CUSTOM_TK_AVAILABLE = False
```

### 2. Removed Tcl Patching
Disabled the `ttk::ThemeChanged` patch in `src/gui/app.py`. This patch is not needed for standard Tkinter and was interfering with the interpreter.

### 3. Disabled Icon Bitmap
Commented out `iconbitmap` as it causes crashes on Linux if the icon format is incorrect.

### 4. Simplified Window Maximization
Replaced OS-specific maximization with a safe geometry setting (90% screen size).

## Result
The application now starts and runs stably on Linux using standard Tkinter.
