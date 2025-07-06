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
        """Download and install the launcher update using external updater.
        
        Args:
            update_info: Update information dictionary
            
        Returns:
            True if update process started successfully, False otherwise.
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
                
                # Move the new executable to final location
                final_new_exe = Path.cwd() / "FFTLauncher_new.exe"
                shutil.move(str(new_executable), str(final_new_exe))
                
                # Launch updater and exit
                return self._launch_updater_and_exit(final_new_exe, update_info['version'])
                
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
    
    def _launch_updater_and_exit(self, new_exe_path: Path, new_version: str) -> bool:
        """Launch the updater and exit the current launcher.
        
        Args:
            new_exe_path: Path to the new executable
            new_version: New version string
            
        Returns:
            True if updater launched successfully.
        """
        try:
            # Check if updater exists
            updater_path = Path.cwd() / "FFTLauncherUpdater.exe"
            if not updater_path.exists():
                self.logger.error("Updater not found - please ensure FFTLauncherUpdater.exe is in the launcher directory")
                self._update_progress("Updater not found", None, "error")
                return False
            
            self._update_progress("Starting updater...", None, "loading")
            
            # Prepare arguments for updater
            old_exe_path = self.current_executable
            launcher_args = "None"  # Could pass command line args if needed
            
            # Launch updater with arguments
            subprocess.Popen([
                str(updater_path),
                str(old_exe_path),
                str(new_exe_path),
                launcher_args
            ], creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0)
            
            self._update_progress("Updater started - launcher will restart", 1.0, "success")
            
            # Signal that we should exit
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to launch updater: {e}")
            self._update_progress("Failed to launch updater", None, "error")
            return False


class SelfUpdateError(Exception):
    """Exception raised for self-update related errors."""
    pass
