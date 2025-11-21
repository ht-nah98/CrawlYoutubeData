# 🐛 Segmentation Fault Fix

## Issue
The application was crashing with a segmentation fault (`can't invoke "event" command: application has been destroyed`) when starting up.

## Cause
The Tcl/Tk patch intended to fix this crash was being applied to a **temporary** `Tk` instance in `src/main.py` (and previously `src/gui/app.py`) which was then destroyed.
When `CustomTkinter` created the **actual** application window (`ctk.CTk()`), it initialized a **new** Tcl interpreter that did NOT have the patch applied. This left the application vulnerable to the crash when theme events occurred.

## Solution
1. **Moved Patching Logic**: Moved the Tcl patching code into `YouTubeScraperGUI.__init__` in `src/gui/app.py`.
2. **Applied to Active Root**: The patch is now applied directly to `self.root` (the main application window) immediately after it is created. This ensures the active Tcl interpreter is patched.
3. **Cleaned up main.py**: Removed the ineffective patching code from `src/main.py` to avoid confusion and unnecessary overhead.
4. **Fixed Window Visibility**: Updated `src/main.py` to call `app.run()` instead of `app.root.mainloop()`, ensuring the window is properly shown (`deiconify`) after initialization.

## Result
The application now correctly patches the active Tcl interpreter and manages window visibility, preventing segmentation faults and "hanging" behavior.
