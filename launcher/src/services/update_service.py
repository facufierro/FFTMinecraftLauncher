"""Update service for managing file synchronization."""

import tempfile
from pathlib import Path
from typing import List, Optional, Callable
from ..models.config import LauncherConfig
from ..models.update_info import UpdateInfo
from ..services.github_service import GitHubService
from ..utils.file_ops import get_file_ops
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
        self.file_ops = get_file_ops()
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
                
                # Compare all files between repo and instance
                if self._compare_folder_contents(extract_path, instance_path):
                    self.logger.info("Files have changed - update needed")
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
        
        # Check if this is a mods folder to apply .connector exclusion
        is_mods_folder = remote_folder.name.lower() == "mods" or local_folder.name.lower() == "mods"
        
        if remote_folder.exists():
            for file_path in remote_folder.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(remote_folder)
                    # Skip .connector folder and its contents for mods folder
                    if is_mods_folder and (str(rel_path).startswith('.connector') or '.connector' in str(rel_path)):
                        continue
                    remote_files.add(rel_path)
        
        if local_folder.exists():
            for file_path in local_folder.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(local_folder)
                    # Skip .connector folder and its contents for mods folder
                    if is_mods_folder and (str(rel_path).startswith('.connector') or '.connector' in str(rel_path)):
                        continue
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
    
    def _verify_mods_folder_integrity(self, remote_extract_path: Path, instance_path: Path) -> bool:
        """Perform additional verification of mods folder integrity.
        
        This method provides an extra layer of verification specifically for the mods folder
        to ensure it's always synchronized with the repository version.
        
        Args:
            remote_extract_path: Path to extracted remote files
            instance_path: Path to local instance
            
        Returns:
            True if mods folder is properly synchronized, False if update needed.
        """
        try:
            remote_mods = remote_extract_path / "mods"
            local_mods = instance_path / "mods"
            
            # If remote has mods folder but local doesn't, update needed
            if remote_mods.exists() and not local_mods.exists():
                self.logger.warning("Local mods folder missing - update needed")
                return False
            
            # If remote doesn't have mods folder, local shouldn't either
            if not remote_mods.exists():
                if local_mods.exists() and any(local_mods.iterdir()):
                    self.logger.warning("Local mods folder should be empty - cleaning needed")
                    return False
                return True  # Both don't exist or local is empty
            
            # Both exist - perform detailed comparison
            remote_mod_files = set()
            local_mod_files = set()
            
            # Get all .jar files in remote mods folder
            for file_path in remote_mods.rglob('*.jar'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(remote_mods)
                    # Skip .connector folder and its contents
                    if str(rel_path).startswith('.connector') or '.connector' in str(rel_path):
                        continue
                    remote_mod_files.add((rel_path, file_path.stat().st_size))
            
            # Get all .jar files in local mods folder
            for file_path in local_mods.rglob('*.jar'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(local_mods)
                    # Skip .connector folder and its contents
                    if str(rel_path).startswith('.connector') or '.connector' in str(rel_path):
                        continue
                    local_mod_files.add((rel_path, file_path.stat().st_size))
            
            # Check if mod file sets are different
            if remote_mod_files != local_mod_files:
                self.logger.warning("Mods folder contents differ from repository:")
                
                # Log specific differences
                only_in_remote = remote_mod_files - local_mod_files
                only_in_local = local_mod_files - remote_mod_files
                
                if only_in_remote:
                    self.logger.info(f"Mods in repository but not locally: {[str(f[0]) for f in only_in_remote]}")
                if only_in_local:
                    self.logger.info(f"Mods locally but not in repository: {[str(f[0]) for f in only_in_local]}")
                
                return False
            
            # Additional hash-based verification for critical mod files
            for rel_path, size in remote_mod_files:
                remote_file = remote_mods / rel_path
                local_file = local_mods / rel_path
                
                if not local_file.exists():
                    continue  # Already caught above
                
                # For files that might be critical, do hash comparison
                if self._is_critical_mod_file(rel_path):
                    try:
                        remote_hash = self._get_file_hash(remote_file)
                        local_hash = self._get_file_hash(local_file)
                        
                        if remote_hash != local_hash:
                            self.logger.warning(f"Critical mod file hash mismatch: {rel_path}")
                            return False
                    except Exception as e:
                        self.logger.warning(f"Failed to verify hash for {rel_path}: {e}")
                        return False
            
            self.logger.info("Mods folder integrity verification passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during mods folder integrity check: {e}")
            return False  # Assume update needed on error
    
    def _is_critical_mod_file(self, file_path: Path) -> bool:
        """Determine if a mod file is critical and should have hash verification.
        
        Args:
            file_path: Relative path to the mod file
            
        Returns:
            True if the file is considered critical.
        """
        # Consider all .jar files as critical for now
        # In the future, this could be expanded to check for specific mod names
        return file_path.suffix.lower() == '.jar'
    
    def _verify_mods_folder_post_sync(self, source_path: Path, instance_path: Path) -> None:
        """Verify mods folder integrity after synchronization.
        
        This method performs a final verification that the mods folder was correctly
        synchronized and matches the repository version exactly.
        
        Args:
            source_path: Path to the source files that were synced
            instance_path: Path to the local instance
        """
        try:
            source_mods = source_path / "mods"
            local_mods = instance_path / "mods"
            
            self.logger.info("Performing post-sync verification of mods folder...")
            
            # Quick verification that folders match
            if not self._verify_mods_folder_integrity(source_path, instance_path):
                self.logger.error("Post-sync mods folder verification failed!")
                # Try to fix by re-syncing just the mods folder
                self._fix_mods_folder_sync(source_mods, local_mods)
            else:
                self.logger.info("Post-sync mods folder verification passed")
                
            # Log the final state for debugging
            self._log_mods_folder_state(local_mods)
            
        except Exception as e:
            self.logger.error(f"Error during post-sync mods folder verification: {e}")
    
    def _fix_mods_folder_sync(self, source_mods: Path, local_mods: Path) -> None:
        """Attempt to fix mods folder synchronization issues.
        
        Args:
            source_mods: Path to source mods folder
            local_mods: Path to local mods folder
        """
        try:
            self.logger.warning("Attempting to fix mods folder synchronization...")
            
            if source_mods.exists():
                # Re-sync the mods directory
                self._sync_directory(source_mods, local_mods)
                self.logger.info("Mods folder re-synchronization completed")
            else:
                # If source doesn't have mods, ensure local is empty
                if local_mods.exists():
                    import shutil
                    shutil.rmtree(local_mods)
                    local_mods.mkdir(exist_ok=True)
                    self.logger.info("Cleaned local mods folder (no mods in repository)")
                    
        except Exception as e:
            self.logger.error(f"Failed to fix mods folder synchronization: {e}")
    
    def _log_mods_folder_state(self, mods_folder: Path) -> None:
        """Log the current state of the mods folder for debugging.
        
        Args:
            mods_folder: Path to the mods folder to inspect
        """
        try:
            if not mods_folder.exists():
                self.logger.info("Mods folder: Does not exist")
                return
            
            mod_files = []
            for file_path in mods_folder.rglob('*.jar'):
                rel_path = file_path.relative_to(mods_folder)
                # Skip .connector folder and its contents
                if not (str(rel_path).startswith('.connector') or '.connector' in str(rel_path)):
                    mod_files.append(file_path)
            
            self.logger.info(f"Mods folder: Contains {len(mod_files)} mod files (excluding .connector)")
            
            if mod_files:
                for mod_file in sorted(mod_files):
                    rel_path = mod_file.relative_to(mods_folder)
                    size_mb = mod_file.stat().st_size / (1024 * 1024)
                    self.logger.info(f"  - {rel_path} ({size_mb:.1f} MB)")
            else:
                self.logger.info("  - No mod files found")
                
        except Exception as e:
            self.logger.warning(f"Failed to log mods folder state: {e}")
    
    def _check_mods_folder_at_startup(self, instance_path: Path) -> None:
        """Perform a basic mods folder check during startup.
        
        This method performs a lightweight check of the mods folder during startup
        to log its current state and detect any obvious issues.
        
        Args:
            instance_path: Path to the instance directory
        """
        try:
            mods_folder = instance_path / "mods"
            
            if not mods_folder.exists():
                self.logger.warning("Mods folder does not exist - will be created during next update")
                return
            
            # Count mod files (excluding .connector folder)
            mod_files = []
            for file_path in mods_folder.rglob('*.jar'):
                rel_path = file_path.relative_to(mods_folder)
                # Skip .connector folder and its contents
                if not (str(rel_path).startswith('.connector') or '.connector' in str(rel_path)):
                    mod_files.append(file_path)
            
            self.logger.info(f"Startup check: Found {len(mod_files)} mod files in mods folder (excluding .connector)")
            
            # Check for common issues
            if not mod_files:
                self.logger.warning("Mods folder is empty - this may indicate synchronization issues")
            
            # Check for non-jar files that might indicate corruption (excluding .connector)
            all_files = []
            for file_path in mods_folder.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(mods_folder)
                    # Skip .connector folder and its contents
                    if not (str(rel_path).startswith('.connector') or '.connector' in str(rel_path)):
                        all_files.append(file_path)
            
            non_jar_files = [f for f in all_files if not f.name.endswith('.jar')]
            
            if non_jar_files:
                self.logger.warning(f"Found {len(non_jar_files)} non-jar files in mods folder:")
                for file in non_jar_files[:5]:  # Log up to 5 examples
                    self.logger.warning(f"  - {file.name}")
                if len(non_jar_files) > 5:
                    self.logger.warning(f"  ... and {len(non_jar_files) - 5} more")
            
        except Exception as e:
            self.logger.warning(f"Error during startup mods folder check: {e}")
    
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
            self.logger.info("Instance path does not exist")
            return False
        
        # Check for essential folders (these should always exist)
        essential_folders = ['mods', 'config', 'versions']
        has_essential = all((instance_path / folder).exists() for folder in essential_folders)
        
        if not has_essential:
            self.logger.info("Instance missing essential folders")
            return False
        
        # Check if NeoForge is installed
        has_neoforge = self._is_neoforge_installed(instance_path)
        
        if not has_neoforge:
            self.logger.warning("NeoForge not installed in instance")
            return False
        
        self.logger.info("Instance exists and has NeoForge - checking resource pack configuration...")
        
        # Check if resource packs need to be configured
        self._check_and_configure_resource_packs(instance_path)
        
        # Also perform a quick mods folder integrity check during startup
        self._check_mods_folder_at_startup(instance_path)
        
        return True
    
    def _check_and_configure_resource_packs(self, instance_path: Path) -> None:
        """Check if resource packs exist but aren't configured, and configure them.
        
        Args:
            instance_path: Path to the instance directory
        """
        try:
            resourcepacks_dir = instance_path / "resourcepacks"
            if not resourcepacks_dir.exists():
                self.logger.debug("No resourcepacks directory found during startup check")
                return
            
            self.logger.info("Checking resource pack configuration at startup...")
            
            # List all files in resourcepacks directory for debugging
            pack_files = list(resourcepacks_dir.iterdir())
            if pack_files:
                self.logger.info(f"Found {len(pack_files)} files in resourcepacks directory:")
                for pack_file in pack_files:
                    self.logger.info(f"  - {pack_file.name}")
            else:
                self.logger.info("No files found in resourcepacks directory during startup check")
                return
            
            # Look for FFT resource packs
            for pack_file in pack_files:
                if pack_file.name.startswith("fft-resourcepack") or pack_file.name.startswith("fft_resourcepack"):
                    # Check if this pack is already configured in options.txt
                    options_file = instance_path / "options.txt"
                    pack_name = pack_file.stem if pack_file.suffix == '.zip' else pack_file.name
                    resource_pack_file = f"file/{pack_name}"
                    
                    pack_configured = False
                    if options_file.exists():
                        try:
                            with open(options_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if f'"{resource_pack_file}"' in content:
                                    pack_configured = True
                                    self.logger.info(f"Resource pack {pack_name} is already configured")
                        except Exception as e:
                            self.logger.warning(f"Error reading options.txt: {e}")
                    else:
                        self.logger.info("No options.txt file found - resource pack will be configured")
                    
                    if not pack_configured:
                        self.logger.info(f"Found unconfigured resource pack: {pack_name} - configuring now")
                        # Import here to avoid circular imports
                        from ..services.neoforge_service import NeoForgeService
                        neoforge_service = NeoForgeService(self.config)
                        success = neoforge_service.configure_default_resource_pack(instance_path, pack_name)
                        if success:
                            self.logger.info(f"Successfully configured resource pack {pack_name} at startup")
                        else:
                            self.logger.warning(f"Failed to configure resource pack {pack_name} at startup")
                    break
                    
        except Exception as e:
            self.logger.warning(f"Error checking resource pack configuration: {e}")

    def _ensure_instance_setup(self) -> None:
        """Ensure the instance is properly set up with NeoForge and launcher profile."""
        self._update_progress("Checking instance setup...")
        
        instance_path = self.config.get_selected_instance_path()
        if not instance_path:
            raise UpdateError("Instance path could not be determined")
        
        # Check for NeoForge version change - if changed, perform clean installation
        if self.check_for_neoforge_version_change():
            self._update_progress("NeoForge version change detected - performing clean installation...")
            self._perform_clean_installation(instance_path)
            return
        
        # Check if instance is already properly set up
        if self.check_instance_exists():
            self._update_progress("Instance already exists and is properly configured")
            self.logger.info("Instance verification passed - skipping full setup")
            # Still ensure launcher profile is up to date (lightweight operation)
            self._ensure_launcher_profile(instance_path)
            return
        
        self.logger.info("Instance setup required - checking what needs to be done...")
        
        # Create the instance directory if it doesn't exist
        if not instance_path.exists():
            self._update_progress("Creating instance directory...")
            self.logger.info(f"Creating new instance directory at: {instance_path}")
            instance_path.mkdir(parents=True, exist_ok=True)
            
            # Create necessary subdirectories
            subdirs = ['mods', 'config', 'resourcepacks', 'kubejs', 'defaultconfigs', 'versions']
            for subdir in subdirs:
                (instance_path / subdir).mkdir(exist_ok=True)
        else:
            # Instance directory exists, check if missing essential subdirectories
            subdirs = ['mods', 'config', 'resourcepacks', 'kubejs', 'defaultconfigs', 'versions']
            for subdir in subdirs:
                subdir_path = instance_path / subdir
                if not subdir_path.exists():
                    self._update_progress(f"Creating missing directory: {subdir}")
                    self.logger.info(f"Creating missing subdirectory: {subdir}")
                    subdir_path.mkdir(exist_ok=True)
        
        # Create launcher profile BEFORE installing NeoForge
        self._ensure_launcher_profile(instance_path)
        
        # Check if NeoForge is installed
        if not self._is_neoforge_installed(instance_path):
            self._update_progress("Installing NeoForge...")
            self.logger.info("NeoForge not found - installing...")
            self._install_neoforge(instance_path)
        else:
            self._update_progress("NeoForge already installed")
            self.logger.info("NeoForge already installed - skipping installation")
    
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
            profile_needs_update = False
            
            # Define optimized Java arguments for performance (only used for new profiles)
            default_java_args = "-Xmx8G -Xms4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M"
            
            for profile_id, profile_data in profiles_data.get("profiles", {}).items():
                # Check by name OR by gameDir (to update existing instances)
                if (profile_data.get("name") == profile_name or 
                    profile_data.get("gameDir") == str(instance_path)):
                    
                    # Check if profile needs updating (but DON'T touch Java arguments if they exist)
                    needs_update = False
                    if profile_data.get("name") != profile_name:
                        profile_data["name"] = profile_name
                        needs_update = True
                    if profile_data.get("gameDir") != str(instance_path):
                        profile_data["gameDir"] = str(instance_path)
                        needs_update = True
                    # Get current NeoForge version dynamically
                    current_neoforge_version = self._get_neoforge_version()
                    if profile_data.get("lastVersionId") != current_neoforge_version:
                        profile_data["lastVersionId"] = current_neoforge_version
                        needs_update = True
                    if profile_data.get("type") != "custom":
                        profile_data["type"] = "custom"
                        needs_update = True
                    if profile_data.get("icon") != "Furnace":
                        profile_data["icon"] = "Furnace"
                        needs_update = True
                    # NOTE: We intentionally DO NOT update javaArgs here - preserve user customizations
                    
                    profile_exists = True
                    profile_needs_update = needs_update
                    break
            
            # Only create new profile if it doesn't exist
            if not profile_exists:
                # Create new profile with optimized default Java arguments
                profile_id = str(uuid.uuid4()).replace('-', '')
                
                # Get current NeoForge version dynamically
                current_neoforge_version = self._get_neoforge_version()
                
                new_profile = {
                    "name": profile_name,
                    "type": "custom",
                    "created": "2024-01-01T00:00:00.000Z",
                    "lastUsed": "2024-01-01T00:00:00.000Z",
                    "lastVersionId": current_neoforge_version,
                    "icon": "Furnace",
                    "gameDir": str(instance_path),
                    "javaArgs": default_java_args  # Set optimized defaults only for new profiles
                }
                
                profiles_data["profiles"][profile_id] = new_profile
                profile_needs_update = True
            
            # Only save if we made changes
            if profile_needs_update:
                with open(launcher_profiles_path, 'w', encoding='utf-8') as f:
                    json.dump(profiles_data, f, indent=2)
                self.logger.info("Updated launcher profile")
            else:
                self.logger.info("Launcher profile already up to date")
                
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
        # Check if instance exists
        instance_exists = self.check_instance_exists()
        
        # If no updates available and instance exists, nothing to do
        if not force and not update_info.updates_available and instance_exists:
            self.logger.warning("No updates available")
            return False
        
        try:
            # First, ensure the instance is properly set up (installs NeoForge if needed)
            self._ensure_instance_setup()
            
            # If there are file updates available OR we just created a new instance, download and sync files
            if update_info.updates_available or force or not instance_exists:
                # Download and extract the release
                return self._download_and_extract_release(update_info)
            else:
                # Instance was set up but no file updates needed
                self.logger.info("Instance setup completed successfully")
                return True
                
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
                extracted_folder = self.file_ops.extract_zip(zip_path, extract_path)
                if not extracted_folder:
                    raise Exception("Failed to extract ZIP file")
            except Exception as e:
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
            instance_path.mkdir(parents=True, exist_ok=True)
            
            # Sync everything from the repo to the instance
            for item in source_path.iterdir():
                if item.is_dir():
                    dest_folder = instance_path / item.name
                    self._sync_directory(item, dest_folder)
                elif item.is_file():
                    dest_file = instance_path / item.name
                    self._sync_file(item, dest_file)
            
            # After syncing files, check if we need to configure resource packs
            self._configure_resource_packs_after_sync(instance_path)
            
            return True
            
        except Exception as e:
            raise UpdateError(f"Failed to sync files: {e}")
    
    def _sync_directory(self, source: Path, destination: Path) -> None:
        """Sync a directory from source to destination.
        
        Args:
            source: Source directory path
            destination: Destination directory path
        """
        self._update_progress(f"Syncing directory: {source.name}")
        
        # First check if the directory actually needs updating
        if destination.exists() and not self._compare_folder_contents(source, destination):
            self.logger.info(f"Directory {source.name} is already up to date - skipping sync")
            return
        
        try:
            # For mods folder, remove files that exist locally but not in the repo
            if source.name.lower() == "mods" and destination.exists():
                self._cleanup_unwanted_mods(source, destination)
            
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
    
    def _cleanup_unwanted_mods(self, source: Path, destination: Path) -> None:
        """Remove mods that exist locally but not in the repository.
        
        Args:
            source: Source mods directory from repository
            destination: Local mods directory
        """
        try:
            # Get list of mod files in the repository
            repo_mods = set()
            for file_path in source.rglob('*.jar'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(source)
                    # Skip .connector folder
                    if not (str(rel_path).startswith('.connector') or '.connector' in str(rel_path)):
                        repo_mods.add(rel_path)
            
            # Get list of mod files in local directory
            local_mods = []
            for file_path in destination.rglob('*.jar'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(destination)
                    # Skip .connector folder
                    if not (str(rel_path).startswith('.connector') or '.connector' in str(rel_path)):
                        local_mods.append((rel_path, file_path))
            
            # Remove local mods that don't exist in the repository
            removed_count = 0
            for rel_path, full_path in local_mods:
                if rel_path not in repo_mods:
                    try:
                        full_path.unlink()
                        self.logger.info(f"Removed unwanted mod: {rel_path}")
                        removed_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove mod {rel_path}: {e}")
            
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} unwanted mod(s)")
            else:
                self.logger.info("No unwanted mods to remove")
                
        except Exception as e:
            self.logger.warning(f"Error during mod cleanup: {e}")

    def _sync_file(self, source: Path, destination: Path) -> None:
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
    
    def _configure_resource_packs_after_sync(self, instance_path: Path) -> None:
        """Configure resource packs after files have been synced.
        
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
            
            self.logger.info(f"Checking for resource packs in: {resourcepacks_dir}")
            
            # List all files in resourcepacks directory for debugging
            pack_files = list(resourcepacks_dir.iterdir())
            if pack_files:
                self.logger.info(f"Found {len(pack_files)} files in resourcepacks directory:")
                for pack_file in pack_files:
                    self.logger.info(f"  - {pack_file.name}")
            else:
                self.logger.info("No files found in resourcepacks directory")
                return
            
            # Look for FFT resource packs
            fft_pack_found = False
            for pack_file in pack_files:
                if pack_file.name.startswith("fft-resourcepack") or pack_file.name.startswith("fft_resourcepack"):
                    self._update_progress("Configuring resource pack...")
                    self.logger.info(f"Found FFT resource pack: {pack_file.name}")
                    
                    # Use NeoForge service to configure the resource pack
                    neoforge_service = NeoForgeService(self.config)
                    pack_name = pack_file.stem if pack_file.suffix == '.zip' else pack_file.name
                    
                    success = neoforge_service.configure_default_resource_pack(instance_path, pack_name)
                    if success:
                        self.logger.info(f"Successfully configured resource pack: {pack_name}")
                        self._update_progress("Resource pack configured successfully")
                    else:
                        self.logger.warning(f"Failed to configure resource pack: {pack_name}")
                    
                    fft_pack_found = True
                    break
            
            if not fft_pack_found:
                self.logger.info("No FFT resource packs found in resourcepacks directory")
                
        except Exception as e:
            self.logger.warning(f"Error configuring resource packs: {e}")
            # Don't raise the error - this is not critical for the update process
    
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
    
    def _get_neoforge_version(self) -> str:
        """Get the current NeoForge version.
        
        Returns:
            Current NeoForge version string
        """
        # Import here to avoid circular imports
        from .neoforge_service import NeoForgeService
        neoforge_service = NeoForgeService(self.config)
        return f"neoforge-{neoforge_service.neoforge_version}"
    
    def check_for_neoforge_version_change(self) -> bool:
        """Check if the NeoForge version has changed.
        
        Returns:
            True if version has changed and clean installation is needed
        """
        instance_path = self.config.get_selected_instance_path()
        if not instance_path or not instance_path.exists():
            return False
        
        expected_version = self._get_neoforge_version()
        installed_version = self._get_installed_neoforge_version(instance_path)
        
        if installed_version is None:
            # No NeoForge installed yet
            return False
        
        version_changed = installed_version != expected_version
        if version_changed:
            self.logger.info(f"NeoForge version change detected: {installed_version} -> {expected_version}")
        
        return version_changed
    
    def _get_installed_neoforge_version(self, instance_path: Path) -> Optional[str]:
        """Get the currently installed NeoForge version.
        
        Args:
            instance_path: Path to the instance directory
            
        Returns:
            Installed NeoForge version string or None if not found
        """
        versions_dir = instance_path / "versions"
        if not versions_dir.exists():
            return None
        
        # Look for NeoForge version directories
        for version_dir in versions_dir.iterdir():
            if version_dir.is_dir() and "neoforge" in version_dir.name.lower():
                return version_dir.name
        
        return None
    
    def _perform_clean_installation(self, instance_path: Path) -> None:
        """Perform a clean installation with backup and restore.
        
        Args:
            instance_path: Path to the instance directory
        """
        try:
            # Import here to avoid circular imports
            from .backup_service import BackupService
            
            backup_service = BackupService(self.config)
            if self.progress_callback:
                backup_service.set_progress_callback(self.progress_callback)
            
            # Perform clean install (backup configs, clean instance, install fresh)
            backup_path = backup_service.perform_clean_install(instance_path)
            
            # Restore configurations if backup was created
            if backup_path:
                self._update_progress("Restoring configurations...")
                if backup_service.restore_instance_configs(backup_path, instance_path):
                    self.logger.info("Configurations restored successfully")
                else:
                    self.logger.warning("Failed to restore some configurations")
            
        except Exception as e:
            self.logger.error(f"Clean installation failed: {e}")
            raise
