"""Service for downloading the updater at launcher startup."""

import shutil
from pathlib import Path
from typing import Optional
from ..utils.logging_utils import get_logger
from ..utils.github_utils import get_github_client


class UpdaterDownloadService:
    """Service for managing updater download at startup."""
    
    def __init__(self):
        """Initialize the updater download service."""
        self.logger = get_logger()
        self.github_client = get_github_client()
        self.updater_repo = "facufierro/FFTMinecraftLauncher"
        self.updater_filename = "Updater.exe"
    
    def download_updater_at_startup(self) -> bool:
        """Download the updater at launcher startup.
        
        This is the first thing the launcher should do.
        If an updater already exists, it will be deleted first.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting updater download process...")
            
            # Get the updater path (same directory as the launcher)
            updater_path = self._get_updater_path()
            
            # Delete existing updater if it exists
            if updater_path.exists():
                self.logger.info(f"Existing updater found at {updater_path}, deleting...")
                try:
                    updater_path.unlink()
                    self.logger.info("Existing updater deleted successfully")
                except Exception as e:
                    self.logger.warning(f"Failed to delete existing updater: {e}")
                    # Continue anyway - maybe it's in use
            
            # Download the new updater
            self.logger.info("Downloading latest updater...")
            success = self._download_updater(updater_path)
            
            if success:
                self.logger.info("Updater download completed successfully")
                return True
            else:
                self.logger.error("Updater download failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during updater download: {e}")
            return False
    
    def _get_updater_path(self) -> Path:
        """Get the path where the updater should be saved.
        
        Returns:
            Path to the updater executable
        """
        # Get the directory where the current launcher is running from
        try:
            import sys
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                launcher_dir = Path(sys.executable).parent
            else:
                # Running as script - use the launcher directory
                launcher_dir = Path(__file__).parent.parent.parent
        except Exception:
            # Fallback to current working directory
            launcher_dir = Path.cwd()
        
        return launcher_dir / self.updater_filename
    
    def _download_updater(self, output_path: Path) -> bool:
        """Download the updater from GitHub releases.
        
        Args:
            output_path: Where to save the updater
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Define what constitutes an updater asset
            def is_updater_asset(asset_name: str) -> bool:
                name_lower = asset_name.lower()
                return (
                    'updater' in name_lower and 
                    name_lower.endswith('.exe')
                )
            
            # Download the updater from the latest release
            success = self.github_client.download_file_from_release(
                self.updater_repo,
                output_path,
                asset_filter=is_updater_asset,
                progress_callback=self._progress_callback
            )
            
            if success and output_path.exists():
                file_size = output_path.stat().st_size
                self.logger.info(f"Updater downloaded successfully: {file_size} bytes")
                return True
            else:
                self.logger.error("Updater download failed or file not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Error downloading updater: {e}")
            return False
    
    def _progress_callback(self, message: str, progress: Optional[float]) -> None:
        """Handle download progress updates.
        
        Args:
            message: Progress message
            progress: Progress percentage (0.0 to 1.0) or None
        """
        if progress is not None:
            percent = int(progress * 100)
            self.logger.debug(f"Updater download: {message} ({percent}%)")
        else:
            self.logger.debug(f"Updater download: {message}")
