"""Update information model for the FFT Minecraft Launcher."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class UpdateInfo:
    """Information about available updates."""
    
    # Version information
    latest_version: str
    current_version: Optional[str] = None
    
    # Update status
    updates_available: bool = False
    folders_to_update: Optional[List[str]] = None
    
    # Release data
    release_data: Optional[Dict[str, Any]] = None
    download_url: Optional[str] = None
    
    # Metadata
    check_timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.folders_to_update is None:
            self.folders_to_update = []
            
        if self.check_timestamp is None:
            self.check_timestamp = datetime.now()
    
    @property
    def is_new_version_available(self) -> bool:
        """Check if a new version is available."""
        if not self.current_version or not self.latest_version:
            return True
        return self.current_version != self.latest_version
    
    @property
    def version_info_text(self) -> str:
        """Get formatted version information text."""
        if self.updates_available:
            return f"New version available: {self.latest_version}"
        return f"Up to date (Version: {self.latest_version})"
    
    def get_download_url(self) -> Optional[str]:
        """Get the download URL for the update."""
        if self.download_url:
            return self.download_url
            
        if self.release_data:
            # Try to find a ZIP asset first
            for asset in self.release_data.get('assets', []):
                if asset['name'].endswith('.zip'):
                    return asset['browser_download_url']
            
            # Fall back to source code archive
            return self.release_data.get('zipball_url')
        
        return None
