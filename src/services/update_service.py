"""Update service for managing file synchronization."""

import tempfile
from pathlib import Path
from typing import List, Optional, Callable
from ..models.config import LauncherConfig
from ..models.update_info import UpdateInfo
from ..services.github_service import GitHubService
from ..utils.file_utils import FileUtils, FileOperationError
from ..utils.logger import get_logger


class UpdateService:
    """Service for managing updates and file synchronization."""
    
    def __init__(self, config: LauncherConfig):
        """Initialize the update service.
        
        Args:
            config: Launcher configuration
        """
        self.config = config
        self.github_service = GitHubService(config.github_repo)
        self.logger = get_logger()
        self.progress_callback: Optional[Callable[[str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[str], None]) -> None:
        """Set a callback function for progress updates.
        
        Args:
            callback: Function to call with progress messages
        """
        self.progress_callback = callback
    
    def _update_progress(self, message: str) -> None:
        """Update progress with a message.
        
        Args:
            message: Progress message
        """
        self.logger.info(message)
        if self.progress_callback:
            self.progress_callback(message)
    
    def check_for_updates(self) -> UpdateInfo:
        """Check for available updates.
        
        Returns:
            UpdateInfo object containing update information.
        """
        self._update_progress("Checking for updates...")
        
        update_info = self.github_service.create_update_info(
            self.config.current_version
        )
        
        if update_info.updates_available:
            self._update_progress(f"New version available: {update_info.latest_version}")
        else:
            self._update_progress("Up to date")
        
        return update_info
    
    def perform_update(self, update_info: UpdateInfo, force: bool = False) -> bool:
        """Perform the update process.
        
        Args:
            update_info: Information about the update
            force: Whether to force update even if no updates are available
            
        Returns:
            True if update was successful, False otherwise.
        """
        if not force and not update_info.updates_available:
            self.logger.warning("No updates available")
            return False
        
        try:
            return self._download_and_extract_release(update_info)
        except UpdateError as e:
            self.logger.error(f"Update failed: {e}")
            return False
    
    def _download_and_extract_release(self, update_info: UpdateInfo) -> bool:
        """Download and extract the release files.
        
        Args:
            update_info: Information about the update
            
        Returns:
            True if successful, False otherwise.
        """
        download_url = update_info.get_download_url()
        if not download_url:
            raise UpdateError("No download URL available")
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "update.zip"
            extract_path = temp_path / "extract"
            
            # Download the release
            self._update_progress("Downloading update...")
            if not self.github_service.download_file(download_url, str(zip_path)):
                raise UpdateError("Failed to download update")
            
            # Extract the ZIP file
            self._update_progress("Extracting files...")
            try:
                extracted_folder = FileUtils.extract_zip(zip_path, extract_path)
            except FileOperationError as e:
                raise UpdateError(f"Failed to extract update: {e}")
            
            # Sync files to Minecraft directory
            self._update_progress("Syncing files...")
            return self._sync_files(extracted_folder)
    
    def _sync_files(self, source_path: Path) -> bool:
        """Sync files from source to Minecraft directory.
        
        Args:
            source_path: Path to the extracted source files
            
        Returns:
            True if successful, False otherwise.
        """
        minecraft_path = self.config.get_minecraft_path()
        
        try:
            # Ensure Minecraft directory exists
            FileUtils.ensure_directory_exists(minecraft_path)
            
            # Sync all items in the source folder
            for item in source_path.iterdir():
                if item.is_dir():
                    self._sync_directory(item, minecraft_path / item.name)
                else:
                    self._sync_file(item, minecraft_path / item.name)
            
            # Update config with new version from update_info
            # Note: This will be set by the caller after successful update
            
            return True
            
        except FileOperationError as e:
            raise UpdateError(f"Failed to sync files: {e}")
    
    def _sync_directory(self, source: Path, destination: Path) -> None:
        """Sync a directory from source to destination.
        
        Args:
            source: Source directory path
            destination: Destination directory path
        """
        self._update_progress(f"Syncing directory: {source.name}")
        
        try:
            FileUtils.safe_copy_tree(source, destination, overwrite=True)
        except FileOperationError as e:
            self.logger.error(f"Failed to sync directory {source.name}: {e}")
            raise
    
    def _sync_file(self, source: Path, destination: Path) -> None:
        """Sync a file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
        """
        self._update_progress(f"Syncing file: {source.name}")
        
        try:
            FileUtils.safe_copy_file(source, destination)
        except FileOperationError as e:
            self.logger.error(f"Failed to sync file {source.name}: {e}")
            raise
    
    def force_update(self) -> bool:
        """Force an update regardless of current version.
        
        Returns:
            True if successful, False otherwise.
        """
        self._update_progress("Force updating...")
        
        # Get latest release info
        update_info = self.github_service.create_update_info(self.config.current_version)
        
        # Force the update
        return self.perform_update(update_info, force=True)


class UpdateError(Exception):
    """Exception raised for update-related errors."""
    pass
