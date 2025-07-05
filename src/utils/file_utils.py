"""File utility functions for the FFT Minecraft Launcher."""

import os
import shutil
import hashlib
from pathlib import Path
from typing import List, Optional, Set
import zipfile


class FileUtils:
    """Utility class for file operations."""
    
    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
        """Calculate hash of a file."""
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except IOError as e:
            raise FileOperationError(f"Failed to calculate hash for {file_path}: {e}")
    
    @staticmethod
    def safe_remove_directory(directory: Path) -> None:
        """Safely remove a directory and all its contents."""
        if not directory.exists():
            return
            
        try:
            shutil.rmtree(directory)
        except OSError as e:
            raise FileOperationError(f"Failed to remove directory {directory}: {e}")
    
    @staticmethod
    def safe_copy_tree(src: Path, dst: Path, overwrite: bool = True) -> None:
        """Safely copy a directory tree."""
        try:
            if dst.exists() and overwrite:
                FileUtils.safe_remove_directory(dst)
            
            shutil.copytree(src, dst, dirs_exist_ok=overwrite)
        except (OSError, shutil.Error) as e:
            raise FileOperationError(f"Failed to copy {src} to {dst}: {e}")
    
    @staticmethod
    def safe_copy_file(src: Path, dst: Path) -> None:
        """Safely copy a single file."""
        try:
            # Ensure destination directory exists
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        except (OSError, shutil.Error) as e:
            raise FileOperationError(f"Failed to copy {src} to {dst}: {e}")
    
    @staticmethod
    def extract_zip(zip_path: Path, extract_to: Path) -> Path:
        """Extract a ZIP file and return the path to the extracted content."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
            
            # Find the extracted folder (usually there's one root folder)
            extracted_items = list(extract_to.iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                return extracted_items[0]
            
            return extract_to
            
        except (zipfile.BadZipFile, OSError) as e:
            raise FileOperationError(f"Failed to extract {zip_path}: {e}")
    
    @staticmethod
    def get_directory_files(directory: Path, extensions: Optional[List[str]] = None) -> Set[str]:
        """Get a set of all file names in a directory (recursively)."""
        files = set()
        
        if not directory.exists():
            return files
        
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    if extensions is None or file_path.suffix.lower() in extensions:
                        # Store relative path from the directory
                        rel_path = file_path.relative_to(directory)
                        files.add(str(rel_path))
        except OSError:
            pass  # Ignore permission errors
        
        return files
    
    @staticmethod
    def ensure_directory_exists(directory: Path) -> None:
        """Ensure a directory exists, creating it if necessary."""
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise FileOperationError(f"Failed to create directory {directory}: {e}")
    
    @staticmethod
    def cleanup_temp_files(temp_dir: Path) -> None:
        """Clean up temporary files and directories."""
        if temp_dir.exists():
            try:
                FileUtils.safe_remove_directory(temp_dir)
            except FileOperationError:
                pass  # Ignore cleanup errors


class FileOperationError(Exception):
    """Exception raised for file operation errors."""
    pass
