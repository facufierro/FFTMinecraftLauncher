import tkinter as tk
from tkinter import messagebox
import subprocess
import os
import sys
import shutil
import psutil
import time
import requests
from pathlib import Path


class AppUpdater:
    def __init__(self):
        self.base_dir = self._get_base_directory()
        self.target_file = "app.exe"  # File to replace
        self.github_repo = "facufierro/Updater"  # GitHub repo
        self.github_file_path = "dist/app.exe"  # Path to file in repo
        
    def _get_base_directory(self):
        """Get the directory where the executable or script is located"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(__file__)
    
    def close_target_app(self):
        """Close the target app if it's currently running"""
        closed_processes = []
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'].lower() == self.target_file.lower():
                    proc.terminate()
                    closed_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if closed_processes:
            # Wait for graceful termination
            psutil.wait_procs(closed_processes, timeout=5)
            
            # Force kill if still running
            for proc in closed_processes:
                try:
                    if proc.is_running():
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            time.sleep(1)  # Allow file handles to release
        
        return len(closed_processes) > 0
    
    def download_from_github(self):
        """Download the latest file from GitHub repository"""
        try:
            # Construct GitHub raw URL
            url = f"https://raw.githubusercontent.com/{self.github_repo}/main/{self.github_file_path}"
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save to temporary file
            temp_file = os.path.join(self.base_dir, f"{self.target_file}.tmp")
            with open(temp_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return temp_file
            
        except requests.RequestException as e:
            raise Exception(f"Failed to download from GitHub: {e}")
    
    def replace_target_file(self, new_file_path):
        """Replace the target file with the downloaded version"""
        target_path = os.path.join(self.base_dir, self.target_file)
        backup_path = os.path.join(self.base_dir, f"{self.target_file}.backup")
        
        try:
            # Create backup of current file
            if os.path.exists(target_path):
                shutil.copy2(target_path, backup_path)
            
            # Replace with new file
            shutil.move(new_file_path, target_path)
            
            # Remove backup if successful
            if os.path.exists(backup_path):
                os.remove(backup_path)
                
        except Exception as e:
            # Restore backup if replacement failed
            if os.path.exists(backup_path):
                shutil.move(backup_path, target_path)
            raise Exception(f"Failed to replace file: {e}")
    
    def launch_target_app(self):
        """Launch the target application"""
        target_path = os.path.join(self.base_dir, self.target_file)
        
        if os.path.exists(target_path):
            subprocess.Popen([target_path])
        else:
            raise Exception(f"Target file not found: {target_path}")
    
    def update_and_launch(self):
        """Main update process: download, replace, and launch"""
        try:
            # Close running instances
            was_running = self.close_target_app()
            if was_running:
                print("Closed running app instance")
            
            # Download new version
            print("Downloading update from GitHub...")
            temp_file = self.download_from_github()
            
            # Replace file
            print("Installing update...")
            self.replace_target_file(temp_file)
            
            print("Update completed successfully")
            messagebox.showinfo("Update Complete", "Application updated successfully!")
            
            # Launch updated app
            self.launch_target_app()
            
        except Exception as e:
            print(f"Update failed: {e}")
            messagebox.showerror("Update Failed", f"Failed to update application:\n{e}")
            
            # Try to launch existing app anyway
            try:
                self.launch_target_app()
            except Exception as launch_error:
                messagebox.showerror("Launch Failed", f"Could not launch application:\n{launch_error}")


class UpdaterGUI:
    def __init__(self):
        self.updater = AppUpdater()
        self.setup_ui()
    
    def setup_ui(self):
        """Create the user interface"""
        self.root = tk.Tk()
        self.root.title("App Updater")
        self.root.resizable(False, False)
        
        # Main button
        self.update_button = tk.Button(
            self.root, 
            text="Update & Launch", 
            command=self.on_update_click,
            width=20, 
            height=2,
            font=("Arial", 10)
        )
        self.update_button.pack(padx=40, pady=40)
        
        # Center window
        self.center_window()
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_update_click(self):
        """Handle update button click"""
        self.update_button.config(state="disabled", text="Updating...")
        self.root.update()
        
        try:
            self.updater.update_and_launch()
            self.root.destroy()
        except Exception as e:
            self.update_button.config(state="normal", text="Update & Launch")
            print(f"Update process failed: {e}")
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


def main():
    """Main entry point"""
    app = UpdaterGUI()
    app.run()


if __name__ == "__main__":
    main()
