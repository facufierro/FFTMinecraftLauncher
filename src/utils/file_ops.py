"""Enhanced file operations utilities."""

import shutil
import zipfile
import tempfile
import time
from pathlib import Path
from typing import Optional, Callable, List
from .logger import get_logger


class FileOperations:
    """Enhanced file operations with better error handling and progress tracking."""
    
    def __init__(self):
        self.logger = get_logger()
    
    def safe_copy(self, src: Path, dst: Path, max_retries: int = 3) -> bool:
        """Safely copy a file with retries.
        
        Args:
            src: Source file path
            dst: Destination file path
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Ensure destination directory exists
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy the file
                shutil.copy2(str(src), str(dst))
                self.logger.debug(f"Copied {src} -> {dst}")
                return True
                
            except Exception as e:
                self.logger.warning(f"Copy attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)  # Wait before retry
                else:
                    self.logger.error(f"Failed to copy {src} -> {dst} after {max_retries} attempts")
        
        return False
    
    def safe_move(self, src: Path, dst: Path, max_retries: int = 3) -> bool:
        """Safely move a file with retries.
        
        Args:
            src: Source file path
            dst: Destination file path
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Ensure destination directory exists
                dst.parent.mkdir(parents=True, exist_ok=True)
                
                # Move the file
                shutil.move(str(src), str(dst))
                self.logger.debug(f"Moved {src} -> {dst}")
                return True
                
            except Exception as e:
                self.logger.warning(f"Move attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)  # Wait before retry
                else:
                    self.logger.error(f"Failed to move {src} -> {dst} after {max_retries} attempts")
        
        return False
    
    def safe_delete(self, path: Path, max_retries: int = 3) -> bool:
        """Safely delete a file or directory with retries.
        
        Args:
            path: Path to delete
            max_retries: Maximum number of retry attempts
            
        Returns:
            True if successful or doesn't exist, False otherwise
        """
        if not path.exists():
            return True
        
        for attempt in range(max_retries):
            try:
                if path.is_file():
                    path.unlink()
                else:
                    shutil.rmtree(str(path))
                
                self.logger.debug(f"Deleted {path}")
                return True
                
            except Exception as e:
                self.logger.warning(f"Delete attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5)  # Wait before retry
                else:
                    self.logger.error(f"Failed to delete {path} after {max_retries} attempts")
        
        return False
    
    def extract_zip(self, zip_path: Path, extract_to: Path, 
                   progress_callback: Optional[Callable[[str], None]] = None) -> Optional[Path]:
        """Extract a ZIP file with progress tracking.
        
        Args:
            zip_path: Path to the ZIP file
            extract_to: Directory to extract to
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to extracted content or None if failed
        """
        try:
            if progress_callback:
                progress_callback("Extracting files...")
            
            # Ensure extraction directory exists
            extract_to.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            # Find the extracted content
            extracted_items = list(extract_to.iterdir())
            
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                # Single directory extracted
                result_path = extracted_items[0]
            else:
                # Multiple items or files extracted
                result_path = extract_to
            
            if progress_callback:
                progress_callback("Extraction completed")
            
            self.logger.info(f"Extracted {zip_path} to {result_path}")
            return result_path
            
        except Exception as e:
            self.logger.error(f"Failed to extract {zip_path}: {e}")
            if progress_callback:
                progress_callback("Extraction failed")
            return None
    
    def sync_directories(self, src_dir: Path, dst_dir: Path, 
                        exclude_patterns: Optional[List[str]] = None,
                        progress_callback: Optional[Callable[[str], None]] = None) -> bool:
        """Synchronize two directories with exclusion support.
        
        Args:
            src_dir: Source directory
            dst_dir: Destination directory
            exclude_patterns: Patterns to exclude (e.g., ['*.pyc', '__pycache__'])
            progress_callback: Optional callback for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if progress_callback:
                progress_callback(f"Syncing {src_dir.name}...")
            
            # Ensure destination exists
            dst_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all files and directories
            for item in src_dir.rglob('*'):
                if item.is_file():
                    # Check exclusion patterns
                    if exclude_patterns:
                        excluded = False
                        for pattern in exclude_patterns:
                            if item.match(pattern):
                                excluded = True
                                break
                        if excluded:
                            continue
                    
                    # Calculate relative path and destination
                    rel_path = item.relative_to(src_dir)
                    dst_file = dst_dir / rel_path
                    
                    # Copy the file
                    if not self.safe_copy(item, dst_file):
                        return False
            
            if progress_callback:
                progress_callback("Sync completed")
            
            self.logger.info(f"Synced {src_dir} -> {dst_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to sync directories: {e}")
            if progress_callback:
                progress_callback("Sync failed")
            return False
    
    def create_backup(self, file_path: Path, backup_suffix: str = ".backup") -> Optional[Path]:
        """Create a backup of a file.
        
        Args:
            file_path: File to backup
            backup_suffix: Suffix to add to backup file
            
        Returns:
            Path to backup file or None if failed
        """
        if not file_path.exists():
            return None
        
        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
        
        if self.safe_copy(file_path, backup_path):
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path
        
        return None
    
    def with_temp_directory(self, operation: Callable[[Path], bool]) -> bool:
        """Execute an operation with a temporary directory that gets cleaned up.
        
        Args:
            operation: Function that takes a temp directory path and returns success
            
        Returns:
            Result of the operation
        """
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                return operation(temp_path)
        except Exception as e:
            self.logger.error(f"Temporary directory operation failed: {e}")
            return False


# Global file operations instance
_file_ops: Optional[FileOperations] = None


def get_file_ops() -> FileOperations:
    """Get the global file operations instance."""
    global _file_ops
    if _file_ops is None:
        _file_ops = FileOperations()
    return _file_ops


# Convenience functions
def safe_copy(src: Path, dst: Path) -> bool:
    """Safely copy a file."""
    return get_file_ops().safe_copy(src, dst)


def safe_move(src: Path, dst: Path) -> bool:
    """Safely move a file."""
    return get_file_ops().safe_move(src, dst)


def safe_delete(path: Path) -> bool:
    """Safely delete a file or directory."""
    return get_file_ops().safe_delete(path)


def extract_zip(zip_path: Path, extract_to: Path) -> Optional[Path]:
    """Extract a ZIP file."""
    return get_file_ops().extract_zip(zip_path, extract_to)
