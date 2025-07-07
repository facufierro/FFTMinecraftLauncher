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
        """Get the launcher's instance directory as a Path object."""
        # Use instance folder in the same directory as the executable
        import sys
        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller bundle
            exe_dir = Path(sys.executable).parent
        else:
            # Running as a Python script - use the main app.py directory
            exe_dir = Path(__file__).parent.parent.parent  # Go up from src/models/ to project root
        
        return exe_dir / "instance"
    
    def get_selected_instance_path(self) -> Optional[Path]:
        """Get the path to the launcher's instance."""
        instance_path = self.get_minecraft_path()
        
        # Create the instance directory if it doesn't exist
        if not instance_path.exists():
            instance_path.mkdir(parents=True, exist_ok=True)
            
            # Create necessary subdirectories
            subdirs = ['mods', 'config', 'resourcepacks', 'kubejs', 'defaultconfigs', 'versions']
            for subdir in subdirs:
                (instance_path / subdir).mkdir(exist_ok=True)
        
        return instance_path
    
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
