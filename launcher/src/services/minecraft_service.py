"""Minecraft service for managing Minecraft launcher operations."""

import json
import os
import subprocess
from pathlib import Path
from typing import List, Optional
from ..models.config import LauncherConfig
from ..utils.logging_utils import get_logger
from .neoforge_service import NeoForgeService


class MinecraftService:
    """Service for managing Minecraft launcher operations."""
    
    def __init__(self, config: LauncherConfig):
        """Initialize the Minecraft service.
        
        Args:
            config: Launcher configuration
        """
        self.config = config
        self.logger = get_logger()
        self.neoforge_service = NeoForgeService(config)
    
    def validate_installation(self) -> bool:
        """Validate that Minecraft launcher is available.
        
        Returns:
            True if Minecraft launcher is available, False otherwise.
        """
        # Check if Minecraft launcher can be found
        launcher_path = self._find_minecraft_launcher()
        if launcher_path:
            self.logger.info(f"Minecraft launcher found at: {launcher_path}")
            return True
        
        self.logger.warning("Minecraft launcher not found")
        return False
    
    def _find_minecraft_launcher(self) -> Optional[str]:
        """Find the Minecraft launcher executable.
        
        Returns:
            Path to the launcher executable if found, None otherwise.
        """
        # Common Minecraft launcher locations (prioritize actual executables over protocol)
        launcher_candidates = [
            # Official Minecraft Launcher (standalone) - prioritized
            os.path.expandvars(r"%ProgramFiles%\Minecraft Launcher\MinecraftLauncher.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Minecraft Launcher\MinecraftLauncher.exe"),
            # Legacy launcher
            os.path.expandvars(r"%ProgramFiles%\Minecraft\MinecraftLauncher.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Minecraft\MinecraftLauncher.exe"),
            # User AppData locations
            os.path.expandvars(r"%LOCALAPPDATA%\Packages\Microsoft.4297127D64EC6_8wekyb3d8bbwe\LocalCache\Local\game\Minecraft Launcher\MinecraftLauncher.exe"),
            # MultiMC/PolyMC/Prism Launcher
            os.path.expandvars(r"%ProgramFiles%\MultiMC\MultiMC.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\MultiMC\MultiMC.exe"),
            os.path.expandvars(r"%ProgramFiles%\PolyMC\PolyMC.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\PolyMC\PolyMC.exe"),
            os.path.expandvars(r"%ProgramFiles%\PrismLauncher\prismlauncher.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\PrismLauncher\prismlauncher.exe"),
            # Microsoft Store launcher app ID (Java Edition launcher specifically)
            "minecraft-launcher:",  # Try this as a specific launcher protocol
            # Protocol handler as last resort (may open Bedrock Edition)
            "minecraft:",
        ]
        
        # Test each candidate
        for candidate in launcher_candidates:
            if candidate.endswith(":"):
                # Protocol handler - we'll assume it's available if this is Windows
                if os.name == 'nt':
                    return candidate
                continue
            
            if os.path.exists(candidate):
                return candidate
        
        return None
    
    def launch(self) -> bool:
        """Launch the Minecraft launcher.
        
        Returns:
            True if launch was successful, False otherwise.
        """
        try:
            self.logger.info("Launching Minecraft launcher...")
            
            launcher_path = self._find_minecraft_launcher()
            if not launcher_path:
                self.logger.error("Minecraft launcher not found")
                return False
            
            # Launch the Minecraft launcher
            if launcher_path.endswith(":"):
                if launcher_path == "minecraft-launcher:":
                    # Try using the specific Minecraft Launcher app ID
                    self.logger.info("Launching Minecraft Launcher via Microsoft Store app")
                    subprocess.Popen(["start", "shell:AppsFolder\\Microsoft.4297127D64EC6_8wekyb3d8bbwe!Minecraft"], shell=True)
                else:
                    # Protocol handler - avoid using this as it may open Bedrock Edition
                    self.logger.warning("Using protocol handler - may open wrong Minecraft edition")
                    subprocess.Popen(["start", launcher_path], shell=True)
            else:
                # Direct executable - preferred method
                cmd = [launcher_path]
                
                # Add arguments to launch with specific profile if selected
                if self.config.selected_instance and self.config.selected_instance != "Default (.minecraft)":
                    # Try to launch with the selected profile directly
                    cmd.extend(["--launcherui"])  # Show launcher UI to allow profile selection
                    
                self.logger.info(f"Launching: {' '.join(cmd)}")
                subprocess.Popen(cmd, start_new_session=True)
            
            self.logger.info("Minecraft launcher started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to launch Minecraft launcher: {e}")
            return False
    
    def get_available_instances(self) -> List[str]:
        """Get list of available Minecraft instances.
        
        Returns:
            List of instance names.
        """
        return self.neoforge_service.get_available_instances()
    
    def install_neoforge_to_instance(self, instance_name: str) -> bool:
        """Install NeoForge to the specified instance.
        
        Args:
            instance_name: Name of the instance
            
        Returns:
            True if installation was successful, False otherwise.
        """
        return self.neoforge_service.install_neoforge_to_instance(instance_name)
    
    def is_neoforge_installed(self, instance_name: str) -> bool:
        """Check if NeoForge is installed in the specified instance.
        
        Args:
            instance_name: Name of the instance
            
        Returns:
            True if NeoForge is installed, False otherwise.
        """
        return self.neoforge_service.is_neoforge_installed(instance_name)
    
    def get_installation_info(self) -> dict:
        """Get information about the Minecraft installation.
        
        Returns:
            Dictionary containing installation information.
        """
        launcher_path = self._find_minecraft_launcher()
        instances = self.get_available_instances()
        
        info = {
            'launcher_found': launcher_path is not None,
            'launcher_path': launcher_path,
            'available_instances': instances,
            'selected_instance': self.config.selected_instance,
            'is_valid': self.validate_installation()
        }
        
        # Add NeoForge status for selected instance
        if self.config.selected_instance:
            info['neoforge_installed'] = self.is_neoforge_installed(self.config.selected_instance)
        else:
            info['neoforge_installed'] = False
        
        return info
    

