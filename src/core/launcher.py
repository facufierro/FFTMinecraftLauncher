"""Core launcher logic for the FFT Minecraft Launcher."""

import threading
from pathlib import Path
from typing import Optional, Callable
from ..models.config import LauncherConfig, ConfigurationError
from ..models.update_info import UpdateInfo
from ..services.github_service import GitHubService
from ..services.update_service import UpdateService
from ..services.minecraft_service import MinecraftService
from ..utils.logger import get_logger, setup_logger
from .events import LauncherEvents, EventType


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
            setup_logger()
            self.logger.info("Initializing FFT Minecraft Launcher...")
            
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
        
        # Re-initialize services if repo changed
        if 'github_repo' in kwargs:
            self._initialize_services()
        
        self.events.emit(EventType.CONFIG_CHANGED, {
            'old': old_config,
            'new': dict(self.config.__dict__)
        })
    
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
                self.logger.info("Checking for updates...")
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
