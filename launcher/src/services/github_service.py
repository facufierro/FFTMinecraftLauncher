"""GitHub service for handling repository operations."""

import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..models.update_info import UpdateInfo
from ..utils.logging_utils import get_logger
from ..utils.github_utils import get_github_client
from ..constants import NEOFORGE_VERSION, MINECRAFT_VERSION, LAUNCHER_PROFILE_NAME


class GitHubService:
    """Service for interacting with GitHub API."""
    
    # NeoForge configuration - now imported from constants
    NEOFORGE_VERSION = NEOFORGE_VERSION
    MINECRAFT_VERSION = MINECRAFT_VERSION
    PROFILE_NAME = LAUNCHER_PROFILE_NAME
    
    def __init__(self, repo: str, timeout: int = 30):
        """Initialize the GitHub service.
        
        Args:
            repo: Repository in format 'owner/repo'
            timeout: Request timeout in seconds (kept for compatibility)
        """
        self.repo = repo
        self.logger = get_logger()
        self.github_client = get_github_client()
        self.minecraft_dir = Path(os.environ['APPDATA']) / ".minecraft"
    
    def get_latest_release(self) -> Optional[Dict[str, Any]]:
        """Get the latest release information from GitHub.
        
        Returns:
            Dictionary containing release information or None if failed.
        """
        return self.github_client.get_latest_release(self.repo)
    
    def get_releases(self, per_page: int = 10) -> List[Dict[str, Any]]:
        """Get list of releases from GitHub.
        
        Args:
            per_page: Number of releases to fetch per page
            
        Returns:
            List of release dictionaries.
        """
        # This could be implemented in github_utils if needed
        # For now, delegate to get_latest_release
        latest = self.get_latest_release()
        return [latest] if latest else []
    
    def get_repository_info(self) -> Optional[Dict[str, Any]]:
        """Get repository information.
        
        Returns:
            Dictionary containing repository information or None if failed.
        """
        # This could be implemented in github_utils if needed
        # For now, return basic info
        latest = self.get_latest_release()
        if latest:
            return {
                'name': self.repo.split('/')[-1],
                'full_name': self.repo,
                'latest_release': latest
            }
        return None
    
    def download_file(self, url: str, output_path: str) -> bool:
        """Download a file from the given URL.
        
        Args:
            url: URL to download from
            output_path: Local path to save the file
            
        Returns:
            True if download was successful, False otherwise.
        """
        return self.github_client.download_file_from_url(url, Path(output_path))
    
    def create_update_info(self, current_version: Optional[str] = None) -> UpdateInfo:
        """Create an UpdateInfo object with the latest release data.
        
        Args:
            current_version: Current version to compare against
            
        Returns:
            UpdateInfo object with the latest information.
        """
        release_data = self.get_latest_release()
        
        if not release_data:
            return UpdateInfo(
                latest_version="Unknown",
                current_version=current_version,
                updates_available=False
            )
        
        latest_version = release_data.get('tag_name', 'Unknown').lstrip('v')
        updates_available = current_version != latest_version
        
        return UpdateInfo(
            latest_version=latest_version,
            current_version=current_version,
            updates_available=updates_available,
            release_data=release_data
        )
    
    def ensure_neoforge_and_profile(self) -> bool:
        """Ensure NeoForge is installed and launcher profile is configured.
        
        This method checks if NeoForge is installed in .minecraft and if the 
        FFTClient profile exists with the correct version. If not, it installs/updates them.
        
        Returns:
            True if everything is properly configured, False otherwise.
        """
        try:
            self.logger.info("Checking NeoForge installation and launcher profile...")
            
            # Check if NeoForge needs installation/update
            neoforge_status = self._check_neoforge_installation()
            
            # Check if launcher profile needs creation/update
            profile_status = self._check_launcher_profile()
            
            # Install/update NeoForge if needed
            if not neoforge_status['installed'] or not neoforge_status['correct_version']:
                self.logger.info(f"Installing/updating NeoForge {self.NEOFORGE_VERSION}...")
                if not self._install_neoforge():
                    self.logger.error("Failed to install/update NeoForge")
                    return False
                self.logger.info("NeoForge installation/update completed")
            else:
                self.logger.info("NeoForge is already up to date")
            
            # Create/update launcher profile if needed
            if not profile_status['exists'] or not profile_status['correct_version']:
                self.logger.info(f"Creating/updating {self.PROFILE_NAME} profile...")
                if not self._update_launcher_profile():
                    self.logger.error("Failed to create/update launcher profile")
                    return False
                self.logger.info("Launcher profile updated successfully")
            else:
                self.logger.info("Launcher profile is already up to date")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error ensuring NeoForge and profile: {e}")
            return False
    
    def _check_neoforge_installation(self) -> Dict[str, bool]:
        """Check if NeoForge is installed and if it's the correct version.
        
        Returns:
            Dictionary with 'installed' and 'correct_version' status.
        """
        try:
            versions_dir = self.minecraft_dir / "versions"
            if not versions_dir.exists():
                return {'installed': False, 'correct_version': False}
            
            # Look for NeoForge version directory
            neoforge_version_name = f"neoforge-{self.NEOFORGE_VERSION}"
            version_dir = versions_dir / neoforge_version_name
            
            if not version_dir.exists():
                self.logger.info(f"NeoForge {self.NEOFORGE_VERSION} not found in versions directory")
                return {'installed': False, 'correct_version': False}
            
            # Check if the version JSON file exists
            version_json = version_dir / f"{neoforge_version_name}.json"
            if not version_json.exists():
                self.logger.info(f"NeoForge version JSON not found: {version_json}")
                return {'installed': False, 'correct_version': False}
            
            # Verify the version in the JSON
            try:
                with open(version_json, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                
                version_id = version_data.get('id', '')
                if neoforge_version_name in version_id:
                    self.logger.info(f"NeoForge {self.NEOFORGE_VERSION} is correctly installed")
                    return {'installed': True, 'correct_version': True}
                else:
                    self.logger.info(f"NeoForge version mismatch. Expected: {neoforge_version_name}, Found: {version_id}")
                    return {'installed': True, 'correct_version': False}
                    
            except Exception as e:
                self.logger.error(f"Error reading NeoForge version JSON: {e}")
                return {'installed': False, 'correct_version': False}
            
        except Exception as e:
            self.logger.error(f"Error checking NeoForge installation: {e}")
            return {'installed': False, 'correct_version': False}
    
    def _check_launcher_profile(self) -> Dict[str, bool]:
        """Check if the FFTClient launcher profile exists and has correct version.
        
        Returns:
            Dictionary with 'exists' and 'correct_version' status.
        """
        try:
            launcher_profiles_path = self.minecraft_dir / "launcher_profiles.json"
            if not launcher_profiles_path.exists():
                self.logger.info("launcher_profiles.json not found")
                return {'exists': False, 'correct_version': False}
            
            with open(launcher_profiles_path, 'r', encoding='utf-8') as f:
                profiles_data = json.load(f)
            
            profiles = profiles_data.get('profiles', {})
            
            # Look for FFTClient profile by name
            fft_profile = None
            for profile_id, profile_data in profiles.items():
                if profile_data.get('name') == self.PROFILE_NAME:
                    fft_profile = profile_data
                    break
            
            if not fft_profile:
                self.logger.info(f"{self.PROFILE_NAME} profile not found")
                return {'exists': False, 'correct_version': False}
            
            # Check if the profile has the correct version
            expected_version = f"neoforge-{self.NEOFORGE_VERSION}"
            current_version = fft_profile.get('lastVersionId', '')
            
            if current_version == expected_version:
                self.logger.info(f"{self.PROFILE_NAME} profile has correct version: {expected_version}")
                return {'exists': True, 'correct_version': True}
            else:
                self.logger.info(f"{self.PROFILE_NAME} profile version mismatch. Expected: {expected_version}, Current: {current_version}")
                return {'exists': True, 'correct_version': False}
            
        except Exception as e:
            self.logger.error(f"Error checking launcher profile: {e}")
            return {'exists': False, 'correct_version': False}
    
    def _install_neoforge(self) -> bool:
        """Install or update NeoForge to the correct version.
        
        Returns:
            True if installation was successful, False otherwise.
        """
        try:
            # Import NeoForgeService to handle the actual installation
            from .neoforge_service import NeoForgeService
            from ..models.config import LauncherConfig
            
            # Create a minimal config for the NeoForge service
            config = LauncherConfig()
            neoforge_service = NeoForgeService(config)
            
            # Update the NeoForge service to use our version
            neoforge_service.neoforge_version = self.NEOFORGE_VERSION
            neoforge_service.minecraft_version = self.MINECRAFT_VERSION
            
            # Install NeoForge to the .minecraft directory
            return neoforge_service.install_neoforge_to_instance_path(self.minecraft_dir)
            
        except Exception as e:
            self.logger.error(f"Error installing NeoForge: {e}")
            return False
    
    def _update_launcher_profile(self) -> bool:
        """Create or update the FFTClient launcher profile.
        
        Returns:
            True if profile was updated successfully, False otherwise.
        """
        try:
            launcher_profiles_path = self.minecraft_dir / "launcher_profiles.json"
            
            # Load existing profiles or create new structure
            if launcher_profiles_path.exists():
                with open(launcher_profiles_path, 'r', encoding='utf-8') as f:
                    profiles_data = json.load(f)
            else:
                profiles_data = {
                    "profiles": {},
                    "settings": {
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
                    },
                    "version": 4
                }
            
            # Look for existing FFTClient profile
            fft_profile_id = None
            for profile_id, profile_data in profiles_data.get('profiles', {}).items():
                if profile_data.get('name') == self.PROFILE_NAME:
                    fft_profile_id = profile_id
                    break
            
            # Generate new profile ID if needed
            if not fft_profile_id:
                fft_profile_id = str(uuid.uuid4()).replace('-', '')
            
            # Create the current timestamp
            current_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3] + 'Z'
            
            # Create/update the profile
            fft_profile = {
                "created": current_time,
                "gameDir": str(self.minecraft_dir),
                "icon": "Furnace",
                "javaArgs": "-Xmx8G -Xms8G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M",
                "lastUsed": current_time,
                "lastVersionId": f"neoforge-{self.NEOFORGE_VERSION}",
                "name": self.PROFILE_NAME,
                "type": "custom"
            }
            
            # Add the profile to the profiles data
            profiles_data["profiles"][fft_profile_id] = fft_profile
            
            # Save the updated profiles
            with open(launcher_profiles_path, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2)
            
            self.logger.info(f"Successfully updated {self.PROFILE_NAME} profile with version neoforge-{self.NEOFORGE_VERSION}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating launcher profile: {e}")
            return False
    
    def get_neoforge_version(self) -> str:
        """Get the NeoForge version that should be installed.
        
        Returns:
            The NeoForge version string.
        """
        return self.NEOFORGE_VERSION
    
    def get_minecraft_version(self) -> str:
        """Get the Minecraft version that NeoForge is based on.
        
        Returns:
            The Minecraft version string.
        """
        return self.MINECRAFT_VERSION
