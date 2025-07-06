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
import time
import logging
import datetime
import threading
from pathlib import Path
import requests


# Global logger instance
logger = None


def safe_log(level, message):
    """Safe logging function that works even if logger is not initialized."""
    if logger:
        getattr(logger, level)(message)
    else:
        print(f"{level.upper()}: {message}")


def setup_logging():
    """Set up logging system."""
    global logger
    
    # Get the directory where the bootstrap exe is located
    if getattr(sys, 'frozen', False):
        bootstrap_dir = Path(sys.executable).parent
    else:
        bootstrap_dir = Path(__file__).parent
    
    # Create logs directory
    logs_dir = bootstrap_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Set up logger
    logger = logging.getLogger('bootstrap')
    logger.setLevel(logging.DEBUG)
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler - new log file each time
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"bootstrap_{timestamp}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info("=" * 50)
    logger.info("FFT Minecraft Launcher Bootstrap Started")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Bootstrap directory: {bootstrap_dir}")
    logger.info("=" * 50)
    
    return logger


def check_single_instance():
    """Check if another instance of bootstrap is already running."""
    if getattr(sys, 'frozen', False):
        bootstrap_dir = Path(sys.executable).parent
    else:
        bootstrap_dir = Path(__file__).parent
    
    lock_file = bootstrap_dir / "bootstrap.lock"
    
    if lock_file.exists():
        try:
            # Check if the PID in the lock file is still running
            with open(lock_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            # Try to check if process is still running
            try:
                import psutil
                if psutil.pid_exists(old_pid):
                    safe_log('warning', f"Another bootstrap instance (PID: {old_pid}) is already running")
                    return False
                else:
                    safe_log('info', f"Stale lock file found (PID: {old_pid} no longer exists), removing...")
                    lock_file.unlink()
            except ImportError:
                # psutil not available, try alternative method on Windows
                if os.name == 'nt':
                    try:
                        # Use tasklist command on Windows
                        result = subprocess.run(['tasklist', '/FI', f'PID eq {old_pid}'], 
                                              capture_output=True, text=True, timeout=5)
                        if f"{old_pid}" in result.stdout:
                            safe_log('warning', f"Another bootstrap instance (PID: {old_pid}) is already running")
                            return False
                        else:
                            safe_log('info', f"Stale lock file found (PID: {old_pid} no longer exists), removing...")
                            lock_file.unlink()
                    except:
                        # If tasklist fails, assume stale lock and remove it
                        safe_log('info', "Cannot check PID, removing potentially stale lock file...")
                        lock_file.unlink()
                else:
                    # Non-Windows, remove stale lock
                    safe_log('info', "Cannot check PID on this platform, removing potentially stale lock file...")
                    lock_file.unlink()
        except (ValueError, FileNotFoundError):
            # If we can't parse PID, remove stale lock
            safe_log('info', "Invalid lock file format, removing...")
            lock_file.unlink(missing_ok=True)
    
    # Create new lock file
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        safe_log('info', f"Created lock file with PID: {os.getpid()}")
        
        # Set up cleanup on exit
        import atexit
        atexit.register(lambda: lock_file.unlink(missing_ok=True))
        
        return True
    except Exception as e:
        safe_log('error', f"Failed to create lock file: {e}")
        return True  # Continue anyway


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
                version = data.get('version', '0.0.0')
                safe_log('debug', f"Current version from file: {version}")
                return version
        except Exception as e:
            safe_log('warning', f"Failed to read version file: {e}")
    
    safe_log('debug', "No version file found, returning default version")
    return "0.0.0"


def check_for_updates():
    """Check for launcher updates on GitHub."""
    try:
        safe_log('info', "Checking for updates...")
        
        # Try using GitHub CLI first (authenticated)
        try:
            gh_path = r"C:\Program Files\GitHub CLI\gh.exe"
            safe_log('debug', f"Trying GitHub CLI at: {gh_path}")
            
            result = subprocess.run([
                gh_path, "release", "list", "--repo", "facufierro/FFTMinecraftLauncher", 
                "--limit", "1", "--json", "tagName,assets"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                releases = json.loads(result.stdout)
                if releases:
                    release = releases[0]
                    latest_version = release.get('tagName', '').lstrip('v')
                    current_version = get_current_version()
                    
                    safe_log('info', f"Current: {current_version}, Latest: {latest_version}")
                    
                    if latest_version != current_version:
                        # Find launcher_package.zip download URL
                        for asset in release.get('assets', []):
                            if asset.get('name') == 'launcher_package.zip':
                                safe_log('info', f"Update available: v{latest_version}")
                                return {
                                    'version': latest_version,
                                    'download_url': asset.get('url')
                                }
                    safe_log('info', "Launcher is up to date (GitHub CLI)")
                    return None
        except Exception as e:
            safe_log('debug', f"GitHub CLI failed: {e}")
            # Fall back to direct API call
            pass
        
        # Fallback to direct API call (unauthenticated)
        safe_log('debug', "Falling back to GitHub API...")
        url = "https://api.github.com/repos/facufierro/FFTMinecraftLauncher/releases/latest"
        response = requests.get(url, timeout=10)
        
        # Handle case where no releases exist yet (404)
        if response.status_code == 404:
            safe_log('info', "No releases found on GitHub (first time setup)")
            return None
        elif response.status_code == 403:
            safe_log('warning', "GitHub API rate limit reached")
            return None
            
        response.raise_for_status()
        
        release_data = response.json()
        latest_version = release_data.get('tag_name', '').lstrip('v')
        current_version = get_current_version()
        
        safe_log('info', f"Current: {current_version}, Latest: {latest_version}")
        
        if latest_version != current_version:
            # Find launcher_package.zip download URL
            for asset in release_data.get('assets', []):
                if asset.get('name') == 'launcher_package.zip':
                    safe_log('info', f"Update available: v{latest_version}")
                    return {
                        'version': latest_version,
                        'download_url': asset.get('browser_download_url')
                    }
        
        safe_log('info', "Launcher is up to date (GitHub API)")
        return None
    except Exception as e:
        safe_log('error', f"Update check failed: {e}")
        return None


def download_and_install_update(update_info):
    """Download and install launcher update."""
    try:
        safe_log('info', f"Downloading update v{update_info['version']}...")
        download_url = update_info['download_url']
        
        # Get the directory where the bootstrap exe is located
        if getattr(sys, 'frozen', False):
            bootstrap_dir = Path(sys.executable).parent
        else:
            bootstrap_dir = Path(__file__).parent
            
        # Try using GitHub CLI for authenticated download first
        try:
            # Create temp directory for gh CLI download
            tmp_dir = tempfile.mkdtemp()
            safe_log('debug', f"Created temp directory: {tmp_dir}")
            
            # Try to download using gh CLI (gh downloads to current directory by default)
            gh_path = r"C:\Program Files\GitHub CLI\gh.exe"
            safe_log('debug', "Attempting download with GitHub CLI...")
            
            result = subprocess.run([
                gh_path, "release", "download", f"v{update_info['version']}", 
                "--repo", "facufierro/FFTMinecraftLauncher",
                "--pattern", "launcher_package.zip"
            ], cwd=tmp_dir, capture_output=True, text=True, timeout=30)
            
            tmp_file_path = Path(tmp_dir) / "launcher_package.zip"
            if result.returncode == 0 and tmp_file_path.exists():
                safe_log('info', "Downloaded using GitHub CLI (authenticated)")
                tmp_file_path = str(tmp_file_path)
            else:
                shutil.rmtree(tmp_dir, ignore_errors=True)
                raise Exception("GitHub CLI download failed")
                
        except Exception as gh_error:
            safe_log('debug', f"GitHub CLI download failed: {gh_error}")
            safe_log('info', "Falling back to direct download...")
            
            # Clean up temp dir if it exists
            try:
                if 'tmp_dir' in locals():
                    shutil.rmtree(tmp_dir, ignore_errors=True)
            except:
                pass
            
            # Fallback to direct download
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
                safe_log('debug', f"Downloading from: {download_url}")
                response = requests.get(download_url, stream=True, timeout=30)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        tmp_file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\rDownloading... {progress:.1f}%", end='', flush=True)
                
                print()  # New line after progress
                tmp_file_path = tmp_file.name
                safe_log('info', "Download completed successfully")
        
        # Installation process
        launcher_dir = bootstrap_dir / "launcher"
        backup_dir = bootstrap_dir / "launcher_backup"
        
        safe_log('info', f"Installing to: {launcher_dir}")
        
        # Remove backup from previous runs
        if backup_dir.exists():
            safe_log('debug', "Removing old backup directory")
            shutil.rmtree(backup_dir)
        
        # Backup current launcher if exists
        if launcher_dir.exists():
            safe_log('debug', "Backing up current launcher")
            shutil.move(str(launcher_dir), str(backup_dir))
        
        # Create fresh launcher directory
        safe_log('info', "Installing update...")
        launcher_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract new launcher with proper handling of nested directories
        with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
            # Extract everything to a temporary location first
            temp_extract_dir = Path(tempfile.mkdtemp())
            safe_log('debug', f"Extracting to temp dir: {temp_extract_dir}")
            zip_ref.extractall(temp_extract_dir)
            
            # Find the actual content to move
            extracted_items = list(temp_extract_dir.iterdir())
            safe_log('debug', f"Found {len(extracted_items)} items in temp extract")
            
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                # If there's only one directory, move its contents
                source_dir = extracted_items[0]
                safe_log('debug', f"Single directory found, moving contents of: {source_dir.name}")
                for item in source_dir.iterdir():
                    dest = launcher_dir / item.name
                    safe_log('debug', f"Moving {item.name} -> {dest}")
                    if item.is_dir():
                        shutil.copytree(item, dest, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, dest)
            else:
                # Move all items directly
                safe_log('debug', "Multiple items or files found, moving directly")
                for item in extracted_items:
                    dest = launcher_dir / item.name
                    safe_log('debug', f"Moving {item.name} -> {dest}")
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
        
        safe_log('info', "Update installed successfully!")
        return True
        
    except Exception as e:
        safe_log('error', f"Update failed: {e}")
        # Restore backup if it exists
        if 'backup_dir' in locals() and backup_dir.exists() and not launcher_dir.exists():
            safe_log('info', "Restoring backup...")
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
        safe_log('error', "Could not find main launcher application!")
        safe_log('info', f"Looking in: {launcher_dir.absolute()}")
        safe_log('info', "Files found:")
        if launcher_dir.exists():
            for file in launcher_dir.iterdir():
                safe_log('info', f"  - {file.name}")
        else:
            safe_log('error', "Launcher directory does not exist!")
        return False
    
    try:
        safe_log('info', f"Starting launcher: {main_script.name}")
        
        # Find Python executable (prioritize virtual environment if available)
        python_exe = sys.executable
        venv_python = bootstrap_dir / "_env" / "Scripts" / "python.exe"
        if venv_python.exists():
            python_exe = str(venv_python.absolute())
            safe_log('debug', f"Using virtual environment Python: {python_exe}")
        else:
            safe_log('debug', f"Using system Python: {python_exe}")
        
        # Set up environment
        env = os.environ.copy()
        env['PYTHONPATH'] = str(launcher_dir.absolute())
        
        # Launch Python script and detach from it completely
        # Use DETACHED_PROCESS to avoid console inheritance
        creation_flags = 0
        if os.name == 'nt':
            creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        
        safe_log('debug', f"Launching: {python_exe} {main_script.name}")
        safe_log('debug', f"Working directory: {launcher_dir.absolute()}")
        
        process = subprocess.Popen([python_exe, str(main_script.name)], 
                                 cwd=str(launcher_dir.absolute()), 
                                 env=env,
                                 stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 creationflags=creation_flags)
        
        # Wait a moment to see if the process starts successfully
        time.sleep(2)
        
        # Check if process is still running
        poll_result = process.poll()
        if poll_result is None:
            safe_log('info', f"Launcher started successfully! (PID: {process.pid})")
            return True
        else:
            safe_log('error', f"Launcher process exited immediately with code: {poll_result}")
            return False
        
    except Exception as e:
        safe_log('error', f"Failed to start launcher: {e}")
        return False


def try_local_package(bootstrap_dir, launcher_dir):
    """Try to extract from local launcher_package.zip"""
    local_package = bootstrap_dir / "launcher_package.zip"
    if not local_package.exists():
        safe_log('debug', "No local package found")
        return False
        
    try:
        safe_log('info', "Using local launcher package...")
        launcher_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract with proper directory handling
        temp_extract_dir = Path(tempfile.mkdtemp())
        safe_log('debug', f"Extracting local package to: {temp_extract_dir}")
        
        with zipfile.ZipFile(local_package, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        
        # Find the actual content to move
        extracted_items = list(temp_extract_dir.iterdir())
        safe_log('debug', f"Found {len(extracted_items)} items in local package")
        
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            # If there's only one directory, move its contents
            source_dir = extracted_items[0]
            safe_log('debug', f"Moving contents of directory: {source_dir.name}")
            for item in source_dir.iterdir():
                dest = launcher_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
        else:
            # Move all items directly
            safe_log('debug', "Moving items directly")
            for item in extracted_items:
                dest = launcher_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)
        
        # Clean up temp extract directory
        shutil.rmtree(temp_extract_dir, ignore_errors=True)
        safe_log('info', "Local package extracted successfully!")
        return True
    except Exception as e:
        safe_log('error', f"Failed to extract local package: {e}")
        return False


def main():
    """Main bootstrap function."""
    global logger
    
    # Initialize logging first
    logger = setup_logging()
    
    logger.info("FFT Minecraft Launcher Bootstrap")
    logger.info("=" * 35)
    
    # Check for single instance
    if not check_single_instance():
        logger.warning("Another bootstrap instance is already running. Exiting.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Get the directory where the bootstrap exe is located
    if getattr(sys, 'frozen', False):
        # Running as exe
        bootstrap_dir = Path(sys.executable).parent
    else:
        # Running as script
        bootstrap_dir = Path(__file__).parent
    
    logger.debug(f"Bootstrap running from: {bootstrap_dir}")
    
    # Change to bootstrap directory to ensure consistent paths
    os.chdir(bootstrap_dir)
    
    # Check if launcher exists
    launcher_dir = bootstrap_dir / "launcher"
    logger.debug(f"Looking for launcher at: {launcher_dir}")
    
    # Single update check and installation logic
    needs_install = not launcher_dir.exists()
    
    if needs_install:
        logger.info("First time setup - downloading launcher...")
    else:
        logger.info("Checking for updates...")
    
    # Add a small delay to make the process visible
    time.sleep(1)
    
    # Check for updates (only once)
    update_info = check_for_updates()
    
    if update_info:
        logger.info(f"{'Installing' if needs_install else 'Updating to'} v{update_info['version']}")
        if not download_and_install_update(update_info):
            if needs_install:
                logger.warning("Installation failed! Trying local package...")
                if not try_local_package(bootstrap_dir, launcher_dir):
                    logger.error("No launcher found and download failed!")
                    input("Press Enter to exit...")
                    sys.exit(1)
            else:
                logger.warning("Update failed, using current version...")
    elif needs_install:
        logger.info("No updates available, trying local package...")
        if not try_local_package(bootstrap_dir, launcher_dir):
            logger.error("No launcher found and download failed!")
            input("Press Enter to exit...")
            sys.exit(1)
    else:
        logger.info("Launcher is up to date!")
    
    # Add delay before launching
    logger.info("Preparing to launch...")
    time.sleep(2)
    
    # Launch main app
    logger.info("Starting launcher...")
    if launch_main_app():
        # Give the app more time to start properly
        logger.info("Waiting for launcher to initialize...")
        time.sleep(3)
        logger.info("Bootstrap completed successfully - exiting.")
        sys.exit(0)
    else:
        logger.error("Failed to start launcher!")
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
