"""Service for comparing files and directories."""

import hashlib
from pathlib import Path
from typing import Set, Tuple
from ..utils.logging_utils import get_logger


class FileComparisonService:
    """Service responsible for file and directory comparison operations."""
    
    def __init__(self):
        """Initialize the file comparison service."""
        self.logger = get_logger()
    
    def compare_folder_contents(self, remote_folder: Path, local_folder: Path) -> bool:
        """Compare contents of two folders recursively.
        
        Args:
            remote_folder: Path to remote folder
            local_folder: Path to local folder
            
        Returns:
            True if folders are different, False if they match.
        """
        # Get all files in both folders
        remote_files = set()
        local_files = set()
        
        # Check if this is a mods folder to apply .connector exclusion
        is_mods_folder = remote_folder.name.lower() == "mods" or local_folder.name.lower() == "mods"
        
        if remote_folder.exists():
            for file_path in remote_folder.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(remote_folder)
                    # Skip .connector folder and its contents for mods folder
                    if is_mods_folder and self._should_exclude_from_mods(rel_path):
                        continue
                    remote_files.add(rel_path)
        
        if local_folder.exists():
            for file_path in local_folder.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(local_folder)
                    # Skip .connector folder and its contents for mods folder
                    if is_mods_folder and self._should_exclude_from_mods(rel_path):
                        continue
                    local_files.add(rel_path)
        
        # Check if file lists are different
        if remote_files != local_files:
            return True
        
        # Compare file contents for matching files
        for rel_path in remote_files:
            remote_file = remote_folder / rel_path
            local_file = local_folder / rel_path
            
            if not local_file.exists():
                return True
            
            # Compare file hashes
            try:
                remote_hash = self.get_file_hash(remote_file)
                local_hash = self.get_file_hash(local_file)
                
                if remote_hash != local_hash:
                    return True
            except Exception:
                return True  # Error reading file, assume different
        
        return False  # All files match
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash as hex string.
        """
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def get_mod_files_with_metadata(self, mods_folder: Path) -> Set[Tuple[Path, int]]:
        """Get all mod files with their metadata from a mods folder.
        
        Args:
            mods_folder: Path to the mods folder
            
        Returns:
            Set of tuples containing (relative_path, file_size).
        """
        mod_files = set()
        
        if not mods_folder.exists():
            return mod_files
        
        for file_path in mods_folder.rglob('*.jar'):
            if file_path.is_file():
                rel_path = file_path.relative_to(mods_folder)
                # Skip .connector folder and its contents
                if not self._should_exclude_from_mods(rel_path):
                    mod_files.add((rel_path, file_path.stat().st_size))
        
        return mod_files
    
    def _should_exclude_from_mods(self, rel_path: Path) -> bool:
        """Check if a relative path should be excluded from mods folder operations.
        
        Args:
            rel_path: Relative path to check
            
        Returns:
            True if the path should be excluded.
        """
        path_str = str(rel_path)
        return path_str.startswith('.connector') or '.connector' in path_str
    
    def is_critical_mod_file(self, file_path: Path) -> bool:
        """Determine if a mod file is critical and should have hash verification.
        
        Args:
            file_path: Relative path to the mod file
            
        Returns:
            True if the file is considered critical.
        """
        # Consider all .jar files as critical for now
        # In the future, this could be expanded to check for specific mod names
        return file_path.suffix.lower() == '.jar'
