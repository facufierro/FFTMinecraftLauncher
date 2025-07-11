"""Service for handling file synchronization operations."""

import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Callable
from ..models.config import LauncherConfig
from ..models.update_info import UpdateInfo
from ..services.github_service import GitHubService
from ..services.file_comparison_service import FileComparisonService
from ..services.mods_management_service import ModsManagementService
from ..utils.file_ops import get_file_ops
from ..utils.logging_utils import get_logger


class FileSyncService:
    """Service responsible for file synchronization operations."""
    
    def __init__(self, config: LauncherConfig):
        """Initialize the file sync service.
        
        Args:
            config: Launcher configuration
        """
        self.config = config
        self.github_service = GitHubService(config.github_repo)
        self.file_ops = get_file_ops()
        self.file_comparison = FileComparisonService()
        self.mods_management = ModsManagementService()
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
    
    def check_files_need_update(self, update_info: UpdateInfo) -> bool:
        """Check if local files need updating by comparing with remote release.
        
        Args:
            update_info: Information about the latest release
            
        Returns:
            True if files need updating, False otherwise.
        """
        try:
            download_url = update_info.get_download_url()
            if not download_url:
                return False
            
            instance_path = self.config.get_selected_instance_path()
            if not instance_path or not instance_path.exists():
                return True  # If instance doesn't exist, we need to update
            
            # Create temporary directory to download and check files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                zip_path = temp_path / "check.zip"
                extract_path = temp_path / "extract"
                
                # Download the release
                if not self.github_service.download_file(download_url, str(zip_path)):
                    self.logger.warning("Could not download release for comparison")
                    return False
                
                # Extract the ZIP file
                with zipfile.ZipFile(zip_path, 'r') as zip_file:
                    zip_file.extractall(extract_path)
                
                # Compare all files between repo and instance
                if self.file_comparison.compare_folder_contents(extract_path, instance_path):
                    self.logger.info("Files have changed - update needed")
                    return True  # Files are different, need update
                
                self.logger.info("All files match - no update needed")
                return False  # All files match
                
        except Exception as e:
            self.logger.warning(f"Error checking file differences: {e}")
            return False  # Don't force update on error
    
    def download_and_extract_release(self, update_info: UpdateInfo) -> bool:
        """Download and extract the release files.
        
        Args:
            update_info: Information about the update
            
        Returns:
            True if successful, False otherwise.
        """
        download_url = update_info.get_download_url()
        if not download_url:
            raise Exception("No download URL available")
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / "update.zip"
            extract_path = temp_path / "extract"
            
            # Download the release
            self._update_progress("Downloading update...")
            if not self.github_service.download_file(download_url, str(zip_path)):
                raise Exception("Failed to download update")
            
            # Extract the ZIP file
            self._update_progress("Extracting files...")
            try:
                extracted_folder = self.file_ops.extract_zip(zip_path, extract_path)
                if not extracted_folder:
                    raise Exception("Failed to extract ZIP file")
            except Exception as e:
                raise Exception(f"Failed to extract update: {e}")
            
            # Sync files to Minecraft directory
            self._update_progress("Syncing files...")
            return self.sync_files(extracted_folder)
    
    def sync_files(self, source_path: Path) -> bool:
        """Sync files from source to the launcher's instance directory.
        
        Args:
            source_path: Path to the extracted source files
            
        Returns:
            True if successful, False otherwise.
        """
        # Get the launcher's instance path (will be created if it doesn't exist)
        instance_path = self.config.get_selected_instance_path()
        if not instance_path:
            raise Exception("Could not determine instance path")
        
        try:
            # Ensure instance directory exists (it should be created automatically)
            instance_path.mkdir(parents=True, exist_ok=True)
            
            # Define what should be synced
            always_replace_folders = {'configureddefaults', 'kubejs', 'local', 'modflared'}
            always_replace_files = {'servers.dat'}
            conditional_sync_folders = {'mods'}  # Only sync if there are inconsistencies
            skip_folders = {'shaderpacks'}  # Don't touch these
            special_folders = {'resourcepacks'}  # Special handling
            
            # Sync items from the repo to the instance based on rules
            for item in source_path.iterdir():
                item_name_lower = item.name.lower()
                
                if item.is_dir():
                    dest_folder = instance_path / item.name
                    
                    if item_name_lower in always_replace_folders:
                        self._update_progress(f"Force replacing folder: {item.name}")
                        self.logger.info(f"Force replacing folder {item.name} from repository")
                        self.sync_directory_force(item, dest_folder)
                    elif item_name_lower in conditional_sync_folders:
                        # For mods, only sync if there are inconsistencies
                        if self._should_sync_mods_folder(item, dest_folder):
                            self._update_progress(f"Syncing mods folder due to inconsistencies")
                            self.sync_directory(item, dest_folder)
                        else:
                            self.logger.info("Mods folder is consistent - skipping sync")
                    elif item_name_lower in special_folders:
                        # Special handling for resourcepacks
                        self._handle_resourcepacks_folder(item, dest_folder)
                    elif item_name_lower not in skip_folders:
                        # For other folders, don't sync unless explicitly needed
                        self.logger.debug(f"Skipping folder: {item.name}")
                        
                elif item.is_file():
                    if item_name_lower in always_replace_files:
                        dest_file = instance_path / item.name
                        self._update_progress(f"Force replacing file: {item.name}")
                        self.logger.info(f"Force replacing file {item.name} from repository")
                        self.sync_file_force(item, dest_file)
                    else:
                        # Skip other files unless they're critical
                        self.logger.debug(f"Skipping file: {item.name}")
            
            # After syncing files, configure resource pack priority using NeoForge service
            self._configure_resource_pack_priority(instance_path)
            
            # Verify mods folder post-sync if it was synced
            if (source_path / "mods").exists():
                self.mods_management.verify_mods_folder_post_sync(source_path, instance_path)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to sync files: {e}")
    
    def sync_directory(self, source: Path, destination: Path) -> None:
        """Sync a directory from source to destination.
        
        Args:
            source: Source directory path
            destination: Destination directory path
        """
        self._update_progress(f"Syncing directory: {source.name}")
        
        try:
            # For mods folder, remove files that exist locally but not in the repo
            if source.name.lower() == "mods" and destination.exists():
                self.mods_management.cleanup_unwanted_mods(source, destination)
            
            # Set up exclusion patterns for mods folder
            exclude_patterns = None
            if source.name.lower() == "mods":
                exclude_patterns = [".connector", ".connector/*"]
                self.logger.info("Syncing mods folder with .connector exclusion")
            
            if self.file_ops.sync_directories(source, destination, exclude_patterns):
                self.logger.info(f"Successfully synced directory: {source.name}")
            else:
                raise Exception(f"Failed to sync directory {source.name}")
                
        except Exception as e:
            self.logger.error(f"Failed to sync directory {source.name}: {e}")
            raise
    
    def sync_file(self, source: Path, destination: Path) -> None:
        """Sync a file from source to destination.
        
        Args:
            source: Source file path
            destination: Destination file path
        """
        self._update_progress(f"Syncing file: {source.name}")
        
        try:
            if not self.file_ops.safe_copy(source, destination):
                raise Exception(f"Failed to copy file {source.name}")
        except Exception as e:
            self.logger.error(f"Failed to sync file {source.name}: {e}")
            raise
    
    def sync_file_force(self, source: Path, destination: Path) -> None:
        """Force sync a file from source to destination, always overwriting.
        
        Args:
            source: Source file path
            destination: Destination file path
        """
        self._update_progress(f"Force replacing file: {source.name}")
        
        try:
            if not self.file_ops.safe_copy(source, destination):
                raise Exception(f"Failed to force copy file {source.name}")
        except Exception as e:
            self.logger.error(f"Failed to force sync file {source.name}: {e}")
            raise

    def sync_directory_force(self, source: Path, destination: Path) -> None:
        """Force sync a directory from source to destination, always replacing.
        
        Args:
            source: Source directory path
            destination: Destination directory path
        """
        self._update_progress(f"Force replacing directory: {source.name}")
        
        try:
            # Remove existing directory if it exists
            if destination.exists():
                self.file_ops.safe_delete(destination)
            
            # Copy the entire directory
            if self.file_ops.sync_directories(source, destination):
                self.logger.info(f"Successfully force synced directory: {source.name}")
            else:
                raise Exception(f"Failed to force sync directory {source.name}")
                
        except Exception as e:
            self.logger.error(f"Failed to force sync directory {source.name}: {e}")
            raise

    def _should_sync_mods_folder(self, source: Path, destination: Path) -> bool:
        """Check if mods folder should be synced due to inconsistencies.
        
        Args:
            source: Source mods folder
            destination: Destination mods folder
            
        Returns:
            True if mods folder should be synced, False otherwise
        """
        try:
            # If destination doesn't exist, we should sync
            if not destination.exists():
                self.logger.info("Mods folder doesn't exist - sync needed")
                return True
            
            # Check if there are differences using file comparison
            if self.file_comparison.compare_folder_contents(source, destination):
                self.logger.info("Mods folder has inconsistencies - sync needed")
                return True
            
            self.logger.info("Mods folder is consistent - no sync needed")
            return False
            
        except Exception as e:
            self.logger.warning(f"Error checking mods folder consistency: {e}")
            # If we can't determine, err on the side of syncing
            return True

    def _handle_resourcepacks_folder(self, source: Path, destination: Path) -> None:
        """Handle resourcepacks folder with special priority logic.
        
        Args:
            source: Source resourcepacks folder
            destination: Destination resourcepacks folder
        """
        try:
            self._update_progress("Handling resourcepacks with priority...")
            
            # Ensure destination exists
            destination.mkdir(parents=True, exist_ok=True)
            
            # Copy all resource packs from source to destination
            # but don't overwrite existing ones (users might have their own packs)
            for pack_file in source.iterdir():
                if pack_file.is_file():
                    dest_pack = destination / pack_file.name
                    
                    # For FFT resource packs, always update them
                    if pack_file.name.lower().startswith(('fft-resourcepack', 'fft_resourcepack')):
                        self.logger.info(f"Updating FFT resource pack: {pack_file.name}")
                        self.file_ops.safe_copy(pack_file, dest_pack)
                    elif not dest_pack.exists():
                        # For other packs, only copy if they don't exist
                        self.logger.info(f"Adding new resource pack: {pack_file.name}")
                        self.file_ops.safe_copy(pack_file, dest_pack)
                    else:
                        self.logger.debug(f"Keeping existing resource pack: {pack_file.name}")
                        
        except Exception as e:
            self.logger.warning(f"Error handling resourcepacks folder: {e}")
            # Don't raise - this is not critical for the sync process

    def _configure_resource_pack_priority(self, instance_path: Path) -> None:
        """Configure resource pack priority to ensure FFT pack has highest priority.
        
        Args:
            instance_path: Path to the instance directory
        """
        try:
            # Import here to avoid circular imports
            from ..services.neoforge_service import NeoForgeService
            
            resourcepacks_dir = instance_path / "resourcepacks"
            if not resourcepacks_dir.exists():
                self.logger.debug("No resourcepacks directory found - skipping resource pack configuration")
                return
            
            self.logger.info(f"Configuring resource pack priority in: {resourcepacks_dir}")
            
            # Look for FFT resource packs and configure them with highest priority
            for pack_file in resourcepacks_dir.iterdir():
                if pack_file.is_file() and pack_file.name.lower().startswith(('fft-resourcepack', 'fft_resourcepack')):
                    self._update_progress("Configuring FFT resource pack with highest priority...")
                    self.logger.info(f"Found FFT resource pack: {pack_file.name}")
                    
                    # Use NeoForge service to configure the resource pack
                    neoforge_service = NeoForgeService(self.config)
                    pack_name = pack_file.stem if pack_file.suffix == '.zip' else pack_file.name
                    
                    success = neoforge_service.configure_default_resource_pack(instance_path, pack_name)
                    if success:
                        self.logger.info(f"Successfully configured FFT resource pack with highest priority: {pack_name}")
                        self._update_progress("FFT resource pack configured with highest priority")
                    else:
                        self.logger.warning(f"Failed to configure FFT resource pack: {pack_name}")
                    break
                        
        except Exception as e:
            self.logger.warning(f"Error configuring resource pack priority: {e}")
            # Don't raise - this is not critical for the sync process
