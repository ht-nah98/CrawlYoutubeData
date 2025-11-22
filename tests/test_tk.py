import tkinter as tk
import sys

print("1. Importing tkinter...")
try:
    root = tk.Tk()
    print("2. Root created.")
    
    root.title("Test Window")
    print("3. Title set.")
    
    label = tk.Label(root, text="If you see this, Tkinter is working.")
    label.pack(padx=20, pady=20)
    print("4. Label packed.")
    
    # Center window
    root.geometry("300x200")
    print("5. Geometry set.")
    
    print("6. Starting mainloop...")
    root.mainloop()
    print("7. Mainloop finished.")
    
except Exception as e:
    print(f"ERROR: {e}")
