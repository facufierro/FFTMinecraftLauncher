"""Settings window for the FFT Minecraft Launcher."""

import customtkinter as ctk
from typing import Optional
from ..core.launcher import LauncherCore
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
        self.minecraft_dir_entry: Optional[ctk.CTkEntry] = None
        self.minecraft_executable_entry: Optional[ctk.CTkEntry] = None
        self.github_repo_entry: Optional[ctk.CTkEntry] = None
        
        self._create_window()
    
    def _create_window(self) -> None:
        """Create the settings window."""
        self.window = ctk.CTkToplevel(self.parent)
        self.window.title("Launcher Settings")
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
        
        # Minecraft Directory
        self._create_setting_group(
            form_frame, "Minecraft Directory", "minecraft_dir", 0
        )
        
        # Minecraft Executable
        self._create_setting_group(
            form_frame, "Minecraft Executable", "minecraft_executable", 1
        )
        
        # GitHub Repository
        self._create_setting_group(
            form_frame, "GitHub Repository", "github_repo", 2
        )
        
        # Checkboxes
        checkbox_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        checkbox_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
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
    
    def _create_setting_group(self, parent, label_text: str, setting_name: str, row: int) -> None:
        """Create a setting group with label and entry.
        
        Args:
            parent: Parent widget
            label_text: Label text
            setting_name: Setting attribute name
            row: Grid row
        """
        # Label
        label = ctk.CTkLabel(parent, text=f"{label_text}:")
        label.grid(row=row, column=0, sticky="w", pady=(0, 10))
        
        # Entry
        entry = ctk.CTkEntry(parent, width=250)
        entry.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=(0, 10))
        
        # Store reference
        setattr(self, f"{setting_name}_entry", entry)
        
        # Configure grid
        parent.columnconfigure(1, weight=1)
        
        # Bind change event
        entry.bind('<KeyRelease>', lambda e: self._on_setting_changed(setting_name, entry.get()))
    
    def _load_current_settings(self) -> None:
        """Load current settings into the UI."""
        if not self.launcher_core.config:
            return
        
        config = self.launcher_core.config
        
        # Load text settings
        if self.minecraft_dir_entry:
            self.minecraft_dir_entry.insert(0, config.minecraft_dir)
        if self.minecraft_executable_entry:
            self.minecraft_executable_entry.insert(0, config.minecraft_executable)
        if self.github_repo_entry:
            self.github_repo_entry.insert(0, config.github_repo)
        
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
            
            # Show success message
            UIUtils.show_info_dialog("Settings Saved", "Settings have been saved successfully.")
            
            # Close window
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
        self._clear_entries()
        self._load_current_settings()
        
        UIUtils.show_info_dialog("Reset Complete", "Settings have been reset to defaults.")
    
    def _clear_entries(self) -> None:
        """Clear all entry widgets."""
        if self.minecraft_dir_entry:
            self.minecraft_dir_entry.delete(0, 'end')
        if self.minecraft_executable_entry:
            self.minecraft_executable_entry.delete(0, 'end')
        if self.github_repo_entry:
            self.github_repo_entry.delete(0, 'end')
    
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
