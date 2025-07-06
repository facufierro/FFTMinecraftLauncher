"""Self-update service for the FFT Launcher executable."""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Callable, Dict, Any, Union
import requests
from ..models.config import LauncherConfig
from ..constants import LAUNCHER_VERSION
from ..utils.logger import get_logger


class SelfUpdateService:
    """Service for updating the launcher executable itself."""
    
    def __init__(self, config: LauncherConfig):
        """Initialize the self-update service.
        
        Args:
            config: Launcher configuration
        """
        self.config = config
        self.logger = get_logger()
        self.progress_callback: Optional[Callable[[str, Optional[float], str], None]] = None
        
        # GitHub repository for launcher releases
        self.launcher_repo = "facufierro/FFTMinecraftLauncher"  # Update this to your launcher repo
        self.base_url = "https://api.github.com"
        self.timeout = 30
        
        # Current executable info
        self.current_executable = Path(sys.executable)
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            self.current_executable = Path(sys.argv[0])
        
    def set_progress_callback(self, callback: Callable[[str, Optional[float], str], None]) -> None:
        """Set a callback function for progress updates.
        
        Args:
            callback: Function to call with (message, progress, status_type)
        """
        self.progress_callback = callback
    
    def _update_progress(self, message: str, progress: Optional[float] = None, status_type: str = "info") -> None:
        """Update progress with a message.
        
        Args:
            message: Progress message
            progress: Progress value (0.0 to 1.0), None for indeterminate
            status_type: Type of status ('info', 'success', 'warning', 'error', 'loading')
        """
        self.logger.info(message)
        if self.progress_callback:
            self.progress_callback(message, progress, status_type)
    
    def check_for_launcher_update(self) -> Optional[Dict[str, Any]]:
        """Check if a new version of the launcher is available.
        
        Returns:
            Dictionary with update info if available, None otherwise.
        """
        try:
            self._update_progress("Checking for launcher updates...", None, "loading")
            
            # Get latest release from GitHub
            latest_release = self._get_latest_launcher_release()
            if not latest_release:
                self._update_progress("Could not check for launcher updates", None, "warning")
                return None
            
            latest_version = latest_release.get('tag_name', '').lstrip('v')
            current_version = LAUNCHER_VERSION.lstrip('v')
            
            self.logger.info(f"Current launcher version: {current_version}")
            self.logger.info(f"Latest launcher version: {latest_version}")
            
            if self._is_newer_version(latest_version, current_version):
                self._update_progress(f"Launcher update available: v{latest_version}", None, "info")
                return {
                    'version': latest_version,
                    'download_url': self._get_executable_download_url(latest_release),
                    'release_notes': latest_release.get('body', ''),
                    'release_data': latest_release
                }
            else:
                self._update_progress("Launcher is up to date", None, "success")
                return None
                
        except Exception as e:
            self.logger.error(f"Error checking for launcher updates: {e}")
            self._update_progress("Error checking for launcher updates", None, "error")
            return None
    
    def _get_latest_launcher_release(self) -> Optional[Dict[str, Any]]:
        """Get the latest launcher release from GitHub.
        
        Returns:
            Release data dictionary or None if failed.
        """
        try:
            url = f"{self.base_url}/repos/{self.launcher_repo}/releases/latest"
            self.logger.info(f"Fetching launcher release from: {url}")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch launcher release: {e}")
            return None
    
    def _get_executable_download_url(self, release_data: Dict[str, Any]) -> Optional[str]:
        """Get the download URL for the executable from release assets.
        
        Args:
            release_data: GitHub release data
            
        Returns:
            Download URL for the executable or None if not found.
        """
        assets = release_data.get('assets', [])
        
        # Look for Windows executable
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.exe') and 'fft' in name and 'launcher' in name:
                return asset.get('browser_download_url')
        
        # Fallback: look for any .exe file
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.exe'):
                return asset.get('browser_download_url')
        
        return None
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings to determine if latest is newer.
        
        Args:
            latest: Latest version string
            current: Current version string
            
        Returns:
            True if latest is newer than current.
        """
        try:
            # Simple version comparison for semantic versioning (e.g., 1.2.3)
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad with zeros to make same length
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
            
        except (ValueError, AttributeError):
            # Fallback to string comparison if version parsing fails
            return latest != current
    
    def download_and_install_update(self, update_info: Dict[str, Any]) -> bool:
        """Download and install the launcher update.
        
        Args:
            update_info: Update information dictionary
            
        Returns:
            True if successful, False otherwise.
        """
        download_url = update_info.get('download_url')
        if not download_url:
            self._update_progress("No download URL available", None, "error")
            return False
        
        try:
            # Create temporary directory for download
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                new_executable = temp_path / "FFTLauncher_new.exe"
                
                # Download the new executable
                if not self._download_file(download_url, new_executable):
                    return False
                
                # Verify the download
                if not new_executable.exists() or new_executable.stat().st_size == 0:
                    self._update_progress("Downloaded file is invalid", None, "error")
                    return False
                
                # Prepare update script
                return self._prepare_and_execute_update(new_executable, update_info['version'])
                
        except Exception as e:
            self.logger.error(f"Error during launcher update: {e}")
            self._update_progress("Error during launcher update", None, "error")
            return False
    
    def _download_file(self, url: str, destination: Path) -> bool:
        """Download a file from URL to destination.
        
        Args:
            url: Download URL
            destination: Destination file path
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self._update_progress("Downloading launcher update...", 0.0, "loading")
            
            response = requests.get(url, stream=True, timeout=self.timeout)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = downloaded / total_size
                            self._update_progress(
                                f"Downloading... {downloaded // 1024}KB / {total_size // 1024}KB",
                                progress,
                                "loading"
                            )
            
            self._update_progress("Download completed", 1.0, "success")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Download failed: {e}")
            self._update_progress("Download failed", None, "error")
            return False
    
    def _prepare_and_execute_update(self, new_executable: Path, new_version: str) -> bool:
        """Prepare and execute the update process.
        
        Args:
            new_executable: Path to the new executable
            new_version: New version string
            
        Returns:
            True if update process started successfully.
        """
        try:
            # Create update script
            update_script = self._create_update_script(new_executable, new_version)
            if not update_script:
                return False
            
            self._update_progress("Starting update process...", None, "loading")
            
            # Execute update script
            if os.name == 'nt':  # Windows
                subprocess.Popen([
                    'cmd', '/c', 'start', '/min', 'cmd', '/c', str(update_script)
                ], shell=True)
            else:  # Unix-like
                subprocess.Popen(['bash', str(update_script)])
            
            self._update_progress("Update will complete after restart", None, "success")
            
            # Give the script a moment to start
            import time
            time.sleep(1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to execute update: {e}")
            self._update_progress("Failed to execute update", None, "error")
            return False
    
    def _create_update_script(self, new_executable: Path, new_version: str) -> Optional[Path]:
        """Create a script to handle the update process.
        
        Args:
            new_executable: Path to the new executable
            new_version: New version string
            
        Returns:
            Path to the update script or None if failed.
        """
        try:
            script_dir = Path.cwd()
            backup_name = f"FFTLauncher_backup_{LAUNCHER_VERSION}.exe"
            
            if os.name == 'nt':  # Windows
                script_path = script_dir / "update_launcher.bat"
                script_content = f'''@echo off
echo Updating FFT Launcher to version {new_version}...

REM Wait for the current process to exit
timeout /t 3 /nobreak >nul

REM Create backup of current executable
if exist "{self.current_executable}" (
    echo Creating backup...
    copy "{self.current_executable}" "{script_dir / backup_name}" >nul
)

REM Copy new executable
echo Installing new version...
copy "{new_executable}" "{self.current_executable}" >nul

REM Update version in config if needed
echo Updating configuration...

REM Start the new launcher
echo Starting updated launcher...
start "" "{self.current_executable}"

REM Clean up
timeout /t 2 /nobreak >nul
del "%~f0"
'''
            else:  # Unix-like
                script_path = script_dir / "update_launcher.sh"
                script_content = f'''#!/bin/bash
echo "Updating FFT Launcher to version {new_version}..."

# Wait for the current process to exit
sleep 3

# Create backup of current executable
if [ -f "{self.current_executable}" ]; then
    echo "Creating backup..."
    cp "{self.current_executable}" "{script_dir / backup_name}"
fi

# Copy new executable
echo "Installing new version..."
cp "{new_executable}" "{self.current_executable}"
chmod +x "{self.current_executable}"

# Start the new launcher
echo "Starting updated launcher..."
"{self.current_executable}" &

# Clean up
sleep 2
rm "$0"
'''
            
            # Write script file
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Make executable on Unix-like systems
            if os.name != 'nt':
                os.chmod(script_path, 0o755)
            
            return script_path
            
        except Exception as e:
            self.logger.error(f"Failed to create update script: {e}")
            return None
    
    def get_launcher_version_info(self) -> Dict[str, Union[str, bool]]:
        """Get current launcher version information.
        
        Returns:
            Dictionary with version information.
        """
        return {
            'current_version': LAUNCHER_VERSION,
            'executable_path': str(self.current_executable),
            'is_frozen': str(getattr(sys, 'frozen', False)),
            'launcher_repo': self.launcher_repo
        }
    
    def force_check_update(self) -> Optional[Dict[str, Any]]:
        """Force check for updates, bypassing any caching.
        
        Returns:
            Update info if available, None otherwise.
        """
        return self.check_for_launcher_update()


class SelfUpdateError(Exception):
    """Exception raised for self-update related errors."""
    pass
