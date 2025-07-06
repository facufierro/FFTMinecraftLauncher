"""Settings window for the FFT Minecraft Launcher."""

import customtkinter as ctk
from typing import Optional
from ..core.launcher import LauncherCore
from ..core.events import EventType
from ..utils.ui_utils import UIUtils


class SettingsWindow:
    """Settings window for configuring the launcher."""
    
    def __init__(self, parent: ctk.CTk, launcher_core: LauncherCore):
        """Initialize the settings window.
        
        Args:
            parent: Parent window
            launcher_core: The launcher core instance
        """
        self.parent = parent
        self.launcher_core = launcher_core
        self.window: Optional[ctk.CTkToplevel] = None
        
        # Initialize entry widgets (will be set in _setup_ui)
        self.instance_combobox: Optional[ctk.CTkComboBox] = None
        self.install_neoforge_button: Optional[ctk.CTkButton] = None
        
        self._create_window()
    
    def _create_window(self) -> None:
        """Create the settings window."""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Modpack Settings")
        UIUtils.center_window(self.window, 600, 400)
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        
        # Setup UI
        self._setup_ui()
        self._load_current_settings()
    
    def _setup_ui(self) -> None:
        """Setup the settings UI."""
        if not self.window:
            return
        
        # Main frame
        main_frame = ctk.CTkFrame(self.window, corner_radius=10)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(20, 20))
        
        # Settings form
        form_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Checkboxes
        checkbox_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        checkbox_frame.pack(fill="x", pady=(10, 0))
        
        
        # Check on startup
        self.check_startup_var = ctk.BooleanVar()
        self.check_startup_cb = ctk.CTkCheckBox(
            checkbox_frame,
            text="Check for updates on startup",
            variable=self.check_startup_var,
            command=self._on_check_startup_changed
        )
        self.check_startup_cb.pack(anchor="w", pady=(0, 5))
        
        # Auto update
        self.auto_update_var = ctk.BooleanVar()
        self.auto_update_cb = ctk.CTkCheckBox(
            checkbox_frame,
            text="Auto-update without asking",
            variable=self.auto_update_var,
            command=self._on_auto_update_changed
        )
        self.auto_update_cb.pack(anchor="w", pady=(0, 10))
        
        # Button frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Buttons
        self.save_button = ctk.CTkButton(
            button_frame, text="Save", command=self._save_settings
        )
        self.save_button.pack(side="right", padx=(10, 0))
        
        self.cancel_button = ctk.CTkButton(
            button_frame, text="Cancel", command=self.close
        )
        self.cancel_button.pack(side="right")
        
        self.reset_button = ctk.CTkButton(
            button_frame, text="Reset to Defaults", command=self._reset_settings
        )
        self.reset_button.pack(side="left")
    
    def _load_current_settings(self) -> None:
        """Load current settings into the UI."""
        if not self.launcher_core.config:
            return
        
        config = self.launcher_core.config
        
        # Load checkbox settings
        self.check_startup_var.set(config.check_on_startup)
        self.auto_update_var.set(config.auto_update)
    
    def _on_setting_changed(self, setting_name: str, value: str) -> None:
        """Handle setting change.
        
        Args:
            setting_name: Name of the setting
            value: New value
        """
        if not self.launcher_core.config:
            return
        
        # Update config
        setattr(self.launcher_core.config, setting_name, value.strip())
    
    def _on_check_startup_changed(self) -> None:
        """Handle check on startup setting change."""
        if self.launcher_core.config:
            self.launcher_core.config.check_on_startup = self.check_startup_var.get()
    
    def _on_auto_update_changed(self) -> None:
        """Handle auto update setting change."""
        if self.launcher_core.config:
            self.launcher_core.config.auto_update = self.auto_update_var.get()
    
    def _save_settings(self) -> None:
        """Save settings and close window."""
        try:
            # Validate settings
            if self.launcher_core.config:
                errors = self.launcher_core.config.validate()
                if errors:
                    error_msg = "Settings validation failed:\n" + "\n".join(errors)
                    UIUtils.show_error_dialog("Invalid Settings", error_msg)
                    return
            
            # Save configuration
            self.launcher_core.save_config()
            
            # Close window silently
            self.close()
            
        except Exception as e:
            UIUtils.show_error_dialog("Save Failed", f"Failed to save settings:\n{str(e)}")
    
    def _reset_settings(self) -> None:
        """Reset settings to defaults."""
        if not UIUtils.ask_yes_no(
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?"
        ):
            return
        
        # Create default config
        from ..models.config import LauncherConfig
        default_config = LauncherConfig()
        
        # Update launcher config
        if self.launcher_core.config:
            for key, value in default_config.__dict__.items():
                setattr(self.launcher_core.config, key, value)
        
        # Update UI
        self._load_current_settings()
        
        UIUtils.show_info_dialog("Reset Complete", "Settings have been reset to defaults.")
    
    def _clear_entries(self) -> None:
        """Clear all entry widgets."""
        # No longer needed since we don't have text entries
        pass
    
    def is_open(self) -> bool:
        """Check if the settings window is open.
        
        Returns:
            True if window is open, False otherwise.
        """
        return self.window is not None and self.window.winfo_exists()
    
    def close(self) -> None:
        """Close the settings window."""
        if self.window:
            self.window.destroy()
            self.window = None
