"""Launcher version checking service."""

from typing import Optional, Tuple
from ..utils.logging_utils import get_logger
from ..utils.github_utils import get_github_client
from ..models.config import LauncherConfig


class LauncherVersionService:
    """Service for checking launcher version against GitHub releases."""
    
    def __init__(self):
        """Initialize the launcher version service."""
        self.logger = get_logger()
        self.github_client = get_github_client()
        self.launcher_repo = "facufierro/FFTMinecraftLauncher"
    
    def get_current_launcher_version(self) -> str:
        """Get the current launcher version from config file or default."""
        # Try to read from launcher_config.json file first
        try:
            from pathlib import Path
            import sys
            import json
            
            # Try multiple locations for launcher_config.json
            possible_locations = []
            
            if getattr(sys, 'frozen', False):
                # Running as executable - look relative to exe
                exe_dir = Path(sys.executable).parent
                possible_locations.append(exe_dir / "launcher_config.json")
                possible_locations.append(exe_dir.parent / "launcher_config.json")
                possible_locations.append(exe_dir.parent / "launcher" / "launcher_config.json")
            else:
                # Running as script - look relative to project root
                script_dir = Path(__file__).parent.parent.parent.parent
                possible_locations.append(script_dir / "launcher" / "launcher_config.json")
                possible_locations.append(script_dir / "launcher_config.json")
            
            for config_file in possible_locations:
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        version = config_data.get('launcher_version')
                        if version:
                            self.logger.info(f"Found launcher version in config at {config_file}: {version}")
                            return version
            
            self.logger.warning("No launcher_version found in config files, using default")
            
        except Exception as e:
            self.logger.error(f"Error reading launcher version from config: {e}")
        
        # Fallback to default version (should match the build spec)
        default_version = "2.0.0"
        return default_version
    
    def get_latest_launcher_version(self) -> Optional[str]:
        """Get the latest launcher version from GitHub releases."""
        try:
            release_data = self.github_client.get_latest_release(self.launcher_repo)
            if release_data:
                version = release_data.get('tag_name', '').lstrip('v')
                self.logger.info(f"Latest launcher version from GitHub: {version}")
                return version
        except Exception as e:
            self.logger.error(f"Failed to fetch latest launcher version: {e}")
        
        return None
    
    def check_for_launcher_update(self, config: LauncherConfig) -> Tuple[bool, Optional[str], Optional[str]]:
        """Check if launcher update is available.
        
        Args:
            config: Launcher configuration
            
        Returns:
            Tuple of (update_available, current_version, latest_version)
        """
        try:
            # Get current version (prefer from file, then config, then default)
            current_version = self.get_current_launcher_version()
            
            # Update config if it's different or not set
            if not config.launcher_version or config.launcher_version != current_version:
                config.launcher_version = current_version
                self.logger.info(f"Updated config launcher version to: {current_version}")
            
            # Get latest version from GitHub
            latest_version = self.get_latest_launcher_version()
            
            if not latest_version:
                self.logger.warning("Could not fetch latest launcher version")
                return False, current_version, None
            
            # Compare versions
            update_available = self._is_newer_version(latest_version, current_version)
            
            self.logger.info(f"Version check: current={current_version}, latest={latest_version}, update_available={update_available}")
            
            return update_available, current_version, latest_version
            
        except Exception as e:
            self.logger.error(f"Error checking for launcher update: {e}")
            return False, None, None
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings to determine if latest is newer than current.
        
        Args:
            latest: Latest version string
            current: Current version string
            
        Returns:
            True if latest is newer than current
        """
        try:
            # Clean version strings (remove 'v' prefix if present)
            latest_clean = latest.lstrip('v')
            current_clean = current.lstrip('v')
            
            # Split into components
            latest_parts = [int(x) for x in latest_clean.split('.')]
            current_parts = [int(x) for x in current_clean.split('.')]
            
            # Pad shorter version with zeros
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            # Compare component by component
            for latest_part, current_part in zip(latest_parts, current_parts):
                if latest_part > current_part:
                    return True
                elif latest_part < current_part:
                    return False
            
            # Versions are equal
            return False
            
        except (ValueError, AttributeError) as e:
            self.logger.error(f"Error comparing versions {latest} and {current}: {e}")
            # If we can't parse versions, assume no update needed
            return False
