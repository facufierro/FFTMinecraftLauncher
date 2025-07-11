"""NeoForge service for managing NeoForge installations in Minecraft launcher instances."""

import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional
from ..models.config import LauncherConfig
from ..utils.logging_utils import get_logger

# Windows-specific constants for hiding console windows
if os.name == 'nt':
    try:
        # These constants may not be available on all systems
        CREATE_NO_WINDOW = 0x08000000
        subprocess.CREATE_NO_WINDOW = CREATE_NO_WINDOW
    except AttributeError:
        # Fallback if constant is not available
        subprocess.CREATE_NO_WINDOW = 0x08000000


class NeoForgeService:
    """Service for managing NeoForge installations in Minecraft launcher instances."""
    
    def __init__(self, config: LauncherConfig):
        """Initialize the NeoForge service.
        
        Args:
            config: Launcher configuration
        """
        self.config = config
        self.logger = get_logger()
        self.minecraft_version = "1.21.1"  # Base version - NeoForge 21.1.190 supports 1.21.1+
        self.neoforge_version = "21.1.190"  # Latest stable NeoForge for 1.21.x
        
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
    
    def install_neoforge_to_instance_path(self, instance_path: Path) -> bool:
        """Install NeoForge to a specific instance path.
        
        Args:
            instance_path: Path to the instance directory
            
        Returns:
            True if installation was successful, False otherwise.
        """
        try:
            self.logger.info(f"Installing NeoForge {self.neoforge_version} to path: {instance_path}")
            
            # Clean up old NeoForge installations first
            self._cleanup_old_neoforge_installations(instance_path)
            
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
                "--installClient",
                "--targetDir", str(instance_path)
            ]
            
            # Configure process creation flags to hide console on Windows
            creation_flags = 0
            if os.name == 'nt':  # Windows
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            # Set MINECRAFT_LAUNCHER_HOME environment variable for the installer
            env = os.environ.copy()
            env['MINECRAFT_LAUNCHER_HOME'] = str(instance_path)
            
            result = subprocess.run(
                install_cmd, 
                capture_output=True, 
                text=True, 
                cwd=str(instance_path),
                env=env,
                creationflags=creation_flags
            )
            
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
                
                # Configure default resource pack if it exists
                resourcepacks_dir = instance_path / "resourcepacks"
                if resourcepacks_dir.exists():
                    for pack_file in resourcepacks_dir.iterdir():
                        if pack_file.name.startswith("fft-resourcepack"):
                            pack_name = pack_file.stem if pack_file.suffix == '.zip' else pack_file.name
                            self.configure_default_resource_pack(instance_path, pack_name)
                            break
                
                return True
            else:
                self.logger.error("NeoForge installation verification failed")
                return False
            
        except Exception as e:
            self.logger.error(f"Failed to install NeoForge to path: {e}")
            return False

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
            
            # Clean up old NeoForge installations first
            self._cleanup_old_neoforge_installations(instance_path)
            
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
                "--installClient",
                "--targetDir", str(instance_path)
            ]
            
            # Configure process creation flags to hide console on Windows
            creation_flags = 0
            if os.name == 'nt':  # Windows
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            # Set MINECRAFT_LAUNCHER_HOME environment variable for the installer
            env = os.environ.copy()
            env['MINECRAFT_LAUNCHER_HOME'] = str(instance_path)
            
            result = subprocess.run(
                install_cmd, 
                capture_output=True, 
                text=True, 
                cwd=str(instance_path),
                env=env,
                creationflags=creation_flags
            )
            
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
                
                # Configure default resource pack if it exists
                resourcepacks_dir = instance_path / "resourcepacks"
                if resourcepacks_dir.exists():
                    for pack_file in resourcepacks_dir.iterdir():
                        if pack_file.name.startswith("fft-resourcepack"):
                            pack_name = pack_file.stem if pack_file.suffix == '.zip' else pack_file.name
                            self.configure_default_resource_pack(instance_path, pack_name)
                            break
                
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
            
            # Always download fresh installer to ensure we have the latest
            if installer_path.exists():
                self.logger.info(f"Removing existing installer: {installer_path}")
                installer_path.unlink()
            
            self.logger.info(f"Downloading NeoForge {self.neoforge_version} installer from {installer_url}")
            urllib.request.urlretrieve(installer_url, installer_path)
            
            if installer_path.exists() and installer_path.stat().st_size > 0:
                self.logger.info(f"Successfully downloaded installer: {installer_path}")
                return installer_path
            else:
                self.logger.error("Downloaded installer is empty or missing")
                return None
            
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
            self.logger.debug(f"Versions directory not found: {versions_dir}")
            return False
        
        # List all directories in versions to see what was actually installed
        try:
            version_dirs = [d.name for d in versions_dir.iterdir() if d.is_dir()]
            self.logger.info(f"Found version directories: {version_dirs}")
        except Exception as e:
            self.logger.warning(f"Could not list version directories: {e}")
            version_dirs = []
        
        # Look for NeoForge version directory - try multiple formats
        possible_version_names = [
            f"neoforge-{self.neoforge_version}",
            f"{self.minecraft_version}-neoforge-{self.neoforge_version}",
            f"{self.minecraft_version}-{self.neoforge_version}",
            f"neoforge-{self.minecraft_version}-{self.neoforge_version}"
        ]
        
        for version_name in possible_version_names:
            version_dir = versions_dir / version_name
            if version_dir.exists():
                version_json = version_dir / f"{version_name}.json"
                if version_json.exists():
                    self.logger.info(f"Found NeoForge installation: {version_name}")
                    return True
                else:
                    self.logger.debug(f"Version directory exists but no JSON: {version_dir}")
        
        # Check if any directory contains neoforge and our version
        for version_dir_name in version_dirs:
            if "neoforge" in version_dir_name.lower() and self.neoforge_version in version_dir_name:
                version_dir = versions_dir / version_dir_name
                version_json = version_dir / f"{version_dir_name}.json"
                if version_json.exists():
                    self.logger.info(f"Found NeoForge installation (pattern match): {version_dir_name}")
                    return True
        
        self.logger.error(f"NeoForge {self.neoforge_version} installation not found in {versions_dir}")
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
    
    def enable_resource_pack_for_instance(self, instance_name: str, resource_pack_name: str = "fft-resourcepack") -> bool:
        """Enable a resource pack for a specific instance.
        
        Args:
            instance_name: Name of the instance
            resource_pack_name: Name of the resource pack to enable
            
        Returns:
            True if configuration was successful, False otherwise.
        """
        instance_path = self._find_instance_path(instance_name)
        if not instance_path:
            self.logger.error(f"Instance '{instance_name}' not found")
            return False
        
        return self.configure_default_resource_pack(instance_path, resource_pack_name)
    
    def configure_default_resource_pack(self, instance_path: Path, resource_pack_name: str = "fft-resourcepack") -> bool:
        """Configure default resource pack for an instance without overriding player settings.
        
        Args:
            instance_path: Path to the instance directory
            resource_pack_name: Name of the resource pack to enable
            
        Returns:
            True if configuration was successful, False otherwise.
        """
        try:
            options_file = instance_path / "options.txt"
            resource_pack_file = f"file/{resource_pack_name}"
            
            # If options.txt doesn't exist, create it with minimal settings
            if not options_file.exists():
                self.logger.info(f"Creating new options.txt with default resource pack: {resource_pack_name}")
                options_content = f"resourcePacks:[\"vanilla\",\"{resource_pack_file}\"]\n"
                options_content += f"incompatibleResourcePacks:[]\n"
                
                with open(options_file, 'w', encoding='utf-8') as f:
                    f.write(options_content)
                return True
            
            # Read existing options.txt
            with open(options_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check if resource pack is already enabled
            for line in lines:
                if line.startswith('resourcePacks:') and resource_pack_file in line:
                    self.logger.info(f"Resource pack {resource_pack_name} already enabled in options.txt")
                    return True
            
            # Modify existing options.txt to add the resource pack
            modified_lines = []
            resource_pack_added = False
            
            for line in lines:
                if line.startswith('resourcePacks:'):
                    # Parse existing resource packs
                    if line.strip().endswith('[]'):
                        # Empty resource packs list
                        new_line = f'resourcePacks:[\"vanilla\",\"{resource_pack_file}\"]\n'
                    elif '\"vanilla\"' in line and resource_pack_file not in line:
                        # Add our pack after vanilla
                        new_line = line.rstrip()
                        if new_line.endswith(']'):
                            new_line = new_line[:-1] + f',\"{resource_pack_file}\"]\n'
                        else:
                            new_line = line.rstrip() + f',\"{resource_pack_file}\"]\n'
                    else:
                        new_line = line
                    
                    modified_lines.append(new_line)
                    resource_pack_added = True
                elif line.startswith('incompatibleResourcePacks:') and resource_pack_added:
                    # Ensure our pack is not in incompatible list
                    if resource_pack_file in line:
                        # Remove our pack from incompatible list
                        new_line = line.replace(f',\"{resource_pack_file}\"', '').replace(f'\"{resource_pack_file}\",', '').replace(f'\"{resource_pack_file}\"', '')
                        if new_line.strip().endswith('[,]') or new_line.strip().endswith('[, ]'):
                            new_line = new_line.replace('[,]', '[]').replace('[, ]', '[]')
                        modified_lines.append(new_line)
                    else:
                        modified_lines.append(line)
                else:
                    modified_lines.append(line)
            
            # If resourcePacks line wasn't found, add it
            if not resource_pack_added:
                modified_lines.append(f'resourcePacks:[\"vanilla\",\"{resource_pack_file}\"]\n')
                modified_lines.append(f'incompatibleResourcePacks:[]\n')
            
            # Write back the modified options.txt
            with open(options_file, 'w', encoding='utf-8') as f:
                f.writelines(modified_lines)
            
            self.logger.info(f"Successfully enabled resource pack {resource_pack_name} in options.txt")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to configure default resource pack: {e}")
            return False
    
    def _cleanup_old_neoforge_installations(self, instance_path: Path) -> None:
        """Clean up old NeoForge installations to avoid conflicts.
        
        Args:
            instance_path: Path to the instance directory
        """
        try:
            versions_dir = instance_path / "versions"
            if not versions_dir.exists():
                return
            
            # Find and remove old NeoForge versions
            for version_dir in versions_dir.iterdir():
                if version_dir.is_dir() and "neoforge" in version_dir.name.lower():
                    # Don't remove if it's already the version we want
                    if self.neoforge_version in version_dir.name:
                        continue
                    
                    self.logger.info(f"Removing old NeoForge installation: {version_dir.name}")
                    try:
                        shutil.rmtree(version_dir)
                    except Exception as e:
                        self.logger.warning(f"Failed to remove old NeoForge version {version_dir.name}: {e}")
                        
            # Also clean up launcher profiles that might reference old versions
            launcher_profiles = instance_path / "launcher_profiles.json"
            if launcher_profiles.exists():
                try:
                    with open(launcher_profiles, 'r', encoding='utf-8') as f:
                        profiles = json.load(f)
                    
                    modified = False
                    for profile_id, profile_data in profiles.get("profiles", {}).items():
                        if "lastVersionId" in profile_data and "neoforge" in profile_data["lastVersionId"].lower():
                            if self.neoforge_version not in profile_data["lastVersionId"]:
                                self.logger.info(f"Updating profile {profile_id} to use latest NeoForge")
                                # Will be updated after successful installation
                                modified = True
                    
                except Exception as e:
                    self.logger.warning(f"Failed to clean up launcher profiles: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Failed to cleanup old NeoForge installations: {e}")
