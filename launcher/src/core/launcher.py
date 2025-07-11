"""Core launcher logic for the FFT Minecraft Launcher."""

import threading
from pathlib import Path
from typing import Optional, Callable
from ..models.config import LauncherConfig, ConfigurationError
from ..models.update_info import UpdateInfo
from ..services.github_service import GitHubService
from ..services.update_service import UpdateService
from ..services.minecraft_service import MinecraftService
from ..services.updater_download_service import UpdaterDownloadService
from ..utils.logging_utils import get_logger, setup_logger
from ..utils.github_utils import get_github_client, compare_versions, is_newer_version
from .events import LauncherEvents, EventType

# Version constant - updated automatically by build script
LAUNCHER_VERSION = "1.1.8"


class LauncherCore:
    """Core launcher logic and coordination."""
    
    def __init__(self, config_path: str = "launcher_config.json"):
        """Initialize the launcher core.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config: Optional[LauncherConfig] = None
        self.events = LauncherEvents()
        self.logger = get_logger()
        
        # Services
        self.github_service: Optional[GitHubService] = None
        self.update_service: Optional[UpdateService] = None
        self.minecraft_service: Optional[MinecraftService] = None
        self.updater_download_service: Optional[UpdaterDownloadService] = None
        
        # State
        self.is_updating = False
        self.current_update_info: Optional[UpdateInfo] = None
        self._update_thread: Optional[threading.Thread] = None
        
        # Initialize
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the launcher components."""
        try:
            # Setup logging
            self.logger.info("Initializing FFT Minecraft Launcher...")
            self.logger.info(f"Using log directory: {self.logger.log_dir}")
            self.logger.info(f"Latest log: {self.logger.latest_log_path}")
            
            # Clean up old logs
            self.logger.cleanup_old_logs(max_logs=10)
            
            # Download updater first - this is the first thing we do
            self.logger.info("Downloading updater...")
            self.updater_download_service = UpdaterDownloadService()
            updater_success = self.updater_download_service.download_updater_at_startup()
            
            if not updater_success:
                self.logger.warning("Updater download failed, but continuing with launcher initialization")
            
            # Load configuration
            self.load_config()
            
            # Initialize services
            self._initialize_services()
            
            # Emit initialization event
            self.events.emit(EventType.CONFIG_LOADED, self.config)
            
            self.logger.info("Launcher core initialized successfully")
            
        except Exception as e:
            self.logger.critical(f"Failed to initialize launcher: {e}")
            raise LauncherError(f"Initialization failed: {e}")
    
    def _initialize_services(self) -> None:
        """Initialize all services."""
        if not self.config:
            raise LauncherError("Configuration not loaded")
        
        self.github_service = GitHubService(self.config.github_repo)
        self.update_service = UpdateService(self.config)
        self.minecraft_service = MinecraftService(self.config)
        
        # Set up progress callback for update service
        self.update_service.set_progress_callback(self._on_update_progress)
    
    def load_config(self) -> None:
        """Load the launcher configuration."""
        try:
            self.config = LauncherConfig.load_from_file(self.config_path)
            
            # Validate configuration
            errors = self.config.validate()
            if errors:
                error_msg = "Configuration validation failed:\n" + "\n".join(errors)
                raise ConfigurationError(error_msg)
            
            self.logger.info("Configuration loaded successfully")
            
        except ConfigurationError as e:
            self.logger.error(f"Configuration error: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise LauncherError(f"Failed to load configuration: {e}")
    
    def save_config(self) -> None:
        """Save the current configuration."""
        if not self.config:
            return
        
        try:
            self.config.save_to_file(self.config_path)
            self.events.emit(EventType.CONFIG_SAVED, self.config)
            self.logger.info("Configuration saved successfully")
            
        except ConfigurationError as e:
            self.logger.error(f"Failed to save configuration: {e}")
            raise
    
    def update_config(self, **kwargs) -> None:
        """Update configuration with new values.
        
        Args:
            **kwargs: Configuration values to update
        """
        if not self.config:
            return
        
        old_config = dict(self.config.__dict__)
        
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        self.events.emit(EventType.CONFIG_CHANGED, {
            'old': old_config,
            'new': dict(self.config.__dict__)
        })
    
    def check_for_launcher_update(self, callback: Optional[Callable[[bool, str, str], None]] = None) -> None:
        """Check for launcher updates asynchronously.
        
        Args:
            callback: Optional callback with (update_available, current_version, latest_version)
        """
        if not self.config:
            if callback:
                callback(False, "Unknown", "Unknown")
            return
        
        def check_thread():
            try:
                # Get current version from constant
                current_version = LAUNCHER_VERSION
                
                # Get latest version from GitHub
                github_client = get_github_client()
                release_data = github_client.get_latest_release("facufierro/FFTMinecraftLauncher")
                
                if not release_data:
                    if callback:
                        callback(False, current_version, "Unknown")
                    return
                
                latest_version = release_data.get('tag_name', '').lstrip('v')
                update_available = is_newer_version(latest_version, current_version)
                
                # Update config if needed (with proper null check)
                if self.config and (not self.config.launcher_version or self.config.launcher_version != current_version):
                    self.config.launcher_version = current_version
                
                if callback:
                    callback(update_available, current_version, latest_version)
                
            except Exception as e:
                self.logger.error(f"Launcher version check failed: {e}")
                if callback:
                    callback(False, "Unknown", "Unknown")
        
        import threading
        check_thread_obj = threading.Thread(target=check_thread, daemon=True)
        check_thread_obj.start()
    
    def check_for_updates(self, callback: Optional[Callable[[UpdateInfo], None]] = None) -> None:
        """Check for updates asynchronously.
        
        Args:
            callback: Optional callback to call with update info
        """
        if self.is_updating:
            self.logger.warning("Update check already in progress")
            return
        
        self.is_updating = True
        self.events.emit(EventType.UPDATE_CHECK_STARTED)
        
        def check_thread():
            try:
                if not self.update_service:
                    raise LauncherError("Update service not initialized")
                
                update_info = self.update_service.check_for_updates()
                self.current_update_info = update_info
                
                self.events.emit(EventType.UPDATE_CHECK_COMPLETED, update_info)
                
                if callback:
                    callback(update_info)
                
            except Exception as e:
                self.logger.error(f"Update check failed: {e}")
                self.events.emit(EventType.UPDATE_CHECK_FAILED, str(e))
            finally:
                self.is_updating = False
        
        self._update_thread = threading.Thread(target=check_thread, daemon=True)
        self._update_thread.start()
    
    def perform_update(self, force: bool = False, callback: Optional[Callable[[bool], None]] = None) -> None:
        """Perform update asynchronously.
        
        Args:
            force: Whether to force update
            callback: Optional callback to call with success status
        """
        if self.is_updating:
            self.logger.warning("Update already in progress")
            return
        
        if not force and (not self.current_update_info or not self.current_update_info.updates_available):
            self.logger.warning("No updates available")
            return
        
        self.is_updating = True
        self.events.emit(EventType.UPDATE_STARTED)
        
        def update_thread():
            try:
                self.logger.info("Starting update process...")
                
                if not self.update_service:
                    raise LauncherError("Update service not initialized")
                
                if force:
                    success = self.update_service.force_update()
                else:
                    if not self.current_update_info:
                        raise LauncherError("No update information available")
                    success = self.update_service.perform_update(self.current_update_info)
                
                if success:
                    # Update config with new version
                    if self.current_update_info and self.config:
                        self.config.current_version = self.current_update_info.latest_version
                        self.save_config()
                    
                    self.events.emit(EventType.UPDATE_COMPLETED)
                    self.logger.info("Update completed successfully")
                else:
                    self.events.emit(EventType.UPDATE_FAILED, "Update process failed")
                
                if callback:
                    callback(success)
                
            except Exception as e:
                self.logger.error(f"Update failed: {e}")
                self.events.emit(EventType.UPDATE_FAILED, str(e))
                if callback:
                    callback(False)
            finally:
                self.is_updating = False
        
        self._update_thread = threading.Thread(target=update_thread, daemon=True)
        self._update_thread.start()
    
    def launch_minecraft(self, callback: Optional[Callable[[bool], None]] = None) -> None:
        """Launch Minecraft.
        
        Args:
            callback: Optional callback to call with success status
        """
        self.events.emit(EventType.MINECRAFT_LAUNCH_STARTED)
        
        try:
            if not self.minecraft_service:
                raise LauncherError("Minecraft service not initialized")
            
            success = self.minecraft_service.launch()
            
            if success:
                self.events.emit(EventType.MINECRAFT_LAUNCH_COMPLETED)
            else:
                self.events.emit(EventType.MINECRAFT_LAUNCH_FAILED, "Launch failed")
            
            if callback:
                callback(success)
                
        except Exception as e:
            self.logger.error(f"Minecraft launch failed: {e}")
            self.events.emit(EventType.MINECRAFT_LAUNCH_FAILED, str(e))
            if callback:
                callback(False)
    
    def validate_minecraft_installation(self) -> bool:
        """Validate Minecraft installation.
        
        Returns:
            True if installation is valid, False otherwise.
        """
        if not self.minecraft_service:
            return False
        return self.minecraft_service.validate_installation()
    
    def verify_mods_folder_integrity(self, callback: Optional[Callable[[bool, str], None]] = None) -> None:
        """Verify mods folder integrity against repository.
        
        This method checks if the local mods folder matches the repository version
        and can be used to detect synchronization issues.
        
        Args:
            callback: Optional callback with (is_valid, message) parameters
        """
        if not self.update_service or not self.config:
            if callback:
                callback(False, "Services not initialized")
            return
        
        def verify_thread():
            try:
                # Type guard checks
                if not self.update_service or not self.config:
                    if callback:
                        callback(False, "Required services not available")
                    return
                
                self.logger.info("Starting mods folder integrity verification...")
                
                # Get latest release info for comparison
                update_info = self.update_service.check_for_updates()
                
                # Download and compare mods folder
                import tempfile
                from pathlib import Path
                
                download_url = update_info.get_download_url()
                if not download_url:
                    if callback:
                        callback(False, "Could not get repository download URL")
                    return
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    zip_path = temp_path / "verify.zip"
                    extract_path = temp_path / "extract"
                    
                    # Download and extract
                    if not self.update_service.github_service.download_file(download_url, str(zip_path)):
                        if callback:
                            callback(False, "Failed to download repository files for verification")
                        return
                    
                    import zipfile
                    with zipfile.ZipFile(zip_path, 'r') as zip_file:
                        zip_file.extractall(extract_path)
                    
                    # Get instance path
                    instance_path = self.config.get_selected_instance_path()
                    if not instance_path:
                        if callback:
                            callback(False, "Instance path not available")
                        return
                    
                    # Verify mods folder using ModsManagementService
                    from ..services.mods_management_service import ModsManagementService
                    mods_service = ModsManagementService()
                    is_valid = mods_service.verify_mods_folder_integrity(extract_path, instance_path)
                    
                    if is_valid:
                        message = "Mods folder is properly synchronized with repository"
                        self.logger.info(message)
                    else:
                        message = "Mods folder differs from repository version - update recommended"
                        self.logger.warning(message)
                    
                    if callback:
                        callback(is_valid, message)
                        
            except Exception as e:
                error_msg = f"Error during mods folder verification: {e}"
                self.logger.error(error_msg)
                if callback:
                    callback(False, error_msg)
        
        import threading
        verify_thread_obj = threading.Thread(target=verify_thread, daemon=True)
        verify_thread_obj.start()
    
    def get_minecraft_info(self) -> dict:
        """Get Minecraft installation information.
        
        Returns:
            Dictionary containing installation info.
        """
        if not self.minecraft_service:
            return {}
        return self.minecraft_service.get_installation_info()
    
    def _on_update_progress(self, message: str) -> None:
        """Handle update progress messages.
        
        Args:
            message: Progress message
        """
        self.events.emit(EventType.UPDATE_PROGRESS, message)
    
    def shutdown(self) -> None:
        """Shutdown the launcher core."""
        self.logger.info("Shutting down launcher core...")
        
        # Wait for any ongoing update to complete
        if self._update_thread and self._update_thread.is_alive():
            self.logger.info("Waiting for update to complete...")
            self._update_thread.join(timeout=5.0)
        
        # Clear event listeners
        self.events.clear_listeners()
        
        self.logger.info("Launcher core shutdown complete")


class LauncherError(Exception):
    """Exception raised for launcher-related errors."""
    pass
