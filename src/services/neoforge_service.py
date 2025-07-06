"""NeoForge service for managing NeoForge installations in Minecraft launcher instances."""

import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional
from ..models.config import LauncherConfig
from ..utils.logger import get_logger


class NeoForgeService:
    """Service for managing NeoForge installations in Minecraft launcher instances."""
    
    def __init__(self, config: LauncherConfig):
        """Initialize the NeoForge service.
        
        Args:
            config: Launcher configuration
        """
        self.config = config
        self.logger = get_logger()
        self.minecraft_version = "1.21.1"  # Base version - NeoForge 21.1.186 supports 1.21.1+
        self.neoforge_version = "21.1.186"  # Latest stable NeoForge for 1.21.x
        
    def get_available_instances(self) -> List[str]:
        """Get list of available Minecraft launcher instances.
        
        Returns:
            List of instance names.
        """
        instances = []
        minecraft_dir = Path(os.environ['APPDATA']) / ".minecraft"
        
        # First, add the default Minecraft installation as an option
        if minecraft_dir.exists():
            instances.append("Default (.minecraft)")
        
        # Check for official launcher profiles
        launcher_profiles = minecraft_dir / "launcher_profiles.json"
        if launcher_profiles.exists():
            try:
                with open(launcher_profiles, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                
                for profile_id, profile_data in profiles.get("profiles", {}).items():
                    profile_name = profile_data.get("name", profile_id)
                    
                    # Handle profiles without names or with default names - show as "last release"
                    if not profile_name or profile_name.lower() in ["default", ""]:
                        profile_name = "last release"
                    
                    # Add each profile only once with a clear indicator
                    if "gameDir" in profile_data:
                        game_dir = Path(profile_data["gameDir"])
                        # Check if it uses a custom directory
                        if game_dir.resolve() != minecraft_dir.resolve():
                            instances.append(profile_name)  # Just use the profile name directly
                        else:
                            instances.append(profile_name)  # Also just use the profile name
                    else:
                        instances.append(profile_name)  # Profile uses default .minecraft
                        
            except Exception as e:
                self.logger.warning(f"Failed to read launcher profiles: {e}")
        
        # Check for MultiMC/PolyMC/PrismLauncher style instances
        common_launcher_dirs = [
            Path(os.environ['APPDATA']) / "PrismLauncher" / "instances",
            Path(os.environ['APPDATA']) / "PolyMC" / "instances", 
            Path(os.environ['APPDATA']) / "MultiMC" / "instances",
            minecraft_dir / "instances",  # Some launchers put instances here
        ]
        
        for launcher_dir in common_launcher_dirs:
            if launcher_dir.exists():
                for instance_dir in launcher_dir.iterdir():
                    if instance_dir.is_dir():
                        # Check if it's a valid instance
                        minecraft_subdir = None
                        if (instance_dir / ".minecraft").exists():
                            minecraft_subdir = instance_dir / ".minecraft"
                        elif (instance_dir / "minecraft").exists():
                            minecraft_subdir = instance_dir / "minecraft"
                        
                        if minecraft_subdir:
                            launcher_name = launcher_dir.parent.name
                            instance_name = f"{instance_dir.name} ({launcher_name})"
                            if instance_name not in instances:
                                instances.append(instance_name)
        
        return sorted(instances)
    
    def install_neoforge_to_instance(self, instance_name: str) -> bool:
        """Install NeoForge to the specified Minecraft launcher instance.
        
        Args:
            instance_name: Name of the instance to install NeoForge to
            
        Returns:
            True if installation was successful, False otherwise.
        """
        try:
            self.logger.info(f"Installing NeoForge {self.neoforge_version} to instance: {instance_name}")
            
            # Find the instance directory
            instance_path = self._find_instance_path(instance_name)
            if not instance_path:
                self.logger.error(f"Instance '{instance_name}' not found")
                return False
            
            # Download NeoForge installer
            installer_path = self._download_neoforge_installer()
            if not installer_path:
                return False
            
            # Find Java executable
            java_exe = self._find_java_executable()
            if not java_exe:
                self.logger.error("Java executable not found")
                return False
            
            # Run NeoForge installer on the instance
            self.logger.info("Running NeoForge installer...")
            install_cmd = [
                java_exe,
                "-jar", str(installer_path),
                "--installClient", str(instance_path)
            ]
            
            result = subprocess.run(install_cmd, capture_output=True, text=True, cwd=str(instance_path))
            
            if result.stdout:
                self.logger.info(f"NeoForge installer stdout: {result.stdout}")
            if result.stderr:
                self.logger.info(f"NeoForge installer stderr: {result.stderr}")
            
            if result.returncode != 0:
                self.logger.error(f"NeoForge installation failed with return code {result.returncode}")
                return False
            
            # Verify installation
            if self._verify_neoforge_installation(instance_path):
                self.logger.info("NeoForge installation completed successfully")
                return True
            else:
                self.logger.error("NeoForge installation verification failed")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to install NeoForge: {e}")
            return False
    
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
        
        # Handle launcher profiles (now using direct profile names)
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
            except Exception as e:
                self.logger.warning(f"Failed to read launcher profiles: {e}")
        
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
        
        self.logger.warning(f"Instance path not found for: {instance_name}")
        return None
    
    def _download_neoforge_installer(self) -> Optional[Path]:
        """Download the NeoForge installer.
        
        Returns:
            Path to the downloaded installer, or None if download failed.
        """
        try:
            temp_dir = Path.cwd() / "temp"
            temp_dir.mkdir(exist_ok=True)
            
            installer_url = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{self.neoforge_version}/neoforge-{self.neoforge_version}-installer.jar"
            installer_path = temp_dir / f"neoforge-{self.neoforge_version}-installer.jar"
            
            if not installer_path.exists():
                self.logger.info(f"Downloading NeoForge {self.neoforge_version} installer...")
                urllib.request.urlretrieve(installer_url, installer_path)
            
            return installer_path
            
        except Exception as e:
            self.logger.error(f"Failed to download NeoForge installer: {e}")
            return None
    
    def _find_java_executable(self) -> Optional[str]:
        """Find Java executable on the system.
        
        Returns:
            Path to Java executable, or None if not found.
        """
        # Check system Java first
        java_candidates = ["java", "javaw"]
        
        # Add JAVA_HOME if available
        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            java_candidates.extend([
                os.path.join(java_home, "bin", "java.exe"),
                os.path.join(java_home, "bin", "java"),
            ])
        
        # Add common Java installation directories on Windows
        program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
        program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
        
        for base_path in [program_files, program_files_x86]:
            java_base = os.path.join(base_path, "Java")
            if os.path.exists(java_base):
                try:
                    for java_dir in sorted(os.listdir(java_base), reverse=True):
                        if "jdk" in java_dir.lower() or "jre" in java_dir.lower():
                            java_candidates.append(os.path.join(java_base, java_dir, "bin", "java.exe"))
                except:
                    continue
        
        # Test each candidate
        for java_path in java_candidates:
            try:
                result = subprocess.run([java_path, "-version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.logger.info(f"Found Java executable: {java_path}")
                    return java_path
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                continue
        
        return None
    
    def _verify_neoforge_installation(self, instance_path: Path) -> bool:
        """Verify that NeoForge was installed correctly.
        
        Args:
            instance_path: Path to the instance directory
            
        Returns:
            True if installation is verified, False otherwise.
        """
        # Check for NeoForge version JSON
        versions_dir = instance_path / "versions"
        if not versions_dir.exists():
            return False
        
        # Look for NeoForge version directory
        neoforge_version_name = f"neoforge-{self.neoforge_version}"
        neoforge_version_dir = versions_dir / neoforge_version_name
        
        if neoforge_version_dir.exists():
            version_json = neoforge_version_dir / f"{neoforge_version_name}.json"
            if version_json.exists():
                return True
        
        # Also check for combined version names
        combined_version_name = f"{self.minecraft_version}-{self.neoforge_version}"
        combined_version_dir = versions_dir / combined_version_name
        
        if combined_version_dir.exists():
            version_json = combined_version_dir / f"{combined_version_name}.json"
            if version_json.exists():
                return True
        
        return False
    
    def is_neoforge_installed(self, instance_name: str) -> bool:
        """Check if NeoForge is installed in the specified instance.
        
        Args:
            instance_name: Name of the instance to check
            
        Returns:
            True if NeoForge is installed, False otherwise.
        """
        instance_path = self._find_instance_path(instance_name)
        if not instance_path:
            return False
        
        return self._verify_neoforge_installation(instance_path)
