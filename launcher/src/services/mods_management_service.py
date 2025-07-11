"""Service for managing mods folder operations."""

import shutil
from pathlib import Path
from typing import List, Optional, Set, Tuple
from .file_comparison_service import FileComparisonService
from ..utils.logging_utils import get_logger


class ModsManagementService:
    """Service responsible for mods folder management and verification."""
    
    def __init__(self):
        """Initialize the mods management service."""
        self.logger = get_logger()
        self.file_comparison = FileComparisonService()
    
    def verify_mods_folder_integrity(self, remote_extract_path: Path, instance_path: Path) -> bool:
        """Perform verification of mods folder integrity.
        
        This method provides verification specifically for the mods folder
        to ensure it's always synchronized with the repository version.
        
        Args:
            remote_extract_path: Path to extracted remote files
            instance_path: Path to local instance
            
        Returns:
            True if mods folder is properly synchronized, False if update needed.
        """
        try:
            remote_mods = remote_extract_path / "mods"
            local_mods = instance_path / "mods"
            
            # If remote has mods folder but local doesn't, update needed
            if remote_mods.exists() and not local_mods.exists():
                self.logger.warning("Local mods folder missing - update needed")
                return False
            
            # If remote doesn't have mods folder, local shouldn't either
            if not remote_mods.exists():
                if local_mods.exists() and any(local_mods.iterdir()):
                    self.logger.warning("Local mods folder should be empty - cleaning needed")
                    return False
                return True  # Both don't exist or local is empty
            
            # Both exist - perform detailed comparison
            remote_mod_files = self.file_comparison.get_mod_files_with_metadata(remote_mods)
            local_mod_files = self.file_comparison.get_mod_files_with_metadata(local_mods)
            
            # Check if mod file sets are different
            if remote_mod_files != local_mod_files:
                self.logger.warning("Mods folder contents differ from repository:")
                
                # Log specific differences
                only_in_remote = remote_mod_files - local_mod_files
                only_in_local = local_mod_files - remote_mod_files
                
                if only_in_remote:
                    self.logger.info(f"Mods in repository but not locally: {[str(f[0]) for f in only_in_remote]}")
                if only_in_local:
                    self.logger.info(f"Mods locally but not in repository: {[str(f[0]) for f in only_in_local]}")
                
                return False
            
            # Additional hash-based verification for critical mod files
            for rel_path, size in remote_mod_files:
                remote_file = remote_mods / rel_path
                local_file = local_mods / rel_path
                
                if not local_file.exists():
                    continue  # Already caught above
                
                # For files that might be critical, do hash comparison
                if self.file_comparison.is_critical_mod_file(rel_path):
                    try:
                        remote_hash = self.file_comparison.get_file_hash(remote_file)
                        local_hash = self.file_comparison.get_file_hash(local_file)
                        
                        if remote_hash != local_hash:
                            self.logger.warning(f"Critical mod file hash mismatch: {rel_path}")
                            return False
                    except Exception as e:
                        self.logger.warning(f"Failed to verify hash for {rel_path}: {e}")
                        return False
            
            self.logger.info("Mods folder integrity verification passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during mods folder integrity check: {e}")
            return False  # Assume update needed on error
    
    def verify_mods_folder_post_sync(self, source_path: Path, instance_path: Path) -> None:
        """Verify mods folder integrity after synchronization.
        
        This method performs a final verification that the mods folder was correctly
        synchronized and matches the repository version exactly.
        
        Args:
            source_path: Path to the source files that were synced
            instance_path: Path to the local instance
        """
        try:
            source_mods = source_path / "mods"
            local_mods = instance_path / "mods"
            
            self.logger.info("Performing post-sync verification of mods folder...")
            
            # Quick verification that folders match
            if not self.verify_mods_folder_integrity(source_path, instance_path):
                self.logger.error("Post-sync mods folder verification failed!")
                # Try to fix by re-syncing just the mods folder
                self.fix_mods_folder_sync(source_mods, local_mods)
            else:
                self.logger.info("Post-sync mods folder verification passed")
                
            # Log the final state for debugging
            self.log_mods_folder_state(local_mods)
            
        except Exception as e:
            self.logger.error(f"Error during post-sync mods folder verification: {e}")
    
    def fix_mods_folder_sync(self, source_mods: Path, local_mods: Path) -> None:
        """Attempt to fix mods folder synchronization issues.
        
        Args:
            source_mods: Path to source mods folder
            local_mods: Path to local mods folder
        """
        try:
            from ..utils.file_ops import get_file_ops
            
            self.logger.warning("Attempting to fix mods folder synchronization...")
            file_ops = get_file_ops()
            
            if source_mods.exists():
                # Re-sync the mods directory with .connector exclusion
                exclude_patterns = [".connector", ".connector/*"]
                if file_ops.sync_directories(source_mods, local_mods, exclude_patterns):
                    self.logger.info("Mods folder re-synchronization completed")
                else:
                    self.logger.error("Failed to re-synchronize mods folder")
            else:
                # If source doesn't have mods, ensure local is empty
                if local_mods.exists():
                    shutil.rmtree(local_mods)
                    local_mods.mkdir(exist_ok=True)
                    self.logger.info("Cleaned local mods folder (no mods in repository)")
                    
        except Exception as e:
            self.logger.error(f"Failed to fix mods folder synchronization: {e}")
    
    def log_mods_folder_state(self, mods_folder: Path) -> None:
        """Log the current state of the mods folder for debugging.
        
        Args:
            mods_folder: Path to the mods folder to inspect
        """
        try:
            if not mods_folder.exists():
                self.logger.info("Mods folder: Does not exist")
                return
            
            mod_files = []
            for file_path in mods_folder.rglob('*.jar'):
                rel_path = file_path.relative_to(mods_folder)
                # Skip .connector folder and its contents
                if not self.file_comparison._should_exclude_from_mods(rel_path):
                    mod_files.append(file_path)
            
            self.logger.info(f"Mods folder: Contains {len(mod_files)} mod files (excluding .connector)")
            
            if mod_files:
                for mod_file in sorted(mod_files):
                    rel_path = mod_file.relative_to(mods_folder)
                    size_mb = mod_file.stat().st_size / (1024 * 1024)
                    self.logger.info(f"  - {rel_path} ({size_mb:.1f} MB)")
            else:
                self.logger.info("  - No mod files found")
                
        except Exception as e:
            self.logger.warning(f"Failed to log mods folder state: {e}")
    
    def check_mods_folder_at_startup(self, instance_path: Path) -> None:
        """Perform a basic mods folder check during startup.
        
        This method performs a lightweight check of the mods folder during startup
        to log its current state and detect any obvious issues.
        
        Args:
            instance_path: Path to the instance directory
        """
        try:
            mods_folder = instance_path / "mods"
            
            if not mods_folder.exists():
                self.logger.warning("Mods folder does not exist - will be created during next update")
                return
            
            # Count mod files (excluding .connector folder)
            mod_files = []
            for file_path in mods_folder.rglob('*.jar'):
                rel_path = file_path.relative_to(mods_folder)
                # Skip .connector folder and its contents
                if not self.file_comparison._should_exclude_from_mods(rel_path):
                    mod_files.append(file_path)
            
            self.logger.info(f"Startup check: Found {len(mod_files)} mod files in mods folder (excluding .connector)")
            
            # Check for common issues
            if not mod_files:
                self.logger.warning("Mods folder is empty - this may indicate synchronization issues")
            
            # Check for non-jar files that might indicate corruption (excluding .connector)
            all_files = []
            for file_path in mods_folder.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(mods_folder)
                    # Skip .connector folder and its contents
                    if not self.file_comparison._should_exclude_from_mods(rel_path):
                        all_files.append(file_path)
            
            non_jar_files = [f for f in all_files if not f.name.endswith('.jar')]
            
            if non_jar_files:
                self.logger.warning(f"Found {len(non_jar_files)} non-jar files in mods folder:")
                for file in non_jar_files[:5]:  # Log up to 5 examples
                    self.logger.warning(f"  - {file.name}")
                if len(non_jar_files) > 5:
                    self.logger.warning(f"  ... and {len(non_jar_files) - 5} more")
            
        except Exception as e:
            self.logger.warning(f"Error during startup mods folder check: {e}")
    
    def cleanup_unwanted_mods(self, source: Path, destination: Path) -> None:
        """Remove mods that exist locally but not in the repository.
        
        Args:
            source: Source mods directory from repository
            destination: Local mods directory
        """
        try:
            # Get list of mod files in the repository
            repo_mods = set()
            for file_path in source.rglob('*.jar'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(source)
                    # Skip .connector folder
                    if not self.file_comparison._should_exclude_from_mods(rel_path):
                        repo_mods.add(rel_path)
            
            # Get list of mod files in local directory
            local_mods = []
            for file_path in destination.rglob('*.jar'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(destination)
                    # Skip .connector folder
                    if not self.file_comparison._should_exclude_from_mods(rel_path):
                        local_mods.append((rel_path, file_path))
            
            # Remove local mods that don't exist in the repository
            removed_count = 0
            for rel_path, full_path in local_mods:
                if rel_path not in repo_mods:
                    try:
                        full_path.unlink()
                        self.logger.info(f"Removed unwanted mod: {rel_path}")
                        removed_count += 1
                    except Exception as e:
                        self.logger.warning(f"Failed to remove mod {rel_path}: {e}")
            
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} unwanted mod(s)")
            else:
                self.logger.info("No unwanted mods to remove")
                
        except Exception as e:
            self.logger.warning(f"Error during mod cleanup: {e}")
