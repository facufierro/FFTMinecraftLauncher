"""Minecraft service for managing Minecraft launcher operations."""

import os
import subprocess
from pathlib import Path
from typing import List, Optional
from ..models.config import LauncherConfig
from ..utils.logger import get_logger
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
    
    def create_neoforge_installation(self, installation_name: str, installation_dir: Optional[str] = None) -> bool:
        """Create a new NeoForge installation with a custom name and directory.
        
        Args:
            installation_name: Name for the new installation
            installation_dir: Optional custom directory path
            
        Returns:
            True if installation was successful, False otherwise.
        """
        try:
            import json
            import os
            from pathlib import Path
            
            self.logger.info(f"Creating new NeoForge installation: {installation_name}")
            
            # Determine installation directory
            if installation_dir:
                instance_path = Path(installation_dir)
                # Create the directory if it doesn't exist
                instance_path.mkdir(parents=True, exist_ok=True)
            else:
                # Use default .minecraft directory
                instance_path = Path(os.environ['APPDATA']) / ".minecraft"
            
            # Create necessary subdirectories
            subdirs = ['mods', 'config', 'resourcepacks', 'kubejs', 'defaultconfigs', 'versions']
            for subdir in subdirs:
                (instance_path / subdir).mkdir(exist_ok=True)
            
            # Install NeoForge to the instance
            if not self.neoforge_service.install_neoforge_to_instance_path(instance_path):
                self.logger.error("Failed to install NeoForge")
                return False
            
            # Create/update launcher profile
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
            
            # Generate a unique profile ID
            import uuid
            profile_id = str(uuid.uuid4()).replace('-', '')
            
            # Create the new profile
            new_profile = {
                "name": installation_name,
                "type": "custom",
                "created": "2024-01-01T00:00:00.000Z",
                "lastUsed": "2024-01-01T00:00:00.000Z",
                "icon": "Furnace"
            }
            
            # Add gameDir only if using custom directory
            if installation_dir and Path(installation_dir).resolve() != minecraft_dir.resolve():
                new_profile["gameDir"] = str(instance_path)
            
            # Add the profile to the profiles data
            profiles_data["profiles"][profile_id] = new_profile
            
            # Save the updated profiles
            with open(launcher_profiles_path, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2)
            
            # Update config to select the new installation
            self.config.selected_instance = installation_name
            
            self.logger.info(f"Successfully created NeoForge installation: {installation_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create NeoForge installation: {e}")
            return False

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
