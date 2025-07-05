"""Configuration model for the FFT Minecraft Launcher."""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class LauncherConfig:
    """Configuration settings for the Minecraft launcher."""
    
    # Repository settings
    github_repo: str = "facufierro/FFTClientMinecraft1211"
    use_releases: bool = True
    release_tag: str = "latest"
    
    # Local paths
    minecraft_dir: str = "../FFTClientMinecraft1211"
    minecraft_executable: str = "minecraft.exe"
    
    # Sync settings
    folders_to_sync: List[str] = field(default_factory=lambda: [
        "config", "mods", "resourcepacks", "kubejs", "scripts", "defaultconfigs"
    ])
    
    # Behavior settings
    check_on_startup: bool = True
    auto_update: bool = False
    night_mode: bool = False
    
    # State
    current_version: Optional[str] = None
    last_check: Optional[str] = None
    
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
                if hasattr(config, key):
                    setattr(config, key, value)
                    
            return config
            
        except (json.JSONDecodeError, IOError) as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        try:
            # Convert to dict, excluding None values
            data = {
                key: value for key, value in self.__dict__.items()
                if value is not None
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
                
        except IOError as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")
    
    def get_minecraft_path(self) -> Path:
        """Get the Minecraft directory as a Path object."""
        return Path(self.minecraft_dir).resolve()
    
    def get_minecraft_executable_path(self) -> Path:
        """Get the full path to the Minecraft executable."""
        minecraft_path = self.get_minecraft_path()
        return minecraft_path / self.minecraft_executable
    
    def validate(self) -> List[str]:
        """Validate the configuration and return a list of errors."""
        errors = []
        
        if not self.github_repo:
            errors.append("GitHub repository must be specified")
        
        if not self.minecraft_dir:
            errors.append("Minecraft directory must be specified")
            
        if not self.minecraft_executable:
            errors.append("Minecraft executable must be specified")
            
        if not self.folders_to_sync:
            errors.append("At least one folder to sync must be specified")
            
        return errors


class ConfigurationError(Exception):
    """Exception raised for configuration-related errors."""
    pass
