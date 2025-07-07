"""Main window for the FFT Minecraft Launcher."""

import customtkinter as ctk
from datetime import datetime
from typing import Optional, Callable
from ..core.launcher import LauncherCore
from ..core.events import EventType
from ..models.update_info import UpdateInfo
from ..services.self_update_service import SelfUpdateService
from ..utils.ui_utils import UIUtils
from .components import StatusFrame, ProgressFrame, ButtonFrame, LogFrame, ThemeToggleButton
from .settings_window import SettingsWindow


class MainWindow:
    """Main window for the launcher application."""
    
    def __init__(self, launcher_core: LauncherCore):
        """Initialize the main window.
        
        Args:
            launcher_core: The launcher core instance
        """
        self.launcher_core = launcher_core
        self.settings_window: Optional[SettingsWindow] = None
        
        # Self-update service (console only - no UI)
        if launcher_core.config:
            self.self_update_service = SelfUpdateService(launcher_core.config)
            # Set progress callback for self-updates to show in log
            self.self_update_service.set_progress_callback(self._on_self_update_progress)
        else:
            self.self_update_service = None
        
        # Setup appearance
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("FFT Minecraft Modpack Launcher")
        UIUtils.center_window(self.root, 800, 600)
        self.root.resizable(True, True)
        
        # Setup UI
        self._setup_ui()
        self._setup_event_handlers()
        self._update_ui_from_config()
        
        # State tracking
        self.update_info = None
        self.needs_update = False
        self.instance_installed = False
        self.instance_up_to_date = False
        
        # Check for updates on startup to set initial button state
        self.root.after(1000, self._check_for_updates_on_startup)
    
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        # Main frame
        main_frame = ctk.CTkFrame(self.root, corner_radius=10)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)  # Log frame is back to row 4
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="FFT Minecraft Modpack Launcher",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, pady=(20, 20))
        
        # Theme toggle button
        self.theme_button = ThemeToggleButton(main_frame)
        self.theme_button.place(relx=1.0, x=-10, y=10, anchor='ne')
        self.theme_button.set_callback(self._on_theme_toggle)
        
        # Status frame
        self.status_frame = StatusFrame(main_frame)
        self.status_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        # Progress frame
        self.progress_frame = ProgressFrame(main_frame)
        self.progress_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        # Button frame
        self.button_frame = ButtonFrame(main_frame)
        self.button_frame.grid(row=3, column=0, pady=(0, 10))
        
        # Setup button callbacks - only launch button now
        self.button_frame.set_button_callbacks({
            'launch': self._handle_launch_action
        })
        
        # Launch after update checkbox
        self.launch_after_update_var = ctk.BooleanVar(value=False)
        self.launch_after_update_cb = ctk.CTkCheckBox(
            main_frame,
            text="Launch After Update",
            variable=self.launch_after_update_var,
            font=ctk.CTkFont(size=12),
            checkbox_width=16,
            checkbox_height=16
        )
        self.launch_after_update_cb.grid(row=3, column=0, sticky="e", padx=(0, 30), pady=(35, 0))
        
        # Log frame
        self.log_frame = LogFrame(main_frame)
        self.log_frame.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 20))
        
        # Initial log message
        self._add_log("FFT Minecraft Launcher started")
        self._add_log("Initializing launcher components...")
        self._add_log("Note: Button will show 'Update' if instance/modpack needs installation or updates")
    
    def _setup_event_handlers(self) -> None:
        """Setup event handlers for launcher events."""
        events = self.launcher_core.events
        
        # Update events
        events.subscribe(EventType.UPDATE_CHECK_STARTED, self._on_update_check_started)
        events.subscribe(EventType.UPDATE_CHECK_COMPLETED, self._on_update_check_completed)
        events.subscribe(EventType.UPDATE_CHECK_FAILED, self._on_update_check_failed)
        
        events.subscribe(EventType.UPDATE_STARTED, self._on_update_started)
        events.subscribe(EventType.UPDATE_PROGRESS, self._on_update_progress)
        events.subscribe(EventType.UPDATE_COMPLETED, self._on_update_completed)
        events.subscribe(EventType.UPDATE_FAILED, self._on_update_failed)
        
        # Minecraft events
        events.subscribe(EventType.MINECRAFT_LAUNCH_STARTED, self._on_minecraft_launch_started)
        events.subscribe(EventType.MINECRAFT_LAUNCH_COMPLETED, self._on_minecraft_launch_completed)
        events.subscribe(EventType.MINECRAFT_LAUNCH_FAILED, self._on_minecraft_launch_failed)
        
        # Configuration events
        events.subscribe(EventType.CONFIG_CHANGED, self._on_config_changed)
        
        # Setup logger callback
        self.launcher_core.logger.set_ui_callback(self._add_log)
    
    def _update_ui_from_config(self) -> None:
        """Update UI elements from current configuration."""
        if not self.launcher_core.config:
            return
        
        config = self.launcher_core.config
        
        # Update status frame with instance info
        instance_path = config.get_selected_instance_path()
        if instance_path:
            self.status_frame.update_directory("Instance: FFTClient")
        else:
            self.status_frame.update_directory("Instance: Not found")
        
        self.status_frame.update_version(config.current_version or "Unknown")
        
        # Initially disable the launch button until we check status
        self.button_frame.set_button_states({
            'launch': 'disabled'
        })
        
        # Log instance info
        if instance_path and instance_path.exists():
            self._add_log(f"Using instance directory: {instance_path}")
        else:
            self._add_log("Instance directory will be created automatically")
    
    def _add_log(self, message: str) -> None:
        """Add a log message to the UI.
        
        Args:
            message: Message to add
        """
        # Check if message already has a timestamp prefix from unified logging
        if message.startswith("[") and "] " in message[:12]:
            # Message already has timestamp, use as-is
            formatted_message = message
        else:
            # Add timestamp to message
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
        
        self.log_frame.add_log_message(formatted_message)
    
    # Update checking methods
    def _check_for_updates_on_startup(self) -> None:
        """Check for updates on startup to set initial button state."""
        self._add_log("Checking for updates...")
        self.button_frame.set_button_states({'launch': 'disabled'})
        
        # First check if instance is installed
        self._check_instance_status()
        
        # Then check for updates
        self.launcher_core.check_for_updates()
        
        # Also check for launcher self-updates (console only)
        if self.self_update_service:
            self.root.after(2000, self._check_for_launcher_updates_silent)
    
    def _check_instance_status(self) -> None:
        """Check if the instance is installed and up to date."""
        if not self.launcher_core.config or not self.launcher_core.update_service:
            self.instance_installed = False
            return
            
        # Use the update service to check if instance exists properly
        self.instance_installed = self.launcher_core.update_service.check_instance_exists()
        self._add_log(f"Instance status: {'Installed' if self.instance_installed else 'Not installed or incomplete'}")
        
        if not self.instance_installed:
            instance_path = self.launcher_core.config.get_selected_instance_path()
            if instance_path and instance_path.exists():
                self._add_log("Instance directory found but setup is incomplete")
            else:
                self._add_log("Instance directory not found")
    
    def _check_for_launcher_updates_silent(self) -> None:
        """Check for launcher self-updates silently (console logging only)."""
        if not self.self_update_service:
            return
        
        def check_async():
            if self.self_update_service:  # Type guard for mypy
                update_info = self.self_update_service.check_for_launcher_update()
                # Just log the result - no UI updates
                if update_info:
                    version = update_info.get('version', 'Unknown')
                    self.root.after(0, lambda: self._add_log(f"Launcher update available: v{version}"))
                    
                    # Check if auto-update is enabled for launcher updates
                    if self.launcher_core.config and self.launcher_core.config.auto_update:
                        self.root.after(0, lambda: self._add_log("Auto-update enabled - updating launcher automatically..."))
                        self.root.after(0, lambda: self._start_launcher_auto_update(update_info))
                    else:
                        self.root.after(0, lambda: self._add_log("Auto-update disabled - launcher update available but not installing automatically"))
                else:
                    self.root.after(0, lambda: self._add_log("Launcher is up to date"))
        
        # Run in a separate thread to avoid blocking UI
        import threading
        threading.Thread(target=check_async, daemon=True).start()
    
    def _start_launcher_auto_update(self, update_info) -> None:
        """Start automatic launcher self-update process."""
        if not self.self_update_service:
            return
            
        self._add_log("Auto-updating launcher...")
        self.progress_frame.update_progress("Updating launcher...", None, "loading")
        
        def update_async():
            if self.self_update_service:  # Type guard for mypy
                try:
                    success = self.self_update_service.download_and_install_update(update_info)
                    if success:
                        self.root.after(0, lambda: self._add_log("Launcher will restart to complete update..."))
                        self.root.after(0, lambda: self.progress_frame.update_progress("Restarting launcher...", 1.0, "success"))
                        # Exit the current launcher - the update script will restart it
                        self.root.after(3000, lambda: self.root.quit())
                    else:
                        self.root.after(0, lambda: self._add_log("Launcher update failed"))
                        self.root.after(0, lambda: self.progress_frame.update_progress("Launcher update failed", 0, "error"))
                except Exception as e:
                    self.root.after(0, lambda: self._add_log(f"Launcher update error: {e}"))
                    self.root.after(0, lambda: self.progress_frame.update_progress("Launcher update error", 0, "error"))
        
        # Run in a separate thread to avoid blocking UI
        import threading
        threading.Thread(target=update_async, daemon=True).start()
    
    def _on_self_update_progress(self, message: str, progress: Optional[float] = None, status_type: str = "info") -> None:
        """Handle self-update progress updates.
        
        Args:
            message: Progress message
            progress: Progress value (0.0 to 1.0), None for indeterminate
            status_type: Type of status ('info', 'success', 'warning', 'error', 'loading')
        """
        # Show self-update progress in the log
        self._add_log(f"Launcher Update: {message}")
        
        # Update progress bar if progress is provided
        if progress is not None:
            self.progress_frame.update_progress(f"Updating launcher: {message}", progress)
    
    # Main action handler
    def _handle_launch_action(self) -> None:
        """Handle the main launch/update action."""
        current_button_text = self.button_frame.launch_button.cget("text")
        
        if current_button_text == "Launch":
            # Launch Minecraft and close the app
            self._launch_minecraft()
        else:
            # Button says "Update" - perform update then launch if checkbox is checked
            self._add_log("Starting update...")
            self.button_frame.set_button_states({'launch': 'disabled'})
            self.launcher_core.perform_update()
    
    def _launch_minecraft(self) -> None:
        """Launch Minecraft launcher."""
        # First validate that Minecraft launcher is available
        if not self.launcher_core.minecraft_service or not self.launcher_core.validate_minecraft_installation():
            self._add_log("Error: Minecraft launcher not found")
            UIUtils.show_error_dialog(
                "Minecraft Launcher Not Found", 
                "The Minecraft launcher could not be found on your system.\n\n"
                "Please install the official Minecraft launcher from:\n"
                "https://www.minecraft.net/en-us/download\n\n"
                "After installation, restart this launcher."
            )
            self.button_frame.set_button_states({'launch': 'normal'})
            return
            
        self.launcher_core.launch_minecraft(self._on_minecraft_launched)
    
    def _on_minecraft_launched(self, success: bool) -> None:
        """Handle Minecraft launcher result.
        
        Args:
            success: Whether launch was successful
        """
        if success:
            self._add_log("Minecraft launcher opened successfully")
            # Close the launcher after successfully opening Minecraft
            self.root.after(1000, self.close)  # Wait 1 second then close
        else:
            self._add_log("Failed to open Minecraft launcher")
            self.button_frame.set_button_states({'launch': 'normal'})
    
    def _on_theme_toggle(self) -> None:
        """Handle theme toggle."""
        if self.launcher_core.config:
            current_mode = ctk.get_appearance_mode()
            self.launcher_core.config.night_mode = (current_mode == "Dark")
            self.launcher_core.save_config()
    
    # Event handlers
    def _on_update_check_started(self, data=None) -> None:
        """Handle update check started."""
        self.progress_frame.update_progress("Checking for updates...")
        self.button_frame.set_button_states({
            'check': 'disabled',
            'update': 'disabled'
        })
    
    def _on_update_check_completed(self, update_info: UpdateInfo) -> None:
        """Handle update check completed."""
        self.progress_frame.reset_progress()
        self.update_info = update_info
        
        # Update last check time
        self.status_frame.update_last_check(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Determine what the button should show based on instance and update status
        if not self.instance_installed:
            # Instance not installed - button should be "Update" to install everything
            self.needs_update = True
            self.button_frame.set_launch_button_text("Update")
            self.button_frame.set_launch_button_color("#ffc107", "#d39e00")  # Yellow for update
            self.progress_frame.update_progress("Instance not installed - click Update to install", 0, "warning")
            self._add_log("Instance not installed - update needed")
        elif update_info.updates_available:
            # Instance installed but modpack needs update
            self.needs_update = True
            self.button_frame.set_launch_button_text("Update")
            self.button_frame.set_launch_button_color("#ffc107", "#d39e00")  # Yellow for update
            self.progress_frame.update_progress(f"New version available: {update_info.latest_version}", 0, "warning")
            self._add_log(f"Modpack update available: v{update_info.latest_version}")
        else:
            # Everything is up to date - button should be "Launch"
            self.needs_update = False
            self.button_frame.set_launch_button_text("Launch")
            self.button_frame.set_launch_button_color("#28a745", "#1e7e34")  # Green for launch
            self.progress_frame.update_progress(f"Up to date (Version: {update_info.latest_version})", 1.0, "success")
            self._add_log("Ready to launch")
        
        # Enable the button
        self.button_frame.set_button_states({'launch': 'normal'})
        
        # Auto-update on startup if enabled and update is needed
        if (self.launcher_core.config and self.launcher_core.config.auto_update and 
            self.needs_update):
            self._add_log("Auto-update enabled - starting update automatically...")
            self.root.after(1000, self._handle_launch_action)
    
    def _on_update_check_failed(self, error: str) -> None:
        """Handle update check failed."""
        self.progress_frame.reset_progress()
        self.progress_frame.update_progress("Error checking updates", 0, "error")
        
        # If we can't check for updates but instance is installed, allow launch
        if self.instance_installed:
            self.button_frame.set_launch_button_text("Launch")
            self.button_frame.set_launch_button_color("#28a745", "#1e7e34")  # Green for launch
            self.button_frame.set_button_states({'launch': 'normal'})
            self._add_log("Update check failed but instance is available - ready to launch")
        else:
            # Can't check updates and no instance - keep disabled
            self.button_frame.set_button_states({'launch': 'disabled'})
            self._add_log("Update check failed and no instance available")
            
        UIUtils.show_error_dialog("Update Check Failed", f"Failed to check for updates:\n{error}")
    
    def _on_update_started(self, data=None) -> None:
        """Handle update started."""
        self.progress_frame.update_progress("Starting update...")
        self.button_frame.set_button_states({'launch': 'disabled'})
    
    def _on_update_progress(self, message: str) -> None:
        """Handle update progress."""
        self.progress_frame.update_progress(message)
    
    def _on_update_completed(self, data=None) -> None:
        """Handle update completed."""
        self.progress_frame.update_progress("Update completed successfully", 1.0, "success")
        
        # Update version display
        if self.launcher_core.config:
            self.status_frame.update_version(self.launcher_core.config.current_version or "Unknown")
        
        # Update instance status since update is complete
        self.instance_installed = True
        self.needs_update = False
        
        # Reset button to launch mode
        self.button_frame.set_launch_button_text("Launch")
        self.button_frame.set_launch_button_color("#28a745", "#1e7e34")  # Green for launch
        
        # Check if auto-launch is enabled
        if self.launch_after_update_var.get():
            self._add_log("Launching Minecraft...")
            self.root.after(1000, self._launch_minecraft)  # Wait 1 second then launch
        else:
            self._add_log("Update completed - ready to launch")
            self.button_frame.set_button_states({'launch': 'normal'})
    
    def _on_update_failed(self, error: str) -> None:
        """Handle update failed."""
        self.progress_frame.reset_progress()
        self.progress_frame.update_progress("Update failed", 0, "error")
        
        # Reset button state based on current status
        if self.needs_update:
            self.button_frame.set_launch_button_text("Update")
            self.button_frame.set_launch_button_color("#ffc107", "#d39e00")  # Yellow for update
        else:
            self.button_frame.set_launch_button_text("Launch")
            self.button_frame.set_launch_button_color("#28a745", "#1e7e34")  # Green for launch
            
        self.button_frame.set_button_states({'launch': 'normal'})
        UIUtils.show_error_dialog("Update Failed", f"Failed to update files:\n{error}")
    
    def _on_minecraft_launch_started(self, data=None) -> None:
        """Handle Minecraft launcher started."""
        self.progress_frame.update_progress("Opening Minecraft launcher...")
    
    def _on_minecraft_launch_completed(self, data=None) -> None:
        """Handle Minecraft launcher completed."""
        self.progress_frame.update_progress("Minecraft launcher opened successfully", 1.0)
    
    def _on_minecraft_launch_failed(self, error: str) -> None:
        """Handle Minecraft launcher failed."""
        self.progress_frame.reset_progress()
        UIUtils.show_error_dialog("Launch Failed", f"Failed to open Minecraft launcher:\n{error}")
    
    def _on_config_changed(self, data=None) -> None:
        """Handle configuration changed."""
        self._update_ui_from_config()
    
    def run(self) -> None:
        """Run the main event loop."""
        try:
            self.root.mainloop()
        finally:
            self.close()
    
    def close(self) -> None:
        """Close the application."""
        try:
            # Close settings window if open
            if self.settings_window and self.settings_window.is_open():
                self.settings_window.close()
        except Exception:
            pass  # Ignore errors during cleanup
        
        try:
            # Shutdown launcher core
            self.launcher_core.shutdown()
        except Exception:
            pass  # Ignore errors during cleanup
        
        try:
            # Destroy main window
            if self.root:
                self.root.quit()
                self.root.destroy()
        except Exception:
            pass  # Ignore errors during cleanup
