"""Backup service for managing instance backups and clean installations."""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Callable
from ..models.config import LauncherConfig
from ..utils.logging_utils import get_logger


class BackupService:
    """Service for managing instance backups and clean installations."""
    
    def __init__(self, config: LauncherConfig):
        """Initialize the backup service.
        
        Args:
            config: Launcher configuration
        """
        self.config = config
        self.logger = get_logger()
        self.progress_callback: Optional[Callable[[str], None]] = None
    
    def set_progress_callback(self, callback: Callable[[str], None]) -> None:
        """Set a callback function for progress updates.
        
        Args:
            callback: Function to call with progress messages
        """
        self.progress_callback = callback
    
    def _update_progress(self, message: str) -> None:
        """Update progress with a message.
        
        Args:
            message: Progress message
        """
        self.logger.info(message)
        if self.progress_callback:
            self.progress_callback(message)
    
    def backup_instance_configs(self, instance_path: Path) -> Optional[Path]:
        """Backup critical instance configuration files.
        
        Args:
            instance_path: Path to the instance directory
            
        Returns:
            Path to the backup directory, or None if backup failed.
        """
        try:
            if not instance_path.exists():
                self.logger.warning("Instance path does not exist - no backup needed")
                return None
            
            # Create backup directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path(tempfile.gettempdir()) / f"fft_backup_{timestamp}"
            backup_dir.mkdir(exist_ok=True)
            
            self._update_progress("Backing up configuration files...")
            self.logger.info(f"Creating backup at: {backup_dir}")
            
            # Files and directories to backup
            backup_items = [
                "config",           # Mod configurations
                "options.txt",      # Minecraft client options
                "optionsof.txt",    # OptiFine options (if exists)
                "servers.dat",      # Server list (if exists)
                "screenshots",      # User screenshots (if exists)
                "saves",           # Worlds (if exists)
                "resourcepacks",   # Custom resource packs (preserving user additions)
            ]
            
            backup_count = 0
            for item_name in backup_items:
                source_item = instance_path / item_name
                if source_item.exists():
                    dest_item = backup_dir / item_name
                    
                    try:
                        if source_item.is_dir():
                            self._update_progress(f"Backing up directory: {item_name}")
                            # For resourcepacks, only backup non-FFT packs to preserve user additions
                            if item_name == "resourcepacks":
                                self._backup_user_resource_packs(source_item, dest_item)
                            else:
                                shutil.copytree(source_item, dest_item, dirs_exist_ok=True)
                        else:
                            self._update_progress(f"Backing up file: {item_name}")
                            dest_item.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(source_item, dest_item)
                        
                        backup_count += 1
                        self.logger.info(f"Backed up: {item_name}")
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to backup {item_name}: {e}")
                        continue
            
            if backup_count > 0:
                self.logger.info(f"Successfully backed up {backup_count} items to: {backup_dir}")
                return backup_dir
            else:
                self.logger.warning("No items were backed up")
                # Clean up empty backup directory
                try:
                    backup_dir.rmdir()
                except:
                    pass
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return None
    
    def _backup_user_resource_packs(self, source_dir: Path, dest_dir: Path) -> None:
        """Backup only user-added resource packs, excluding FFT packs.
        
        Args:
            source_dir: Source resourcepacks directory
            dest_dir: Destination backup directory
        """
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            user_packs_found = 0
            for pack_file in source_dir.iterdir():
                # Skip FFT resource packs as they'll be restored from the repository
                if (pack_file.name.startswith("fft-resourcepack") or 
                    pack_file.name.startswith("fft_resourcepack")):
                    self.logger.debug(f"Skipping FFT resource pack: {pack_file.name}")
                    continue
                
                # Backup user-added resource packs
                dest_pack = dest_dir / pack_file.name
                try:
                    if pack_file.is_dir():
                        shutil.copytree(pack_file, dest_pack, dirs_exist_ok=True)
                    else:
                        shutil.copy2(pack_file, dest_pack)
                    
                    user_packs_found += 1
                    self.logger.info(f"Backed up user resource pack: {pack_file.name}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to backup resource pack {pack_file.name}: {e}")
            
            if user_packs_found == 0:
                self.logger.info("No user resource packs found to backup")
            else:
                self.logger.info(f"Backed up {user_packs_found} user resource packs")
                
        except Exception as e:
            self.logger.warning(f"Failed to backup user resource packs: {e}")
    
    def restore_instance_configs(self, backup_path: Path, instance_path: Path) -> bool:
        """Restore configuration files from backup.
        
        Args:
            backup_path: Path to the backup directory
            instance_path: Path to the instance directory
            
        Returns:
            True if restore was successful, False otherwise.
        """
        try:
            if not backup_path.exists():
                self.logger.warning("Backup path does not exist")
                return False
            
            self._update_progress("Restoring configuration files...")
            self.logger.info(f"Restoring from backup: {backup_path}")
            
            # Ensure instance directory exists
            instance_path.mkdir(parents=True, exist_ok=True)
            
            restore_count = 0
            for backup_item in backup_path.iterdir():
                dest_item = instance_path / backup_item.name
                
                try:
                    if backup_item.is_dir():
                        self._update_progress(f"Restoring directory: {backup_item.name}")
                        # For resourcepacks, merge with existing (don't overwrite FFT packs)
                        if backup_item.name == "resourcepacks":
                            self._restore_user_resource_packs(backup_item, dest_item)
                        else:
                            # Remove existing directory and restore backup
                            if dest_item.exists():
                                shutil.rmtree(dest_item)
                            shutil.copytree(backup_item, dest_item)
                    else:
                        self._update_progress(f"Restoring file: {backup_item.name}")
                        dest_item.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_item, dest_item)
                    
                    restore_count += 1
                    self.logger.info(f"Restored: {backup_item.name}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to restore {backup_item.name}: {e}")
                    continue
            
            if restore_count > 0:
                self.logger.info(f"Successfully restored {restore_count} items")
                return True
            else:
                self.logger.warning("No items were restored")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}")
            return False
    
    def _restore_user_resource_packs(self, backup_dir: Path, dest_dir: Path) -> None:
        """Restore user resource packs without overwriting FFT packs.
        
        Args:
            backup_dir: Backup resourcepacks directory
            dest_dir: Destination resourcepacks directory
        """
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            restored_count = 0
            for pack_file in backup_dir.iterdir():
                dest_pack = dest_dir / pack_file.name
                
                # Don't overwrite existing FFT packs, but restore user packs
                if dest_pack.exists() and (pack_file.name.startswith("fft-resourcepack") or 
                                         pack_file.name.startswith("fft_resourcepack")):
                    self.logger.debug(f"Skipping restore of FFT pack (preserving repository version): {pack_file.name}")
                    continue
                
                try:
                    if pack_file.is_dir():
                        if dest_pack.exists():
                            shutil.rmtree(dest_pack)
                        shutil.copytree(pack_file, dest_pack)
                    else:
                        shutil.copy2(pack_file, dest_pack)
                    
                    restored_count += 1
                    self.logger.info(f"Restored user resource pack: {pack_file.name}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to restore resource pack {pack_file.name}: {e}")
            
            if restored_count == 0:
                self.logger.info("No user resource packs to restore")
            else:
                self.logger.info(f"Restored {restored_count} user resource packs")
                
        except Exception as e:
            self.logger.warning(f"Failed to restore user resource packs: {e}")
    
    def clean_instance(self, instance_path: Path, preserve_backups: bool = True) -> bool:
        """Clean the instance directory, optionally preserving certain files.
        
        Args:
            instance_path: Path to the instance directory
            preserve_backups: Whether to backup configs before cleaning
            
        Returns:
            True if cleaning was successful, False otherwise.
        """
        try:
            if not instance_path.exists():
                self.logger.info("Instance directory does not exist - nothing to clean")
                return True
            
            backup_path = None
            if preserve_backups:
                # Create backup before cleaning
                backup_path = self.backup_instance_configs(instance_path)
                if backup_path:
                    self.logger.info(f"Configurations backed up to: {backup_path}")
                else:
                    self.logger.warning("Failed to create backup - proceeding with clean anyway")
            
            self._update_progress("Cleaning instance directory...")
            self.logger.info(f"Cleaning instance directory: {instance_path}")
            
            # Items to remove during clean (everything except what we want to preserve)
            items_to_remove = []
            items_to_preserve = {
                "launcher_profiles.json"  # Keep launcher profiles
            }
            
            for item in instance_path.iterdir():
                if item.name not in items_to_preserve:
                    items_to_remove.append(item)
            
            removed_count = 0
            for item in items_to_remove:
                try:
                    if item.is_dir():
                        self._update_progress(f"Removing directory: {item.name}")
                        shutil.rmtree(item)
                    else:
                        self._update_progress(f"Removing file: {item.name}")
                        item.unlink()
                    
                    removed_count += 1
                    self.logger.info(f"Removed: {item.name}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to remove {item.name}: {e}")
                    continue
            
            self.logger.info(f"Cleaned {removed_count} items from instance directory")
            
            # Store backup path for potential restoration
            if backup_path:
                self._store_backup_info(instance_path, backup_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clean instance: {e}")
            return False
    
    def _store_backup_info(self, instance_path: Path, backup_path: Path) -> None:
        """Store backup information for later restoration.
        
        Args:
            instance_path: Path to the instance directory
            backup_path: Path to the backup directory
        """
        try:
            backup_info_file = instance_path / ".backup_info"
            with open(backup_info_file, 'w', encoding='utf-8') as f:
                f.write(f"{backup_path}\n")
                f.write(f"{datetime.now().isoformat()}\n")
            
            self.logger.debug(f"Stored backup info: {backup_path}")
            
        except Exception as e:
            self.logger.warning(f"Failed to store backup info: {e}")
    
    def get_latest_backup_path(self, instance_path: Path) -> Optional[Path]:
        """Get the path to the latest backup for an instance.
        
        Args:
            instance_path: Path to the instance directory
            
        Returns:
            Path to the latest backup directory, or None if no backup found.
        """
        try:
            backup_info_file = instance_path / ".backup_info"
            if not backup_info_file.exists():
                return None
            
            with open(backup_info_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            if len(lines) >= 1:
                backup_path = Path(lines[0].strip())
                if backup_path.exists():
                    return backup_path
                else:
                    self.logger.warning(f"Backup path no longer exists: {backup_path}")
                    return None
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to read backup info: {e}")
            return None
    
    def clean_old_backups(self, max_backups: int = 5) -> None:
        """Clean up old backup directories.
        
        Args:
            max_backups: Maximum number of backups to keep
        """
        try:
            temp_dir = Path(tempfile.gettempdir())
            backup_dirs = []
            
            # Find all FFT backup directories
            for item in temp_dir.iterdir():
                if item.is_dir() and item.name.startswith("fft_backup_"):
                    try:
                        # Extract timestamp from name for sorting
                        timestamp_str = item.name.replace("fft_backup_", "")
                        timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        backup_dirs.append((timestamp, item))
                    except ValueError:
                        # Invalid timestamp format, skip
                        continue
            
            # Sort by timestamp (newest first)
            backup_dirs.sort(key=lambda x: x[0], reverse=True)
            
            # Remove old backups
            removed_count = 0
            for i, (timestamp, backup_dir) in enumerate(backup_dirs):
                if i >= max_backups:
                    try:
                        shutil.rmtree(backup_dir)
                        removed_count += 1
                        self.logger.info(f"Removed old backup: {backup_dir.name}")
                    except Exception as e:
                        self.logger.warning(f"Failed to remove old backup {backup_dir.name}: {e}")
            
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old backup(s)")
            else:
                self.logger.debug("No old backups to clean up")
                
        except Exception as e:
            self.logger.warning(f"Failed to clean old backups: {e}")
    
    def perform_clean_install(self, instance_path: Path) -> Optional[Path]:
        """Perform a clean installation by backing up configs and cleaning the instance.
        
        Args:
            instance_path: Path to the instance directory
            
        Returns:
            Path to the backup directory if successful, None otherwise.
        """
        try:
            self._update_progress("Performing clean installation...")
            
            # Clean old backups first
            self.clean_old_backups()
            
            # Clean the instance with backup
            if self.clean_instance(instance_path, preserve_backups=True):
                backup_path = self.get_latest_backup_path(instance_path)
                if backup_path:
                    self.logger.info("Clean installation completed - configurations backed up")
                    return backup_path
                else:
                    self.logger.info("Clean installation completed - no configurations to backup")
                    return None
            else:
                raise Exception("Failed to clean instance")
                
        except Exception as e:
            self.logger.error(f"Clean installation failed: {e}")
            return None


class BackupError(Exception):
    """Exception raised for backup-related errors."""
    pass
