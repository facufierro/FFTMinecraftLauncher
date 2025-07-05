"""GitHub service for handling repository operations."""

import requests
from typing import Dict, Any, Optional, List
from ..models.update_info import UpdateInfo
from ..utils.logger import get_logger


class GitHubService:
    """Service for interacting with GitHub API."""
    
    def __init__(self, repo: str, timeout: int = 30):
        """Initialize the GitHub service.
        
        Args:
            repo: Repository in format 'owner/repo'
            timeout: Request timeout in seconds
        """
        self.repo = repo
        self.timeout = timeout
        self.base_url = "https://api.github.com"
        self.logger = get_logger()
    
    def get_latest_release(self) -> Optional[Dict[str, Any]]:
        """Get the latest release information from GitHub.
        
        Returns:
            Dictionary containing release information or None if failed.
        """
        try:
            url = f"{self.base_url}/repos/{self.repo}/releases/latest"
            self.logger.info(f"Fetching latest release from: {url}")
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            release_data = response.json()
            self.logger.info(f"Found release: {release_data.get('tag_name', 'Unknown')}")
            
            return release_data
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch release information: {e}")
            return None
    
    def get_releases(self, per_page: int = 10) -> List[Dict[str, Any]]:
        """Get list of releases from GitHub.
        
        Args:
            per_page: Number of releases to fetch per page
            
        Returns:
            List of release dictionaries.
        """
        try:
            url = f"{self.base_url}/repos/{self.repo}/releases"
            params = {'per_page': per_page}
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch releases: {e}")
            return []
    
    def get_repository_info(self) -> Optional[Dict[str, Any]]:
        """Get repository information.
        
        Returns:
            Dictionary containing repository information or None if failed.
        """
        try:
            url = f"{self.base_url}/repos/{self.repo}"
            
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch repository information: {e}")
            return None
    
    def download_file(self, url: str, output_path: str) -> bool:
        """Download a file from the given URL.
        
        Args:
            url: URL to download from
            output_path: Local path to save the file
            
        Returns:
            True if download was successful, False otherwise.
        """
        try:
            self.logger.info(f"Downloading from: {url}")
            
            response = requests.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.logger.info(f"Download completed: {output_path}")
            return True
            
        except (requests.RequestException, IOError) as e:
            self.logger.error(f"Download failed: {e}")
            return False
    
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
        
        latest_version = release_data.get('tag_name', 'Unknown')
        updates_available = current_version != latest_version
        
        return UpdateInfo(
            latest_version=latest_version,
            current_version=current_version,
            updates_available=updates_available,
            release_data=release_data
        )
