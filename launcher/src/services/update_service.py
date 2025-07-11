"""Update service for managing file synchronization."""

from pathlib import Path
from typing import Optional, Callable
from ..models.config import LauncherConfig
from ..models.update_info import UpdateInfo
from ..services.github_service import GitHubService
from ..services.instance_setup_service import InstanceSetupService
from ..services.file_sync_service import FileSyncService
from ..services.mods_management_service import ModsManagementService
from ..utils.logging_utils import get_logger


class UpdateError(Exception):
    """Exception raised for update-related errors."""
    pass


class UpdateService:
    """Service for managing updates and file synchronization."""
    
    def __init__(self, config: LauncherConfig):
        """Initialize the update service.
        
        Args:
            config: Launcher configuration
        """
        self.config = config
        self.github_service = GitHubService(config.github_repo)
        self.instance_setup = InstanceSetupService(config)
        self.file_sync = FileSyncService(config)
        self.mods_management = ModsManagementService()
        self.logger = get_logger()
        self.progress_callback: Optional[Callable[[str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[str], None]) -> None:
        """Set a callback function for progress updates.
        
        Args:
            callback: Function to call with progress messages
        """
        self.progress_callback = callback
        self.file_sync.set_progress_callback(callback)
    
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
        
        # Just check for updates - don't set up instance yet
        update_info = self.github_service.create_update_info(
            self.config.current_version
        )
        
        # Check if instance exists and is properly set up
        instance_exists = self.check_instance_exists()
        
        # If version is the same, also check if files are different or instance doesn't exist
        if not update_info.updates_available:
            if not instance_exists:
                # Instance doesn't exist - force update to install everything
                self._update_progress("Instance not installed - update needed")
                update_info.updates_available = True
                return update_info
            
            self._update_progress("Checking if files have changed...")
            files_need_update = self.file_sync.check_files_need_update(update_info)
            if files_need_update:
                # Override the update availability if files are different
                update_info.updates_available = True
                self._update_progress("Files have changed - update available")
                return update_info
        
        if update_info.updates_available:
            self._update_progress(f"New version available: {update_info.latest_version}")
        else:
            self._update_progress("Up to date")
        
        return update_info
    
    def check_instance_exists(self) -> bool:
        """Check if the instance exists and is properly set up.
        
        Returns:
            True if instance exists and has NeoForge, False otherwise.
        """
        instance_exists = self.instance_setup.check_instance_exists()
        
        if instance_exists:
            # Also perform a quick mods folder integrity check during startup
            instance_path = self.config.get_selected_instance_path()
            if instance_path:
                self.mods_management.check_mods_folder_at_startup(instance_path)
        
        return instance_exists
    
    def perform_update(self, update_info: UpdateInfo, force: bool = False) -> bool:
        """Perform the update process.
        
        Args:
            update_info: Information about the update
            force: Whether to force update even if no updates are available
            
        Returns:
            True if update was successful, False otherwise.
        """
        # Check if instance exists
        instance_exists = self.check_instance_exists()
        
        # If no updates available and instance exists, nothing to do
        if not force and not update_info.updates_available and instance_exists:
            self.logger.warning("No updates available")
            return False
        
        try:
            # First, ensure the instance is properly set up (installs NeoForge if needed)
            self._update_progress("Checking instance setup...")
            self.instance_setup.ensure_instance_setup()
            
            # If there are file updates available OR we just created a new instance, download and sync files
            if update_info.updates_available or force or not instance_exists:
                # Download and extract the release
                return self.file_sync.download_and_extract_release(update_info)
            else:
                # Instance was set up but no file updates needed
                self.logger.info("Instance setup completed successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            return False
    
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
    
    def check_for_neoforge_version_change(self) -> bool:
        """Check if the NeoForge version has changed.
        
        Returns:
            True if version has changed and clean installation is needed
        """
        return self.instance_setup.check_for_neoforge_version_change()
