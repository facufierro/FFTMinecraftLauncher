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
    # Get the directory where the bootstrap exe is located
    if getattr(sys, 'frozen', False):
        bootstrap_dir = Path(sys.executable).parent
    else:
        bootstrap_dir = Path(__file__).parent
    
    version_file = bootstrap_dir / "launcher" / "version.json"
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
        
        # Try using GitHub CLI first (authenticated)
        try:
            import subprocess
            gh_path = r"C:\Program Files\GitHub CLI\gh.exe"
            result = subprocess.run([
                gh_path, "release", "list", "--repo", "facufierro/FFTMinecraftLauncher", 
                "--limit", "1", "--json", "tagName,assets"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                import json
                releases = json.loads(result.stdout)
                if releases:
                    release = releases[0]
                    latest_version = release.get('tagName', '').lstrip('v')
                    current_version = get_current_version()
                    
                    print(f"Current: {current_version}, Latest: {latest_version}")
                    
                    if latest_version != current_version:
                        # Find launcher_package.zip download URL
                        for asset in release.get('assets', []):
                            if asset.get('name') == 'launcher_package.zip':
                                return {
                                    'version': latest_version,
                                    'download_url': asset.get('url')
                                }
                    return None
        except Exception as e:
            print(f"GitHub CLI failed: {e}")
            # Fall back to direct API call
            pass
        
        # Fallback to direct API call (unauthenticated)
        url = "https://api.github.com/repos/facufierro/FFTMinecraftLauncher/releases/latest"
        response = requests.get(url, timeout=10)
        
        # Handle case where no releases exist yet (404)
        if response.status_code == 404:
            print("No releases found on GitHub (first time setup)")
            return None
        elif response.status_code == 403:
            print("GitHub API rate limit reached")
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
        
        # Get the directory where the bootstrap exe is located
        if getattr(sys, 'frozen', False):
            bootstrap_dir = Path(sys.executable).parent
        else:
            bootstrap_dir = Path(__file__).parent
            
        # Try using GitHub CLI for authenticated download first
        try:
            import subprocess
            # Create temp directory for gh CLI download
            import tempfile
            tmp_dir = tempfile.mkdtemp()
            
            # Try to download using gh CLI (gh downloads to current directory by default)
            gh_path = r"C:\Program Files\GitHub CLI\gh.exe"
            result = subprocess.run([
                gh_path, "release", "download", f"v{update_info['version']}", 
                "--repo", "facufierro/FFTMinecraftLauncher",
                "--pattern", "launcher_package.zip"
            ], cwd=tmp_dir, capture_output=True, text=True, timeout=30)
            
            tmp_file_path = Path(tmp_dir) / "launcher_package.zip"
            if result.returncode == 0 and tmp_file_path.exists():
                print("Downloaded using GitHub CLI (authenticated)")
                tmp_file_path = str(tmp_file_path)
            else:
                shutil.rmtree(tmp_dir, ignore_errors=True)
                raise Exception("GitHub CLI download failed")
                
        except Exception as gh_error:
            print(f"GitHub CLI download failed: {gh_error}")
            print("Falling back to direct download...")
            
            # Clean up temp dir if it exists
            try:
                if 'tmp_dir' in locals():
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            except:
                pass
            
            # Fallback to direct download
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                response = requests.get(download_url, stream=True, timeout=30)
                response.raise_for_status()
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                
                tmp_file_path = tmp_file.name
        
        # Clean up any existing launcher directory completely
        launcher_dir = bootstrap_dir / "launcher"
        backup_dir = bootstrap_dir / "launcher_backup"
        
        print(f"DEBUG: Installing to: {launcher_dir}")
        
        # Remove backup from previous runs
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        # Backup current launcher if exists
        if launcher_dir.exists():
            shutil.move(str(launcher_dir), str(backup_dir))
        
        # Create fresh launcher directory
        print("Installing update...")
        launcher_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract new launcher with proper handling of nested directories
        with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
            # Extract everything to a temporary location first
            temp_extract_dir = Path(tempfile.mkdtemp())
            print(f"DEBUG: Extracting to temp dir: {temp_extract_dir}")
            zip_ref.extractall(temp_extract_dir)
            
            # Find the actual content to move
            extracted_items = list(temp_extract_dir.iterdir())
            print(f"DEBUG: Found {len(extracted_items)} items in temp extract:")
            for item in extracted_items:
                print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")
            
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                # If there's only one directory, move its contents
                source_dir = extracted_items[0]
                print(f"DEBUG: Single directory found, moving contents of: {source_dir.name}")
                for item in source_dir.iterdir():
                    dest = launcher_dir / item.name
                    print(f"DEBUG: Moving {item.name} -> {dest}")
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest)
            else:
                # Move all items directly
                print("DEBUG: Multiple items or files found, moving directly")
                for item in extracted_items:
                    dest = launcher_dir / item.name
                    print(f"DEBUG: Moving {item.name} -> {dest}")
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest)
            
            # Clean up temp extract directory
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
        
        # Clean up
        os.unlink(tmp_file_path)
        
        # Clean up temp dir from gh CLI if it exists
        try:
            if 'tmp_dir' in locals():
                shutil.rmtree(tmp_dir, ignore_errors=True)
        except:
            pass
        
        # Only remove backup if installation was successful
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        print("Update installed successfully!")
        return True
        
    except Exception as e:
        print(f"Update failed: {e}")
        # Restore backup if it exists
        if 'backup_dir' in locals() and backup_dir.exists() and not launcher_dir.exists():
            shutil.move(str(backup_dir), str(launcher_dir))
        return False


def launch_main_app():
    """Launch the main launcher application."""
    # Get the directory where the bootstrap exe is located
    if getattr(sys, 'frozen', False):
        bootstrap_dir = Path(sys.executable).parent
    else:
        bootstrap_dir = Path(__file__).parent
        
    launcher_dir = bootstrap_dir / "launcher"
    
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
        venv_python = bootstrap_dir / "_env" / "Scripts" / "python.exe"
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
    
    # Get the directory where the bootstrap exe is located
    if getattr(sys, 'frozen', False):
        # Running as exe
        bootstrap_dir = Path(sys.executable).parent
    else:
        # Running as script
        bootstrap_dir = Path(__file__).parent
    
    print(f"DEBUG: Bootstrap running from: {bootstrap_dir}")
    
    # Change to bootstrap directory to ensure consistent paths
    os.chdir(bootstrap_dir)
    
    # Check if launcher exists
    launcher_dir = bootstrap_dir / "launcher"
    print(f"DEBUG: Looking for launcher at: {launcher_dir}")
    
    # If no launcher exists, try to get updates
    if not launcher_dir.exists():
        print("First time setup - downloading launcher...")
        
        # Check for updates
        update_info = check_for_updates()
        if update_info:
            print(f"Update available: v{update_info['version']}")
            if download_and_install_update(update_info):
                print("Update completed!")
            else:
                print("Update failed!")
                # Try to use local launcher_package.zip as fallback
                local_package = bootstrap_dir / "launcher_package.zip"
                if local_package.exists():
                    print("Using local launcher package as fallback...")
                    try:
                        launcher_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Extract with proper directory handling
                        temp_extract_dir = Path(tempfile.mkdtemp())
                        with zipfile.ZipFile(local_package, 'r') as zip_ref:
                            zip_ref.extractall(temp_extract_dir)
                        
                        # Find the actual content to move
                        extracted_items = list(temp_extract_dir.iterdir())
                        
                        if len(extracted_items) == 1 and extracted_items[0].is_dir():
                            # If there's only one directory, move its contents
                            source_dir = extracted_items[0]
                            for item in source_dir.iterdir():
                                dest = launcher_dir / item.name
                                if item.is_dir():
                                    shutil.copytree(item, dest, dirs_exist_ok=True)
                                else:
                                    shutil.copy2(item, dest)
                        else:
                            # Move all items directly
                            for item in extracted_items:
                                dest = launcher_dir / item.name
                                if item.is_dir():
                                    shutil.copytree(item, dest, dirs_exist_ok=True)
                                else:
                                    shutil.copy2(item, dest)
                        
                        # Clean up temp extract directory
                        shutil.rmtree(temp_extract_dir, ignore_errors=True)
                        print("Local package extracted successfully!")
                    except Exception as e:
                        print(f"Failed to extract local package: {e}")
        else:
            print("No updates available or update check failed.")
            # Try to use local launcher_package.zip as fallback
            local_package = bootstrap_dir / "launcher_package.zip"
            if local_package.exists():
                print("Using local launcher package as fallback...")
                try:
                    launcher_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Extract with proper directory handling
                    temp_extract_dir = Path(tempfile.mkdtemp())
                    with zipfile.ZipFile(local_package, 'r') as zip_ref:
                        zip_ref.extractall(temp_extract_dir)
                    
                    # Find the actual content to move
                    extracted_items = list(temp_extract_dir.iterdir())
                    
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        # If there's only one directory, move its contents
                        source_dir = extracted_items[0]
                        for item in source_dir.iterdir():
                            dest = launcher_dir / item.name
                            if item.is_dir():
                                shutil.copytree(item, dest, dirs_exist_ok=True)
                            else:
                                shutil.copy2(item, dest)
                    else:
                        # Move all items directly
                        for item in extracted_items:
                            dest = launcher_dir / item.name
                            if item.is_dir():
                                shutil.copytree(item, dest, dirs_exist_ok=True)
                            else:
                                shutil.copy2(item, dest)
                    
                    # Clean up temp extract directory
                    shutil.rmtree(temp_extract_dir, ignore_errors=True)
                    print("Local package extracted successfully!")
                except Exception as e:
                    print(f"Failed to extract local package: {e}")
    else:
        # Launcher exists, check for updates
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
