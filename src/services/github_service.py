"""GitHub service for handling repository operations."""

from pathlib import Path
from typing import Dict, Any, Optional, List
from ..models.update_info import UpdateInfo
from ..utils.logger import get_logger
from ..utils.github_utils import get_github_client


class GitHubService:
    """Service for interacting with GitHub API."""
    
    def __init__(self, repo: str, timeout: int = 30):
        """Initialize the GitHub service.
        
        Args:
            repo: Repository in format 'owner/repo'
            timeout: Request timeout in seconds (kept for compatibility)
        """
        self.repo = repo
        self.logger = get_logger()
        self.github_client = get_github_client()
    
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
