"""Self-update service for the FFT Launcher executable."""

import os
import sys
import shutil
import tempfile
import subprocess
import zipfile
from pathlib import Path
from typing import Optional, Callable, Dict, Any, Union
import requests
from ..models.config import LauncherConfig
from ..utils.version_utils import get_launcher_version, is_newer_version
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
            current_version = get_launcher_version().lstrip('v')
            
            self.logger.info(f"Current launcher application version: {current_version}")
            self.logger.info(f"Latest launcher application version: {latest_version}")
            
            if is_newer_version(latest_version, current_version):
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
    
    def check_for_bootstrap_update(self) -> Optional[Dict[str, Any]]:
        """Check if a new version of the bootstrap is available.
        
        Returns:
            Dictionary with update info if available, None otherwise.
        """
        try:
            self._update_progress("Checking for bootstrap updates...", None, "loading")
            
            # Get latest release from GitHub
            latest_release = self._get_latest_launcher_release()
            if not latest_release:
                self._update_progress("Could not check for bootstrap updates", None, "warning")
                return None
            
            latest_version = latest_release.get('tag_name', '').lstrip('v')
            current_bootstrap_version = self._get_current_bootstrap_version()
            
            self.logger.info(f"Current bootstrap version: {current_bootstrap_version}")
            self.logger.info(f"Latest available version: {latest_version}")
            
            if is_newer_version(latest_version, current_bootstrap_version):
                bootstrap_url = self._get_bootstrap_download_url(latest_release)
                if bootstrap_url:
                    self._update_progress(f"Bootstrap update available: v{latest_version}", None, "info")
                    return {
                        'version': latest_version,
                        'download_url': bootstrap_url,
                        'release_notes': latest_release.get('body', ''),
                        'release_data': latest_release
                    }
                else:
                    self._update_progress("No bootstrap found in latest release", None, "warning")
                    return None
            else:
                self._update_progress("Bootstrap is up to date", None, "success")
                return None
                
        except Exception as e:
            self.logger.error(f"Error checking for bootstrap updates: {e}")
            self._update_progress("Error checking for bootstrap updates", None, "error")
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
            Download URL for the zip file or executable.
        """
        assets = release_data.get('assets', [])
        
        # First, look for zip files (preferred)
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.zip') and 'fft' in name and 'launcher' in name:
                return asset.get('browser_download_url')
        
        # Fallback: look for Windows executable
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.exe') and 'fft' in name and 'launcher' in name:
                return asset.get('browser_download_url')
        
        # Last resort: look for any .exe file
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.exe'):
                return asset.get('browser_download_url')
        
        return None
    
    def _get_current_bootstrap_version(self) -> str:
        """Get the current bootstrap version.
        
        Returns:
            Current bootstrap version or "0.0.0" if not found.
        """
        try:
            # Look for bootstrap executable in parent directory or current directory
            bootstrap_paths = [
                Path.cwd().parent / "FFTMinecraftLauncher.exe",  # If launched from launcher subdirectory
                Path.cwd().parent / "bootstrap.exe", 
                Path.cwd() / "FFTMinecraftLauncher.exe",  # If launched from main directory
                Path.cwd() / "bootstrap.exe"
            ]
            
            # Also check for version file that bootstrap might maintain
            version_files = [
                Path.cwd().parent / "bootstrap_version.json",
                Path.cwd() / "bootstrap_version.json"
            ]
            
            # First try to read version from bootstrap version file
            for version_file in version_files:
                if version_file.exists():
                    try:
                        import json
                        with open(version_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            version = data.get('version', '0.0.0')
                            if version != "dynamic":
                                return version
                    except Exception as e:
                        self.logger.debug(f"Could not read bootstrap version from {version_file}: {e}")
            
            # If no version file, assume it needs updating
            self.logger.debug("No bootstrap version file found, assuming update needed")
            return "0.0.0"
            
        except Exception as e:
            self.logger.debug(f"Error getting bootstrap version: {e}")
            return "0.0.0"
    
    def _get_bootstrap_download_url(self, release_data: Dict[str, Any]) -> Optional[str]:
        """Get the download URL for the bootstrap executable from release assets.
        
        Args:
            release_data: GitHub release data
            
        Returns:
            Download URL for the bootstrap executable or None if not found.
        """
        assets = release_data.get('assets', [])
        
        # Look for bootstrap executable (prioritize specific names)
        bootstrap_names = [
            'FFTMinecraftLauncher.exe',  # Main bootstrap name
            'bootstrap.exe',             # Alternative name
            'FFTLauncher.exe'           # Another alternative
        ]
        
        for asset in assets:
            asset_name = asset.get('name', '')
            if asset_name in bootstrap_names:
                return asset.get('browser_download_url')
        
        # Fallback: look for any exe that might be the bootstrap
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.exe') and ('bootstrap' in name or 'launcher' in name):
                return asset.get('browser_download_url')
        
        return None
    
    def download_and_install_bootstrap_update(self, update_info: Dict[str, Any]) -> bool:
        """Download and install the bootstrap update.
        
        Args:
            update_info: Update information dictionary
            
        Returns:
            True if update was successful, False otherwise.
        """
        download_url = update_info.get('download_url')
        if not download_url:
            self._update_progress("No bootstrap download URL available", None, "error")
            return False
        
        try:
            # Create temporary directory for download
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                download_file = temp_path / "bootstrap_new.exe"
                
                # Download the bootstrap executable
                if not self._download_file(download_url, download_file):
                    return False
                
                # Verify the download
                if not download_file.exists() or download_file.stat().st_size == 0:
                    self._update_progress("Downloaded bootstrap file is invalid", None, "error")
                    return False
                
                # Determine where to install the bootstrap
                bootstrap_locations = [
                    Path.cwd().parent / "FFTMinecraftLauncher.exe",  # Most likely location
                    Path.cwd().parent / "bootstrap.exe",
                    Path.cwd() / "FFTMinecraftLauncher.exe",
                    Path.cwd() / "bootstrap.exe"
                ]
                
                # Find existing bootstrap or use default location
                target_bootstrap = None
                for location in bootstrap_locations:
                    if location.exists():
                        target_bootstrap = location
                        break
                
                if not target_bootstrap:
                    # Default to parent directory with main name
                    target_bootstrap = Path.cwd().parent / "FFTMinecraftLauncher.exe"
                
                self._update_progress(f"Installing bootstrap to: {target_bootstrap}", None, "info")
                
                # Create backup of current bootstrap
                backup_path = target_bootstrap.with_suffix('.exe.backup')
                if target_bootstrap.exists():
                    shutil.copy2(str(target_bootstrap), str(backup_path))
                    self.logger.info(f"Created bootstrap backup: {backup_path}")
                
                try:
                    # Install new bootstrap
                    shutil.copy2(str(download_file), str(target_bootstrap))
                    self._update_progress("Bootstrap update completed successfully", 1.0, "success")
                    
                    # Create/update bootstrap version file
                    version_file = target_bootstrap.parent / "bootstrap_version.json"
                    try:
                        import json
                        import time
                        version_data = {
                            'version': update_info['version'],
                            'updated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'updated_by': 'launcher'
                        }
                        with open(version_file, 'w', encoding='utf-8') as f:
                            json.dump(version_data, f, indent=2)
                        self.logger.info(f"Updated bootstrap version file: {version_file}")
                    except Exception as e:
                        self.logger.warning(f"Could not update bootstrap version file: {e}")
                    
                    # Remove backup if successful
                    if backup_path.exists():
                        backup_path.unlink()
                    
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Failed to install bootstrap: {e}")
                    self._update_progress("Failed to install bootstrap update", None, "error")
                    
                    # Restore backup if installation failed
                    if backup_path.exists() and not target_bootstrap.exists():
                        shutil.copy2(str(backup_path), str(target_bootstrap))
                        self.logger.info("Restored bootstrap from backup")
                    
                    return False
                
        except Exception as e:
            self.logger.error(f"Error during bootstrap update: {e}")
            self._update_progress("Error during bootstrap update", None, "error")
            return False
    
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
                
                # Determine if we're downloading a zip or exe
                is_zip = download_url.lower().endswith('.zip')
                download_file = temp_path / ("update.zip" if is_zip else "FFTLauncher_new.exe")
                
                # Download the file
                if not self._download_file(download_url, download_file):
                    return False
                
                # Handle zip extraction
                if is_zip:
                    if not self._extract_update_files(download_file, temp_path):
                        return False
                    
                    # Find the main launcher executable in extracted files
                    new_executable = self._find_launcher_executable(temp_path)
                    if not new_executable:
                        self._update_progress("Could not find launcher executable in zip", None, "error")
                        return False
                else:
                    new_executable = download_file
                
                # Verify the download
                if not new_executable.exists() or new_executable.stat().st_size == 0:
                    self._update_progress("Downloaded file is invalid", None, "error")
                    return False
                
                # Move the new executable to final location
                final_new_exe = Path.cwd() / "FFTLauncher_new.exe"
                shutil.copy2(str(new_executable), str(final_new_exe))
                
                # If we extracted from zip, also copy the updater if present
                if is_zip:
                    updater_file = self._find_updater_executable(temp_path)
                    if updater_file and updater_file.exists():
                        final_updater = Path.cwd() / "FFTLauncherUpdater_new.exe"
                        shutil.copy2(str(updater_file), str(final_updater))
                        self.logger.info("Updated updater executable found and staged")
                
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
    
    def _extract_update_files(self, zip_path: Path, extract_to: Path) -> bool:
        """Extract update files from zip.
        
        Args:
            zip_path: Path to the zip file
            extract_to: Directory to extract to
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self._update_progress("Extracting update files...", None, "loading")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            self._update_progress("Extraction completed", None, "success")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to extract zip: {e}")
            self._update_progress("Failed to extract update files", None, "error")
            return False
    
    def _find_launcher_executable(self, directory: Path) -> Optional[Path]:
        """Find the main launcher executable in a directory.
        
        Args:
            directory: Directory to search in
            
        Returns:
            Path to launcher executable or None if not found.
        """
        # Look for the main launcher executable
        for exe_file in directory.rglob("*.exe"):
            name = exe_file.name.lower()
            if 'fftminecraftlauncher' in name or (name.startswith('fft') and 'launcher' in name and 'updater' not in name):
                return exe_file
        
        return None
    
    def _find_updater_executable(self, directory: Path) -> Optional[Path]:
        """Find the updater executable in a directory.
        
        Args:
            directory: Directory to search in
            
        Returns:
            Path to updater executable or None if not found.
        """
        # Look for the updater executable
        for exe_file in directory.rglob("*.exe"):
            name = exe_file.name.lower()
            if 'updater' in name and ('fft' in name or 'launcher' in name):
                return exe_file
        
        return None
    
    def get_launcher_version_info(self) -> Dict[str, Union[str, bool]]:
        """Get current launcher version information.
        
        Returns:
            Dictionary with version information.
        """
        return {
            'current_version': get_launcher_version(),
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
