"""Version utilities for dynamic version management."""

from .github_utils import get_github_client, compare_versions, is_newer_version
from .logger import get_logger


def get_launcher_version() -> str:
    """Get the current launcher application version from GitHub releases."""
    return get_github_client().get_latest_version("facufierro/FFTMinecraftLauncher")


def get_client_version() -> str:
    """Get the current client/modpack version from GitHub API."""
    return get_github_client().get_latest_version("facufierro/FFTClientMinecraft1211")


def get_cached_client_version() -> str:
    """Get cached client version with fallback."""
    version = get_client_version()
    if version and version != "0.0.0":
        return version
    
    # Fallback to a reasonable default
    logger = get_logger()
    logger.warning("Using fallback client version")
    return "1.1.4"


# Re-export comparison functions from github_utils for backward compatibility
__all__ = [
    'get_launcher_version',
    'get_client_version', 
    'get_cached_client_version',
    'compare_versions',
    'is_newer_version'
]
