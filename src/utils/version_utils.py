"""Version utilities for dynamic version management."""

import json
import sys
from pathlib import Path
from typing import Optional
from .logger import get_logger


def get_launcher_version() -> str:
    """Get the current launcher application version.
    
    This reads from version.json in the launcher directory, which is dynamically
    generated during the build process.
    
    Returns:
        Version string (e.g., "1.0.16") or "0.0.0" if not found.
    """
    logger = get_logger()
    
    try:
        # Get the directory where the launcher executable is located
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            launcher_dir = Path(sys.executable).parent
        else:
            # Running from source - look for version.json in project root
            launcher_dir = Path(__file__).parent.parent.parent
        
        version_file = launcher_dir / "version.json"
        
        if not version_file.exists():
            logger.warning(f"Version file not found at {version_file}")
            return "0.0.0"
        
        # Check if file is empty first
        if version_file.stat().st_size == 0:
            logger.warning("Version file is empty")
            return "0.0.0"
        
        with open(version_file, 'r', encoding='utf-8-sig') as f:
            content = f.read().strip()
            if not content:
                logger.warning("Version file contains no content")
                return "0.0.0"
            
            data = json.loads(content)
            version = data.get('version', '0.0.0')
            
            # Handle the case where version is "dynamic" (development file)
            if version == "dynamic":
                logger.warning("Found development version file with 'dynamic' version")
                return "0.0.0"
            
            return version
            
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in version file: {e}")
        return "0.0.0"
    except Exception as e:
        logger.error(f"Error reading launcher version: {e}")
        return "0.0.0"


def get_client_version() -> Optional[str]:
    """Get the current client/modpack version from GitHub API.
    
    This checks the latest release of the FFTClientMinecraft1211 repository
    to get the current modpack version.
    
    Returns:
        Version string (e.g., "1.1.4") or None if unable to fetch.
    """
    logger = get_logger()
    
    try:
        import requests
        
        # GitHub repository for client content
        client_repo = "facufierro/FFTClientMinecraft1211"
        url = f"https://api.github.com/repos/{client_repo}/releases/latest"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        release_data = response.json()
        version = release_data.get('tag_name', '').lstrip('v')
        
        if version:
            logger.info(f"Current client version from GitHub: {version}")
            return version
        else:
            logger.warning("No version tag found in latest release")
            return None
            
    except requests.RequestException as e:
        logger.error(f"Failed to fetch client version from GitHub: {e}")
        return None
    except Exception as e:
        logger.error(f"Error getting client version: {e}")
        return None


def get_cached_client_version() -> str:
    """Get cached client version with fallback.
    
    Returns the last known client version or a default if unable to fetch.
    This is useful when network is unavailable.
    
    Returns:
        Version string with fallback to "1.1.4".
    """
    version = get_client_version()
    if version:
        return version
    
    # Fallback to a reasonable default
    logger = get_logger()
    logger.warning("Using fallback client version")
    return "1.1.4"


def compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings.
    
    Args:
        version1: First version string
        version2: Second version string
    
    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2
    """
    try:
        # Parse version strings as semantic versioning (e.g., 1.2.3)
        v1_parts = [int(x) for x in version1.strip().lstrip('v').split('.')]
        v2_parts = [int(x) for x in version2.strip().lstrip('v').split('.')]
        
        # Pad with zeros to make same length
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        if v1_parts < v2_parts:
            return -1
        elif v1_parts > v2_parts:
            return 1
        else:
            return 0
            
    except (ValueError, AttributeError):
        # Fallback to string comparison if version parsing fails
        if version1 < version2:
            return -1
        elif version1 > version2:
            return 1
        else:
            return 0


def is_newer_version(latest: str, current: str) -> bool:
    """Check if latest version is newer than current version.
    
    Args:
        latest: Latest version string
        current: Current version string
        
    Returns:
        True if latest is newer than current.
    """
    return compare_versions(latest, current) > 0
