"""Service for managing Minecraft launcher profiles."""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from ..models.config import LauncherConfig
from ..utils.logging_utils import get_logger


class LauncherProfilesService:
    """Service responsible for managing Minecraft launcher profiles."""
    
    def __init__(self, config: LauncherConfig):
        """Initialize the launcher profiles service.
        
        Args:
            config: Launcher configuration
        """
        self.config = config
        self.logger = get_logger()
    
    def create_launcher_profile(self, instance_path: Path, profile_name: str = "FFTClient") -> bool:
        """Create or update a Minecraft launcher profile for the instance.
        
        Args:
            instance_path: Path to the instance directory
            profile_name: Name for the profile
            
        Returns:
            True if profile was created/updated successfully, False otherwise
        """
        try:
            minecraft_dir = Path(os.environ['APPDATA']) / ".minecraft"
            launcher_profiles_path = minecraft_dir / "launcher_profiles.json"
            
            # Load existing profiles or create new structure
            profiles_data = self._load_or_create_profiles_structure(launcher_profiles_path)
            
            # Clean any existing corrupted profiles
            self._clean_corrupted_profiles(profiles_data)
            
            # Check if profile already exists for this instance
            profile_exists = False
            profile_needs_update = False
            
            for profile_id, profile_data in profiles_data.get("profiles", {}).items():
                # Check by name OR by gameDir (to update existing instances)
                if (profile_data.get("name") == profile_name or 
                    profile_data.get("gameDir") == str(instance_path)):
                    
                    # Update existing profile
                    needs_update = self._update_existing_profile(profile_data, instance_path, profile_name)
                    profile_exists = True
                    profile_needs_update = needs_update
                    break
            
            # Create new profile if it doesn't exist
            if not profile_exists:
                profile_id = str(uuid.uuid4()).replace('-', '')
                new_profile = self._create_new_profile(instance_path, profile_name)
                profiles_data["profiles"][profile_id] = new_profile
                profile_needs_update = True
            
            # Save if changes were made
            if profile_needs_update:
                self._save_profiles(launcher_profiles_path, profiles_data)
                self.logger.info(f"Launcher profile '{profile_name}' updated successfully")
            else:
                self.logger.info(f"Launcher profile '{profile_name}' already up to date")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create/update launcher profile: {e}")
            return False
    
    def _load_or_create_profiles_structure(self, profiles_path: Path) -> Dict[str, Any]:
        """Load existing profiles or create new structure."""
        if profiles_path.exists():
            try:
                with open(profiles_path, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
                
                # Ensure required fields exist
                if "profiles" not in profiles_data:
                    profiles_data["profiles"] = {}
                if "settings" not in profiles_data:
                    profiles_data["settings"] = self._get_default_settings()
                if "version" not in profiles_data:
                    profiles_data["version"] = 4
                
                return profiles_data
            except Exception as e:
                self.logger.warning(f"Failed to load existing profiles, creating new: {e}")
        
        # Create new structure
        return {
            "profiles": {},
            "settings": self._get_default_settings(),
            "version": 4
        }
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default launcher settings."""
        return {
            "crashAssistance": False,
            "enableAdvanced": False,
            "enableAnalytics": True,
            "enableHistorical": False,
            "enableReleases": True,
            "enableSnapshots": False,
            "keepLauncherOpen": False,
            "profileSorting": "ByLastPlayed",
            "showGameLog": False,
            "showMenu": False,
            "soundOn": False
        }
    
    def _clean_corrupted_profiles(self, profiles_data: Dict[str, Any]) -> None:
        """Clean any corrupted profiles in the data."""
        profiles_cleaned = False
        
        for profile_id, profile_data in profiles_data.get("profiles", {}).items():
            if "icon" in profile_data:
                icon_value = profile_data["icon"]
                # Check if icon is a very long string (likely base64 encoded image)
                if isinstance(icon_value, str) and len(icon_value) > 100:
                    self.logger.info(f"Fixing corrupted long icon string in profile: {profile_data.get('name', profile_id)}")
                    profile_data["icon"] = "Furnace"
                    profiles_cleaned = True
                # Fix empty or null icons
                elif icon_value is None or icon_value == "":
                    profile_data["icon"] = "Furnace"
                    profiles_cleaned = True
            elif profile_data.get("type") == "custom":
                # Add missing icon to custom profiles
                profile_data["icon"] = "Furnace"
                profiles_cleaned = True
        
        if profiles_cleaned:
            self.logger.info("Cleaned corrupted profile icons")
    
    def _update_existing_profile(self, profile_data: Dict[str, Any], instance_path: Path, profile_name: str) -> bool:
        """Update an existing profile and return True if changes were made."""
        needs_update = False
        current_neoforge_version = self._get_current_neoforge_version()
        
        if profile_data.get("name") != profile_name:
            profile_data["name"] = profile_name
            needs_update = True
        
        if profile_data.get("gameDir") != str(instance_path):
            profile_data["gameDir"] = str(instance_path)
            needs_update = True
        
        if profile_data.get("lastVersionId") != current_neoforge_version:
            profile_data["lastVersionId"] = current_neoforge_version
            needs_update = True
        
        if profile_data.get("type") != "custom":
            profile_data["type"] = "custom"
            needs_update = True
        
        if profile_data.get("icon") != "Furnace":
            profile_data["icon"] = "Furnace"
            needs_update = True
        
        # Update lastUsed timestamp
        profile_data["lastUsed"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-3] + "Z"
        needs_update = True
        
        return needs_update
    
    def _create_new_profile(self, instance_path: Path, profile_name: str) -> Dict[str, Any]:
        """Create a new profile dictionary."""
        current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")[:-3] + "Z"
        current_neoforge_version = self._get_current_neoforge_version()
        
        # Default Java arguments for performance
        default_java_args = "-Xmx8G -Xms4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M"
        
        return {
            "created": current_time,
            "gameDir": str(instance_path),
            "icon": "Furnace",
            "javaArgs": default_java_args,
            "lastUsed": current_time,
            "lastVersionId": current_neoforge_version,
            "name": profile_name,
            "type": "custom"
        }
    
    def _get_current_neoforge_version(self) -> str:
        """Get the current NeoForge version."""
        try:
            # Import here to avoid circular imports
            from .neoforge_service import NeoForgeService
            neoforge_service = NeoForgeService(self.config)
            return f"neoforge-{neoforge_service.neoforge_version}"
        except Exception:
            return "neoforge-21.1.190"
    
    def _save_profiles(self, profiles_path: Path, profiles_data: Dict[str, Any]) -> None:
        """Save profiles to file."""
        # Ensure parent directory exists
        profiles_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(profiles_path, 'w', encoding='utf-8') as f:
            json.dump(profiles_data, f, indent=2)
    
    def cleanup_corrupted_profiles(self, instance_path: Optional[Path] = None) -> bool:
        """Clean up corrupted launcher profiles with extremely long icon strings.
        
        Args:
            instance_path: Optional path to instance directory. If None, cleans main .minecraft profiles.
            
        Returns:
            True if cleanup was successful, False otherwise.
        """
        try:
            if instance_path:
                # Clean instance-specific launcher profiles
                profiles_path = instance_path / "launcher_profiles.json"
            else:
                # Clean main .minecraft launcher profiles
                minecraft_dir = Path(os.environ['APPDATA']) / ".minecraft"
                profiles_path = minecraft_dir / "launcher_profiles.json"
            
            if not profiles_path.exists():
                self.logger.info(f"No launcher profiles found at {profiles_path}")
                return True
            
            # Load profiles
            with open(profiles_path, 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)
            
            # Clean corrupted profiles
            original_data = json.dumps(profiles_data, sort_keys=True)
            self._clean_corrupted_profiles(profiles_data)
            
            # Save if changes were made
            if json.dumps(profiles_data, sort_keys=True) != original_data:
                self._save_profiles(profiles_path, profiles_data)
                self.logger.info(f"Successfully cleaned corrupted profiles in {profiles_path}")
            else:
                self.logger.info(f"No corrupted profiles found in {profiles_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup launcher profiles: {e}")
            return False
    
    def remove_profile_by_name(self, profile_name: str) -> bool:
        """Remove a profile by name.
        
        Args:
            profile_name: Name of the profile to remove
            
        Returns:
            True if profile was removed successfully, False otherwise
        """
        try:
            minecraft_dir = Path(os.environ['APPDATA']) / ".minecraft"
            launcher_profiles_path = minecraft_dir / "launcher_profiles.json"
            
            if not launcher_profiles_path.exists():
                self.logger.info("No launcher profiles file found")
                return True
            
            # Load profiles
            with open(launcher_profiles_path, 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)
            
            # Find and remove profile
            profile_removed = False
            for profile_id, profile_data in list(profiles_data.get("profiles", {}).items()):
                if profile_data.get("name") == profile_name:
                    del profiles_data["profiles"][profile_id]
                    profile_removed = True
                    self.logger.info(f"Removed profile: {profile_name}")
                    break
            
            if profile_removed:
                self._save_profiles(launcher_profiles_path, profiles_data)
                return True
            else:
                self.logger.info(f"Profile not found: {profile_name}")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove profile: {e}")
            return False
