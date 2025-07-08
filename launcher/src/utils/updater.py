import os
import sys
import subprocess
import time
import tkinter as tk
from tkinter import ttk


def get_base_directory():
    """Get the directory where the executable or script is located"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(__file__)


class UpdateProgress:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Updating...")
        self.root.geometry("300x80")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.eval('tk::PlaceWindow . center')
        
        # Remove window decorations for clean look
        self.root.overrideredirect(True)
        
        # Create progress bar
        self.progress = ttk.Progressbar(self.root, length=250, mode='determinate')
        self.progress.pack(pady=20)
        
        # Status label
        self.status = tk.Label(self.root, text="Initializing...", font=("Arial", 9))
        self.status.pack()
        
        self.root.update()
    
    def update_progress(self, value, status_text):
        self.progress['value'] = value
        self.status.config(text=status_text)
        self.root.update()
    
    def close(self):
        self.root.destroy()


def replace_file():
    """Replace FFTLauncher.exe with FFTLauncher.update"""
    progress = UpdateProgress()
    
    try:
        base_dir = get_base_directory()
        exe_file = os.path.join(base_dir, "FFTLauncher.exe")
        update_file = os.path.join(base_dir, "FFTLauncher.update")
        
        # Wait for the update file to appear (up to 30 seconds)
        progress.update_progress(10, "Waiting for update file...")
        found = False
        for i in range(30):
            if os.path.exists(update_file):
                found = True
                break
            progress.update_progress(10 + (i * 2), f"Waiting for update file... ({i+1}/30)")
            time.sleep(1)
        
        if not found:
            progress.update_progress(100, "Update file not found!")
            time.sleep(2)
            return False
        
        # Wait for file to be fully written
        progress.update_progress(70, "Preparing update...")
        time.sleep(2)
        
        # Remove the exe file if it exists
        progress.update_progress(80, "Removing old launcher...")
        if os.path.exists(exe_file):
            os.remove(exe_file)
        
        # Rename update file to exe
        progress.update_progress(90, "Installing update...")
        os.rename(update_file, exe_file)
        
        # Launch the new executable
        progress.update_progress(95, "Launching updated launcher...")
        subprocess.Popen([exe_file], creationflags=subprocess.CREATE_NO_WINDOW)
        
        progress.update_progress(100, "Update complete!")
        time.sleep(1)
        
        return True
        
    except Exception as e:
        progress.update_progress(100, "Update failed!")
        time.sleep(2)
        return False
    finally:
        progress.close()


def main():
    """Main entry point"""
    try:
        replace_file()
    except Exception:
        pass
    
    # Exit immediately without any output or pause
    sys.exit(0)


if __name__ == "__main__":
    main()
