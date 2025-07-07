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
        
        # Just check for updates - don't set up instance yet
        update_info = self.github_service.create_update_info(
            self.config.current_version
        )
        
        # If version is the same, also check if files are different
        if not update_info.updates_available:
            self._update_progress("Checking if files have changed...")
            files_need_update = self._check_files_need_update(update_info)
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
    
    def _check_files_need_update(self, update_info: UpdateInfo) -> bool:
        """Check if local files need updating by comparing with remote release.
        
        Args:
            update_info: Information about the latest release
            
        Returns:
            True if files need updating, False otherwise.
        """
        try:
            import tempfile
            import zipfile
            import hashlib
            from pathlib import Path
            
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
                
                # Compare files in folders_to_sync
                for folder in self.config.folders_to_sync:
                    remote_folder = extract_path / folder
                    local_folder = instance_path / folder
                    
                    if not remote_folder.exists():
                        continue  # Skip if folder doesn't exist in release
                    
                    if not local_folder.exists():
                        self.logger.info(f"Local folder {folder} missing - update needed")
                        return True  # Local folder missing, need update
                    
                    # Compare all files in this folder
                    if self._compare_folder_contents(remote_folder, local_folder):
                        self.logger.info(f"Files in {folder} have changed - update needed")
                        return True  # Files are different, need update
                
                self.logger.info("All files match - no update needed")
                return False  # All files match
                
        except Exception as e:
            self.logger.warning(f"Error checking file differences: {e}")
            return False  # Don't force update on error
    
    def _compare_folder_contents(self, remote_folder: Path, local_folder: Path) -> bool:
        """Compare contents of two folders recursively.
        
        Args:
            remote_folder: Path to remote folder
            local_folder: Path to local folder
            
        Returns:
            True if folders are different, False if they match.
        """
        import hashlib
        
        # Get all files in both folders
        remote_files = set()
        local_files = set()
        
        if remote_folder.exists():
            for file_path in remote_folder.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(remote_folder)
                    remote_files.add(rel_path)
        
        if local_folder.exists():
            for file_path in local_folder.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(local_folder)
                    local_files.add(rel_path)
        
        # Check if file lists are different
        if remote_files != local_files:
            return True
        
        # Compare file contents for matching files
        for rel_path in remote_files:
            remote_file = remote_folder / rel_path
            local_file = local_folder / rel_path
            
            if not local_file.exists():
                return True
            
            # Compare file hashes
            try:
                remote_hash = self._get_file_hash(remote_file)
                local_hash = self._get_file_hash(local_file)
                
                if remote_hash != local_hash:
                    return True
            except Exception:
                return True  # Error reading file, assume different
        
        return False  # All files match
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash as hex string.
        """
        import hashlib
        
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def check_instance_exists(self) -> bool:
        """Check if the instance exists and is properly set up.
        
        Returns:
            True if instance exists and has NeoForge, False otherwise.
        """
        instance_path = self.config.get_selected_instance_path()
        if not instance_path or not instance_path.exists():
            return False
        
        # Check for essential folders
        essential_folders = ['mods', 'config', 'versions']
        has_essential = all((instance_path / folder).exists() for folder in essential_folders)
        
        # Check if NeoForge is installed
        has_neoforge = self._is_neoforge_installed(instance_path)
        
        return has_essential and has_neoforge

    def _ensure_instance_setup(self) -> None:
        """Ensure the instance is properly set up with NeoForge and launcher profile."""
        self._update_progress("Checking instance setup...")
        
        instance_path = self.config.get_selected_instance_path()
        if not instance_path:
            raise UpdateError("Instance path could not be determined")
        
        # Create the instance directory if it doesn't exist
        if not instance_path.exists():
            self._update_progress("Creating instance directory...")
            instance_path.mkdir(parents=True, exist_ok=True)
            
            # Create necessary subdirectories
            subdirs = ['mods', 'config', 'resourcepacks', 'kubejs', 'defaultconfigs', 'versions']
            for subdir in subdirs:
                (instance_path / subdir).mkdir(exist_ok=True)
        
        # Create launcher profile BEFORE installing NeoForge
        self._ensure_launcher_profile(instance_path)
        
        # Check if NeoForge is installed
        if not self._is_neoforge_installed(instance_path):
            self._update_progress("Installing NeoForge...")
            self._install_neoforge(instance_path)
    
    def _is_neoforge_installed(self, instance_path: Path) -> bool:
        """Check if NeoForge is installed in the instance."""
        versions_dir = instance_path / "versions"
        if not versions_dir.exists():
            return False
        
        # Look for NeoForge version directories
        for version_dir in versions_dir.iterdir():
            if version_dir.is_dir() and "neoforge" in version_dir.name.lower():
                version_json = version_dir / f"{version_dir.name}.json"
                if version_json.exists():
                    return True
        
        return False
    
    def _install_neoforge(self, instance_path: Path) -> None:
        """Install NeoForge to the instance."""
        try:
            # Import here to avoid circular imports
            from ..services.neoforge_service import NeoForgeService
            
            neoforge_service = NeoForgeService(self.config)
            success = neoforge_service.install_neoforge_to_instance_path(instance_path)
            
            if not success:
                raise UpdateError("Failed to install NeoForge")
                
        except Exception as e:
            raise UpdateError(f"NeoForge installation failed: {e}")
    
    def _ensure_launcher_profile(self, instance_path: Path) -> None:
        """Ensure a Minecraft launcher profile exists for this instance."""
        try:
            import json
            import os
            import uuid
            from pathlib import Path
            
            # Create a minimal launcher_profiles.json in the instance directory itself
            instance_profiles_path = instance_path / "launcher_profiles.json"
            
            if not instance_profiles_path.exists():
                # Create minimal launcher profile structure for NeoForge installer
                minimal_profile = {
                    "profiles": {
                        "default": {
                            "name": "FFT Launcher Instance",
                            "type": "latest-release",
                            "created": "2024-01-01T00:00:00.000Z",
                            "lastUsed": "2024-01-01T00:00:00.000Z"
                        }
                    },
                    "settings": {
                        "enableHistorical": False,
                        "enableSnapshots": False,
                        "enableAdvanced": False
                    }
                }
                
                with open(instance_profiles_path, 'w', encoding='utf-8') as f:
                    json.dump(minimal_profile, f, indent=2)
            
            # Also ensure the main .minecraft launcher knows about this instance
            minecraft_dir = Path(os.environ['APPDATA']) / ".minecraft"
            launcher_profiles_path = minecraft_dir / "launcher_profiles.json"
            
            # Load existing profiles or create new structure
            if launcher_profiles_path.exists():
                with open(launcher_profiles_path, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
            else:
                profiles_data = {
                    "profiles": {},
                    "settings": {
                        "enableHistorical": False,
                        "enableSnapshots": False,
                        "enableAdvanced": False
                    }
                }
            
            # Check if profile already exists for this instance
            profile_name = "FFTClient"
            profile_exists = False
            
            for profile_id, profile_data in profiles_data.get("profiles", {}).items():
                # Check by name OR by gameDir (to update existing instances)
                if (profile_data.get("name") == profile_name or 
                    profile_data.get("gameDir") == str(instance_path)):
                    # Update the profile with correct name, gameDir and version
                    profile_data["name"] = profile_name
                    profile_data["gameDir"] = str(instance_path)
                    profile_data["lastVersionId"] = "neoforge-21.1.186"
                    profile_data["type"] = "custom"
                    profile_data["icon"] = "Furnace"
                    profile_exists = True
                    break
            
            if not profile_exists:
                # Create new profile
                profile_id = str(uuid.uuid4()).replace('-', '')
                
                new_profile = {
                    "name": profile_name,
                    "type": "custom",
                    "created": "2024-01-01T00:00:00.000Z",
                    "lastUsed": "2024-01-01T00:00:00.000Z",
                    "lastVersionId": "neoforge-21.1.186",
                    "icon": "Furnace",
                    "gameDir": str(instance_path)
                }
                
                profiles_data["profiles"][profile_id] = new_profile
            
            # Save the updated profiles
            with open(launcher_profiles_path, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2)
                
        except Exception as e:
            self.logger.warning(f"Failed to create launcher profile: {e}")
            # Don't raise error - this is not critical for functionality
    
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
            # First, ensure the instance is properly set up
            self._ensure_instance_setup()
            
            # Then download and extract the release
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
        """Sync files from source to the launcher's instance directory.
        
        Args:
            source_path: Path to the extracted source files
            
        Returns:
            True if successful, False otherwise.
        """
        # Get the launcher's instance path (will be created if it doesn't exist)
        instance_path = self.config.get_selected_instance_path()
        if not instance_path:
            raise UpdateError("Could not determine instance path")
        
        try:
            # Ensure instance directory exists (it should be created automatically)
            FileUtils.ensure_directory_exists(instance_path)
            
            # Only sync the folders that are configured to be synced
            for folder_name in self.config.folders_to_sync:
                source_folder = source_path / folder_name
                if source_folder.exists():
                    dest_folder = instance_path / folder_name
                    self._sync_directory(source_folder, dest_folder)
                else:
                    self.logger.warning(f"Source folder '{folder_name}' not found in update")
            
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
