"""Centralized GitHub API utilities for all launcher components."""

import requests
import subprocess
import os
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from .logging_utils import get_logger


class GitHubAPIClient:
    """Centralized GitHub API client for all launcher operations."""
    
    def __init__(self, timeout: int = 30):
        """Initialize the GitHub API client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.base_url = "https://api.github.com"
        self.timeout = timeout
        self.logger = get_logger()
        self._token = None
        self._token_checked = False
    
    def _get_github_token(self) -> Optional[str]:
        """Get GitHub token from CLI authentication or environment."""
        if self._token_checked:
            return self._token
        
        self._token_checked = True
        
        # First try environment variable
        token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
        if token:
            self.logger.debug("Using GitHub token from environment variable")
            self._token = token
            return self._token
        
        # Try to get token from GitHub CLI
        try:
            result = subprocess.run(
                ['gh', 'auth', 'token'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                self.logger.debug("Using GitHub token from CLI authentication")
                self._token = result.stdout.strip()
                return self._token
            else:
                self.logger.debug("GitHub CLI not authenticated or not available")
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self.logger.debug(f"Could not get GitHub CLI token: {e}")
        
        return None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'FFTMinecraftLauncher/1.0'
        }
        
        token = self._get_github_token()
        if token:
            headers['Authorization'] = f'token {token}'
        
        return headers
    
    def get_latest_release(self, repo: str) -> Optional[Dict[str, Any]]:
        """Get the latest release from a GitHub repository.
        
        Args:
            repo: Repository in format 'owner/repo'
            
        Returns:
            Release data dictionary or None if failed
        """
        try:
            url = f"{self.base_url}/repos/{repo}/releases/latest"
            self.logger.debug(f"Fetching release from: {url}")
            
            headers = self._get_headers()
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch release from {repo}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching release: {e}")
            return None
    
    def get_latest_version(self, repo: str) -> str:
        """Get the latest version tag from a repository.
        
        Args:
            repo: Repository in format 'owner/repo'
            
        Returns:
            Version string (without 'v' prefix) or "0.0.0" if failed
        """
        release_data = self.get_latest_release(repo)
        if release_data:
            version = release_data.get('tag_name', '').lstrip('v')
            if version:
                return version
        
        self.logger.warning(f"Could not get version for {repo}")
        return "0.0.0"
    
    def download_file_from_release(self, repo: str, output_path: Path, 
                                 asset_filter: Optional[Callable[[str], bool]] = None,
                                 progress_callback: Optional[Callable[[str, Optional[float]], None]] = None) -> bool:
        """Download a file from the latest release.
        
        Args:
            repo: Repository in format 'owner/repo'
            output_path: Where to save the downloaded file
            asset_filter: Function to filter assets by name, returns True to select
            progress_callback: Optional callback for progress updates (message, progress)
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            release_data = self.get_latest_release(repo)
            if not release_data:
                return False
            
            # Find the asset to download
            assets = release_data.get('assets', [])
            if not assets:
                self.logger.error(f"No assets found in latest release of {repo}")
                return False
            
            # Apply filter if provided, otherwise take first asset
            selected_asset = None
            if asset_filter:
                for asset in assets:
                    if asset_filter(asset.get('name', '')):
                        selected_asset = asset
                        break
            else:
                selected_asset = assets[0]
            
            if not selected_asset:
                self.logger.error(f"No suitable asset found in {repo}")
                return False
            
            download_url = selected_asset.get('browser_download_url')
            if not download_url:
                self.logger.error(f"No download URL found for asset")
                return False
            
            return self.download_file_from_url(download_url, output_path, progress_callback)
            
        except Exception as e:
            self.logger.error(f"Error downloading from {repo}: {e}")
            return False
    
    def download_file_from_url(self, url: str, output_path: Path,
                              progress_callback: Optional[Callable[[str, Optional[float]], None]] = None) -> bool:
        """Download a file from a direct URL.
        
        Args:
            url: Direct download URL
            output_path: Where to save the file
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Downloading from: {url}")
            
            if progress_callback:
                progress_callback("Starting download...", 0.0)
            
            headers = self._get_headers()
            response = requests.get(url, headers=headers, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            last_progress_update = 0
            progress_update_threshold = 0.05  # Update every 5%
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0 and progress_callback:
                            progress = downloaded / total_size
                            # Only update progress every 5% to avoid spam
                            if progress - last_progress_update >= progress_update_threshold or progress >= 1.0:
                                progress_callback(
                                    f"Downloading... {downloaded // 1024}KB / {total_size // 1024}KB",
                                    progress
                                )
                                last_progress_update = progress
            
            if progress_callback:
                progress_callback("Download completed", 1.0)
            
            self.logger.info(f"Download completed: {output_path}")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Download failed: {e}")
            if progress_callback:
                progress_callback("Download failed", None)
            return False
        except Exception as e:
            self.logger.error(f"Unexpected download error: {e}")
            if progress_callback:
                progress_callback("Download error", None)
            return False
    
    def find_asset_by_pattern(self, repo: str, patterns: list[str]) -> Optional[str]:
        """Find an asset download URL by matching patterns.
        
        Args:
            repo: Repository in format 'owner/repo'
            patterns: List of patterns to match against asset names
            
        Returns:
            Download URL of first matching asset or None
        """
        release_data = self.get_latest_release(repo)
        if not release_data:
            return None
        
        assets = release_data.get('assets', [])
        for asset in assets:
            asset_name = asset.get('name', '').lower()
            for pattern in patterns:
                if pattern.lower() in asset_name:
                    return asset.get('browser_download_url')
        
        return None


# Global GitHub client instance
_github_client: Optional[GitHubAPIClient] = None


def get_github_client() -> GitHubAPIClient:
    """Get the global GitHub API client instance."""
    global _github_client
    if _github_client is None:
        _github_client = GitHubAPIClient()
    return _github_client


# Convenience functions for common operations
def get_launcher_version() -> str:
    """Get the latest launcher version from GitHub."""
    return get_github_client().get_latest_version("facufierro/FFTMinecraftLauncher")


def get_client_version() -> str:
    """Get the latest client/modpack version from GitHub."""
    return get_github_client().get_latest_version("facufierro/FFTClientMinecraft1211")


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
    """Check if latest version is newer than current version."""
    return compare_versions(latest, current) > 0
