"""Configuration model for the FFT Minecraft Launcher."""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
from ..constants import GITHUB_REPO, DEFAULT_SYNC_FOLDERS


@dataclass
class LauncherConfig:
    """Configuration settings for the Minecraft launcher."""
    
    # Instance settings
    selected_instance: str = ""  # Selected Minecraft launcher instance name
    
    # Sync settings
    folders_to_sync: List[str] = field(default_factory=lambda: DEFAULT_SYNC_FOLDERS)
    
    # Behavior settings
    check_on_startup: bool = True
    auto_update: bool = False
    night_mode: bool = False
    
    # State
    current_version: Optional[str] = None
    last_check: Optional[str] = None
    
    @property
    def github_repo(self) -> str:
        """Get the GitHub repository (hardcoded constant)."""
        return GITHUB_REPO
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'LauncherConfig':
        """Load configuration from JSON file."""
        if not os.path.exists(config_path):
            config = cls()
            config.save_to_file(config_path)
            return config
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create config with loaded data, using defaults for missing keys
            config = cls()
            for key, value in data.items():
                # Skip github_repo as it's now a constant
                if key == 'github_repo':
                    continue
                if hasattr(config, key):
                    setattr(config, key, value)
            
            # Migrate legacy settings
            config._migrate_legacy_settings()
                    
            return config
            
        except (json.JSONDecodeError, IOError) as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def _migrate_legacy_settings(self) -> None:
        """Migrate legacy settings to new format."""
        # Clear any legacy fields after migration
        pass
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        try:
            # Convert to dict, excluding None values and github_repo (constant)
            data = {
                key: value for key, value in self.__dict__.items()
                if value is not None and key not in ['github_repo']
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
        except IOError as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def get_minecraft_path(self) -> Path:
        """Get the Minecraft instances directory as a Path object."""
        return Path(os.environ['APPDATA']) / ".minecraft" / "instances"
    
    def get_selected_instance_path(self) -> Optional[Path]:
        """Get the path to the selected instance."""
        if not self.selected_instance:
            return None
        
        # Use the same logic as NeoForgeService to find instance paths
        return self._find_instance_path(self.selected_instance)
    
    def _find_instance_path(self, instance_name: str) -> Optional[Path]:
        """Find the path to a Minecraft launcher instance.
        
        Args:
            instance_name: Name of the instance
            
        Returns:
            Path to the instance directory, or None if not found.
        """
        minecraft_dir = Path(os.environ['APPDATA']) / ".minecraft"
        
        # Handle default Minecraft installation
        if instance_name == "Default (.minecraft)":
            if minecraft_dir.exists():
                return minecraft_dir
            return None
        
        # Handle launcher profiles (using direct profile names)
        launcher_profiles = minecraft_dir / "launcher_profiles.json"
        if launcher_profiles.exists():
            try:
                with open(launcher_profiles, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                
                for profile_id, profile_data in profiles.get("profiles", {}).items():
                    profile_name = profile_data.get("name", profile_id)
                    
                    # Handle "last release" name for unnamed/default profiles
                    if instance_name == "last release" and (not profile_name or profile_name.lower() in ["default", ""]):
                        # Return the custom gameDir if specified, otherwise default .minecraft
                        if "gameDir" in profile_data:
                            return Path(profile_data["gameDir"])
                        else:
                            return minecraft_dir
                    elif profile_name == instance_name:
                        # Return the custom gameDir if specified, otherwise default .minecraft
                        if "gameDir" in profile_data:
                            return Path(profile_data["gameDir"])
                        else:
                            return minecraft_dir
            except Exception:
                pass  # Fall through to other methods
        
        # Handle third-party launcher instances
        for launcher_name in ["PrismLauncher", "PolyMC", "MultiMC"]:
            if instance_name.endswith(f" ({launcher_name})"):
                base_instance_name = instance_name[:-len(f" ({launcher_name})")]
                launcher_dir = Path(os.environ['APPDATA']) / launcher_name / "instances"
                
                if launcher_dir.exists():
                    instance_dir = launcher_dir / base_instance_name
                    if instance_dir.exists():
                        # Check for .minecraft subdirectory (most common)
                        minecraft_subdir = instance_dir / ".minecraft"
                        if minecraft_subdir.exists():
                            return minecraft_subdir
                        # Check for minecraft subdirectory (alternative)
                        minecraft_subdir = instance_dir / "minecraft"
                        if minecraft_subdir.exists():
                            return minecraft_subdir
                        # Return the instance path itself as fallback
                        return instance_dir
        
        # Fallback: check for instances in .minecraft/instances (some launchers)
        instances_dir = minecraft_dir / "instances"
        if instances_dir.exists():
            # Extract base name if it has a launcher suffix
            base_name = instance_name
            for suffix in [" (PrismLauncher)", " (PolyMC)", " (MultiMC)", " (instances)"]:
                if instance_name.endswith(suffix):
                    base_name = instance_name[:-len(suffix)]
                    break
            
            instance_path = instances_dir / base_name
            if instance_path.exists():
                # Check for subdirectories
                for subdir_name in [".minecraft", "minecraft"]:
                    subdir = instance_path / subdir_name
                    if subdir.exists():
                        return subdir
                return instance_path
        
        return None
    
    def validate(self) -> List[str]:
        """Validate the configuration and return a list of errors."""
        errors = []
        
        # Don't require instance selection during initialization - user can set it in settings
        # if not self.selected_instance:
        #     errors.append("A Minecraft instance must be selected")
            
        if not self.folders_to_sync:
            errors.append("At least one folder to sync must be specified")
            
        return errors


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass
