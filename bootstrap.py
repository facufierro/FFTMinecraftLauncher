#!/usr/bin/env python3
"""
FFT Minecraft Launcher Bootstrap

This is a small, stable launcher that handles updates and starts the main application.
The bootstrap rarely changes, while the main launcher can be updated frequently.
"""

import os
import sys
import json
import shutil
import zipfile
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import requests
import tkinter as tk
from tkinter import ttk, messagebox


class BootstrapUpdater:
    """Handles checking for and applying launcher updates."""
    
    def __init__(self):
        self.launcher_repo = "facufierro/FFTMinecraftLauncher"
        self.base_url = "https://api.github.com"
        self.timeout = 30
        self.launcher_dir = Path("launcher")
        self.version_file = self.launcher_dir / "version.json"
        
    def get_current_version(self) -> str:
        """Get the current launcher version."""
        try:
            if self.version_file.exists():
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    return data.get('version', '0.0.0')
        except Exception:
            pass
        return "0.0.0"
    
    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """Check if a launcher update is available."""
        try:
            # Get latest release from GitHub
            url = f"{self.base_url}/repos/{self.launcher_repo}/releases/latest"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            release_data = response.json()
            latest_version = release_data.get('tag_name', '').lstrip('v')
            current_version = self.get_current_version()
            
            if self._is_newer_version(latest_version, current_version):
                # Find download URL for launcher package
                download_url = self._get_launcher_download_url(release_data)
                if download_url:
                    return {
                        'version': latest_version,
                        'download_url': download_url,
                        'release_notes': release_data.get('body', '')
                    }
            
            return None
            
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return None
    
    def _get_launcher_download_url(self, release_data: Dict[str, Any]) -> Optional[str]:
        """Get download URL for the launcher package."""
        assets = release_data.get('assets', [])
        
        # Look for zip file containing launcher
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.zip') and 'launcher' in name:
                return asset.get('browser_download_url')
        
        return None
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings."""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except (ValueError, AttributeError):
            return latest != current
    
    def download_and_install_update(self, update_info: Dict[str, Any], progress_callback=None) -> bool:
        """Download and install launcher update."""
        try:
            download_url = update_info['download_url']
            version = update_info['version']
            
            # Create temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                zip_file = temp_path / "launcher_update.zip"
                
                # Download
                if progress_callback:
                    progress_callback("Downloading update...")
                
                response = requests.get(download_url, stream=True, timeout=self.timeout)
                response.raise_for_status()
                
                with open(zip_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Backup current launcher
                backup_dir = Path("launcher_backup")
                if self.launcher_dir.exists():
                    if backup_dir.exists():
                        shutil.rmtree(backup_dir)
                    shutil.move(str(self.launcher_dir), str(backup_dir))
                
                # Extract new launcher
                if progress_callback:
                    progress_callback("Installing update...")
                
                self.launcher_dir.mkdir(exist_ok=True)
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(self.launcher_dir)
                
                # Write version info
                version_data = {
                    'version': version,
                    'updated_at': str(Path().cwd())  # timestamp could be added
                }
                with open(self.version_file, 'w') as f:
                    json.dump(version_data, f, indent=2)
                
                # Clean up backup on success
                if backup_dir.exists():
                    shutil.rmtree(backup_dir)
                
                return True
                
        except Exception as e:
            print(f"Error installing update: {e}")
            # Restore backup if it exists
            backup_dir = Path("launcher_backup")
            if backup_dir.exists() and not self.launcher_dir.exists():
                shutil.move(str(backup_dir), str(self.launcher_dir))
            return False


class BootstrapGUI:
    """Simple GUI for the bootstrap process."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FFT Minecraft Launcher")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        # Center window
        self.root.eval('tk::PlaceWindow . center')
        
        self.updater = BootstrapUpdater()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the bootstrap UI."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="FFT Minecraft Launcher", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="Checking for updates...")
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 20))
        self.progress.start()
        
        # Start update check
        self.root.after(500, self.check_updates)
    
    def check_updates(self):
        """Check for launcher updates."""
        try:
            update_info = self.updater.check_for_updates()
            
            if update_info:
                self.progress.stop()
                self.progress.configure(mode='determinate', value=0)
                
                # Ask user if they want to update
                result = messagebox.askyesno(
                    "Update Available",
                    f"A new version ({update_info['version']}) is available.\n\n"
                    f"Would you like to update now?\n\n"
                    f"Release notes:\n{update_info['release_notes'][:200]}..."
                )
                
                if result:
                    self.install_update(update_info)
                else:
                    self.launch_app()
            else:
                self.launch_app()
                
        except Exception as e:
            print(f"Error during update check: {e}")
            self.launch_app()
    
    def install_update(self, update_info: Dict[str, Any]):
        """Install the update."""
        def progress_callback(message: str):
            self.status_label.configure(text=message)
            self.root.update()
        
        success = self.updater.download_and_install_update(update_info, progress_callback)
        
        if success:
            self.status_label.configure(text="Update completed! Starting launcher...")
            self.root.after(1000, self.launch_app)
        else:
            messagebox.showerror("Update Failed", "Failed to install update. Starting current version...")
            self.launch_app()
    
    def launch_app(self):
        """Launch the main launcher application."""
        self.status_label.configure(text="Starting launcher...")
        self.progress.stop()
        
        try:
            launcher_dir = Path("launcher")
            
            # Look for main launcher script or executable
            main_script = None
            for potential_main in ["app.py", "main.py", "launcher.py", "FFTMinecraftLauncher.exe"]:
                potential_path = launcher_dir / potential_main
                if potential_path.exists():
                    main_script = potential_path
                    break
            
            if not main_script:
                messagebox.showerror(
                    "Launch Error", 
                    "Could not find main launcher application.\n"
                    "Please reinstall the launcher."
                )
                self.root.quit()
                return
            
            # Launch the main application
            if main_script.suffix == '.py':
                # Python script
                subprocess.Popen([sys.executable, str(main_script)], 
                               cwd=launcher_dir)
            else:
                # Executable
                subprocess.Popen([str(main_script)], cwd=launcher_dir)
            
            # Close bootstrap
            self.root.quit()
            
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to start launcher: {e}")
            self.root.quit()
    
    def run(self):
        """Run the bootstrap GUI."""
        self.root.mainloop()


def main():
    """Main bootstrap entry point."""
    try:
        # Check if launcher directory exists
        launcher_dir = Path("launcher")
        if not launcher_dir.exists():
            # First time setup - create GUI to download initial version
            print("First time setup - launcher directory not found")
        
        # Run bootstrap GUI
        bootstrap = BootstrapGUI()
        bootstrap.run()
        
    except Exception as e:
        print(f"Bootstrap error: {e}")
        # Fallback: try to launch directly if possible
        launcher_dir = Path("launcher")
        if launcher_dir.exists():
            app_py = launcher_dir / "app.py"
            if app_py.exists():
                subprocess.run([sys.executable, str(app_py)], cwd=launcher_dir)


if __name__ == "__main__":
    main()
