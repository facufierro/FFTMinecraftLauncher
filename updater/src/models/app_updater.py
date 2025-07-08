"""
App Updater Model
----------------
Core implementation of the update functionality
"""

import os
import sys
import shutil
import psutil
import time
import subprocess
import requests


class AppUpdater:
    """Handles the core functionality of downloading and replacing application files"""
    
    def __init__(self):
        """Initialize the updater with default configuration"""
        self.base_dir = self._get_base_directory()
        self.target_file = "app.exe"  # File to replace
        self.github_repo = "facufierro/Updater"  # GitHub repo
        self.github_file_path = "dist/app.exe"  # Path to file in repo
        
    def _get_base_directory(self):
        """Get the directory where the executable or script is located"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        else:
            return os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    def close_target_app(self):
        """
        Close the target app if it's currently running
        
        Returns:
            bool: True if any processes were closed, False otherwise
        """
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
        """
        Download the latest file from GitHub repository
        
        Returns:
            str: Path to the downloaded temporary file
            
        Raises:
            Exception: If download fails
        """
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
        """
        Replace the target file with the downloaded version
        
        Args:
            new_file_path (str): Path to the new file
            
        Raises:
            Exception: If replacement fails
        """
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
        """
        Launch the target application
        
        Raises:
            Exception: If launch fails
        """
        target_path = os.path.join(self.base_dir, self.target_file)
        
        if os.path.exists(target_path):
            subprocess.Popen([target_path])
        else:
            raise Exception(f"Target file not found: {target_path}")
    
    def update_and_launch(self):
        """
        Main update process: download, replace, and launch
        
        Raises:
            Exception: If any part of the process fails
        """
        # Close running instances
        was_running = self.close_target_app()
        
        # Download new version
        temp_file = self.download_from_github()
        
        # Replace file
        self.replace_target_file(temp_file)
        
        # Launch updated app
        self.launch_target_app()
