"""Minecraft service for managing Minecraft operations."""

import subprocess
from pathlib import Path
from typing import List, Optional
from ..models.config import LauncherConfig
from ..utils.logger import get_logger


class MinecraftService:
    """Service for managing Minecraft operations."""
    
    def __init__(self, config: LauncherConfig):
        """Initialize the Minecraft service.
        
        Args:
            config: Launcher configuration
        """
        self.config = config
        self.logger = get_logger()
    
    def validate_installation(self) -> bool:
        """Validate that Minecraft is properly installed.
        
        Returns:
            True if Minecraft installation is valid, False otherwise.
        """
        minecraft_path = self.config.get_minecraft_path()
        
        if not minecraft_path.exists():
            self.logger.error(f"Minecraft directory not found: {minecraft_path}")
            return False
        
        if not minecraft_path.is_dir():
            self.logger.error(f"Minecraft path is not a directory: {minecraft_path}")
            return False
        
        # Check if executable exists
        executable_path = self.get_executable_path()
        if not executable_path:
            self.logger.error("Minecraft executable not found")
            return False
        
        self.logger.info(f"Minecraft installation validated: {minecraft_path}")
        return True
    
    def get_executable_path(self) -> Optional[Path]:
        """Get the path to the Minecraft executable.
        
        Returns:
            Path to the executable if found, None otherwise.
        """
        minecraft_path = self.config.get_minecraft_path()
        
        # Try the configured executable first
        configured_exe = Path(self.config.minecraft_executable)
        
        # If it's an absolute path, use it directly
        if configured_exe.is_absolute():
            if configured_exe.exists():
                return configured_exe
        else:
            # Try relative to Minecraft directory
            exe_path = minecraft_path / configured_exe
            if exe_path.exists():
                return exe_path
        
        # Try common Minecraft executable names
        common_names = [
            'minecraft.exe',
            'MinecraftLauncher.exe',
            'launcher.exe',
            'ATLauncher.exe',
            'MultiMC.exe',
            'PrismLauncher.exe'
        ]
        
        for name in common_names:
            exe_path = minecraft_path / name
            if exe_path.exists():
                self.logger.info(f"Found Minecraft executable: {exe_path}")
                return exe_path
        
        return None
    
    def launch(self) -> bool:
        """Launch Minecraft.
        
        Returns:
            True if launch was successful, False otherwise.
        """
        if not self.validate_installation():
            return False
        
        executable_path = self.get_executable_path()
        if not executable_path:
            self.logger.error("Cannot launch: Minecraft executable not found")
            return False
        
        try:
            self.logger.info(f"Launching Minecraft: {executable_path}")
            
            # Launch Minecraft in its own directory
            minecraft_path = self.config.get_minecraft_path()
            
            subprocess.Popen(
                [str(executable_path)],
                cwd=str(minecraft_path),
                start_new_session=True
            )
            
            self.logger.info("Minecraft launched successfully")
            return True
            
        except (subprocess.SubprocessError, OSError) as e:
            self.logger.error(f"Failed to launch Minecraft: {e}")
            return False
    
    def get_installation_info(self) -> dict:
        """Get information about the Minecraft installation.
        
        Returns:
            Dictionary containing installation information.
        """
        minecraft_path = self.config.get_minecraft_path()
        executable_path = self.get_executable_path()
        
        info = {
            'minecraft_directory': str(minecraft_path),
            'minecraft_exists': minecraft_path.exists(),
            'minecraft_executable': str(executable_path) if executable_path else None,
            'executable_exists': executable_path.exists() if executable_path else False,
            'is_valid': self.validate_installation()
        }
        
        # Add folder information
        folders_info = {}
        for folder in self.config.folders_to_sync:
            folder_path = minecraft_path / folder
            folders_info[folder] = {
                'exists': folder_path.exists(),
                'path': str(folder_path),
                'file_count': len(list(folder_path.rglob('*'))) if folder_path.exists() else 0
            }
        
        info['folders'] = folders_info
        
        return info
    
    def get_missing_folders(self) -> List[str]:
        """Get list of folders that should exist but don't.
        
        Returns:
            List of missing folder names.
        """
        minecraft_path = self.config.get_minecraft_path()
        missing = []
        
        for folder in self.config.folders_to_sync:
            folder_path = minecraft_path / folder
            if not folder_path.exists():
                missing.append(folder)
        
        return missing
