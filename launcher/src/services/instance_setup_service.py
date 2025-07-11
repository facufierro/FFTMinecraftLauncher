"""Service for managing instance setup and verification."""

import json
import os
import uuid
from pathlib import Path
from typing import Optional
from ..models.config import LauncherConfig
from ..utils.logging_utils import get_logger


class InstanceSetupService:
    """Service responsible for Minecraft instance setup and verification."""
    
    def __init__(self, config: LauncherConfig):
        """Initialize the instance setup service.
        
        Args:
            config: Launcher configuration
        """
        self.config = config
        self.logger = get_logger()
    
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
        has_neoforge = self.is_neoforge_installed(instance_path)
        
        if not has_neoforge:
            self.logger.warning("NeoForge not installed in instance")
            return False
        
        self.logger.info("Instance exists and has NeoForge - checking resource pack configuration...")
        
        # Check if resource packs need to be configured
        self.check_and_configure_resource_packs(instance_path)
        
        return True
    
    def is_neoforge_installed(self, instance_path: Path) -> bool:
        """Check if NeoForge is installed in the instance.
        
        Args:
            instance_path: Path to the instance directory
            
        Returns:
            True if NeoForge is installed, False otherwise.
        """
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
    
    def ensure_instance_setup(self) -> None:
        """Ensure the instance is properly set up with NeoForge and launcher profile.
        
        Raises:
            Exception: If instance setup fails
        """
        instance_path = self.config.get_selected_instance_path()
        if not instance_path:
            raise Exception("Instance path could not be determined")
        
        # Check for NeoForge version change - if changed, perform clean installation
        if self.check_for_neoforge_version_change():
            from .backup_service import BackupService
            backup_service = BackupService(self.config)
            backup_service.perform_clean_install(instance_path)
            return
        
        # Check if instance is already properly set up
        if self.check_instance_exists():
            self.logger.info("Instance verification passed - skipping full setup")
            # Still ensure launcher profile is up to date (lightweight operation)
            self.ensure_launcher_profile(instance_path)
            return
        
        self.logger.info("Instance setup required - checking what needs to be done...")
        
        # Create the instance directory if it doesn't exist
        if not instance_path.exists():
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
                    self.logger.info(f"Creating missing subdirectory: {subdir}")
                    subdir_path.mkdir(exist_ok=True)
        
        # Create launcher profile BEFORE installing NeoForge
        self.ensure_launcher_profile(instance_path)
        
        # Check if NeoForge is installed
        if not self.is_neoforge_installed(instance_path):
            self.logger.info("NeoForge not found - installing...")
            self.install_neoforge(instance_path)
        else:
            self.logger.info("NeoForge already installed - skipping installation")
    
    def install_neoforge(self, instance_path: Path) -> None:
        """Install NeoForge to the instance.
        
        Args:
            instance_path: Path to the instance directory
            
        Raises:
            Exception: If NeoForge installation fails
        """
        try:
            # Import here to avoid circular imports
            from ..services.neoforge_service import NeoForgeService
            
            neoforge_service = NeoForgeService(self.config)
            success = neoforge_service.install_neoforge_to_instance_path(instance_path)
            
            if not success:
                raise Exception("Failed to install NeoForge")
                
        except Exception as e:
            raise Exception(f"NeoForge installation failed: {e}")
    
    def ensure_launcher_profile(self, instance_path: Path) -> None:
        """Ensure a Minecraft launcher profile exists for this instance.
        
        Args:
            instance_path: Path to the instance directory
        """
        try:
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
                    current_neoforge_version = self.get_neoforge_version()
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
                current_neoforge_version = self.get_neoforge_version()
                
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
    
    def check_and_configure_resource_packs(self, instance_path: Path) -> None:
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
    
    def get_neoforge_version(self) -> str:
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
        
        expected_version = self.get_neoforge_version()
        installed_version = self.get_installed_neoforge_version(instance_path)
        
        if installed_version is None:
            # No NeoForge installed yet
            return False
        
        version_changed = installed_version != expected_version
        if version_changed:
            self.logger.info(f"NeoForge version change detected: {installed_version} -> {expected_version}")
        
        return version_changed
    
    def get_installed_neoforge_version(self, instance_path: Path) -> Optional[str]:
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
