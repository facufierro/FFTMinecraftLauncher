#!/usr/bin/env python3
"""
Simple Bootstrap for FFT Minecraft Launcher
Downloads and launches the main launcher application.
"""

import os
import sys
import json
import shutil
import zipfile
import subprocess
import tempfile
from pathlib import Path
import requests


def get_current_version():
    """Get current launcher version."""
    version_file = Path("launcher/version.json")
    if version_file.exists():
        try:
            with open(version_file, 'r') as f:
                data = json.load(f)
                return data.get('version', '0.0.0')
        except:
            pass
    return "0.0.0"


def check_for_updates():
    """Check for launcher updates on GitHub."""
    try:
        print("Checking for updates...")
        url = "https://api.github.com/repos/facufierro/FFTMinecraftLauncher/releases/latest"
        response = requests.get(url, timeout=10)
        
        # Handle case where no releases exist yet (404)
        if response.status_code == 404:
            print("No releases found on GitHub (first time setup)")
            return None
            
        response.raise_for_status()
        
        release_data = response.json()
        latest_version = release_data.get('tag_name', '').lstrip('v')
        current_version = get_current_version()
        
        print(f"Current: {current_version}, Latest: {latest_version}")
        
        if latest_version != current_version:
            # Find launcher_package.zip download URL
            for asset in release_data.get('assets', []):
                if asset.get('name') == 'launcher_package.zip':
                    return {
                        'version': latest_version,
                        'download_url': asset.get('browser_download_url')
                    }
        return None
    except Exception as e:
        print(f"Update check failed: {e}")
        return None


def download_and_install_update(update_info):
    """Download and install launcher update."""
    try:
        print("Downloading update...")
        download_url = update_info['download_url']
        
        # Download to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp_file.write(chunk)
            
            tmp_file_path = tmp_file.name
        
        # Clean up any existing launcher directory completely
        launcher_dir = Path("launcher")
        backup_dir = Path("launcher_backup")
        
        # Remove backup from previous runs
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        # Backup current launcher if exists
        if launcher_dir.exists():
            shutil.move(str(launcher_dir), str(backup_dir))
        
        # Create fresh launcher directory
        print("Installing update...")
        launcher_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract new launcher
        with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
            zip_ref.extractall(launcher_dir)
        
        # Clean up
        os.unlink(tmp_file_path)
        
        # Only remove backup if installation was successful
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        print("Update installed successfully!")
        return True
        
    except Exception as e:
        print(f"Update failed: {e}")
        # Restore backup if it exists
        if backup_dir.exists() and not launcher_dir.exists():
            shutil.move(str(backup_dir), str(launcher_dir))
        return False


def launch_main_app():
    """Launch the main launcher application."""
    launcher_dir = Path("launcher")
    
    # Look for main script
    main_script = None
    for script_name in ["app.py", "main.py"]:
        script_path = launcher_dir / script_name
        if script_path.exists():
            main_script = script_path
            break
    
    if not main_script:
        print("Error: Could not find main launcher application!")
        print(f"Looking in: {launcher_dir.absolute()}")
        print("Files found:")
        if launcher_dir.exists():
            for file in launcher_dir.iterdir():
                print(f"  - {file.name}")
        input("Press Enter to exit...")
        return False
    
    try:
        print(f"Starting launcher: {main_script.name}")
        
        # Find Python executable (prioritize virtual environment if available)
        python_exe = sys.executable
        venv_python = Path("_env/Scripts/python.exe")
        if venv_python.exists():
            python_exe = str(venv_python.absolute())
        
        # Set up environment
        import os
        env = os.environ.copy()
        env['PYTHONPATH'] = str(launcher_dir.absolute())
        
        # Launch Python script and detach from it (don't wait)
        # Use the launcher directory as working directory
        subprocess.Popen([python_exe, str(main_script.name)], 
                        cwd=str(launcher_dir.absolute()), 
                        env=env,
                        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
        
        print("Launcher started successfully!")
        return True
        
    except Exception as e:
        print(f"Failed to start launcher: {e}")
        input("Press Enter to exit...")
        return False


def main():
    """Main bootstrap function."""
    print("FFT Minecraft Launcher Bootstrap")
    print("=" * 35)
    
    # Check if launcher exists
    launcher_dir = Path("launcher")
    if not launcher_dir.exists():
        print("First time setup - downloading launcher...")
    
    # Check for updates
    update_info = check_for_updates()
    if update_info:
        print(f"Update available: v{update_info['version']}")
        if download_and_install_update(update_info):
            print("Update completed!")
        else:
            print("Update failed, using current version...")
    else:
        print("Launcher is up to date!")
    
    # Launch main app
    if not launcher_dir.exists():
        print("Error: No launcher found and download failed!")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Launch the main app and exit
    if launch_main_app():
        # Give the app a moment to start, then exit
        import time
        time.sleep(2)
        print("Bootstrap completed - exiting.")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
