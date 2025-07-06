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
        
        # Instance Selection
        self._create_instance_selection(form_frame, 0)
        
        # NeoForge Installation
        self._create_neoforge_section(form_frame, 1)
        
        # Checkboxes
        checkbox_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        checkbox_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        
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
    
    def _create_instance_selection(self, parent, row: int) -> None:
        """Create the instance selection section.
        
        Args:
            parent: Parent widget
            row: Grid row
        """
        # Label
        label = ctk.CTkLabel(parent, text="Minecraft Instance:")
        label.grid(row=row, column=0, sticky="w", pady=(0, 10))
        
        # Get available instances
        instances = self.launcher_core.minecraft_service.get_available_instances()
        
        # Instance selection combobox
        self.instance_combobox = ctk.CTkComboBox(
            parent, 
            values=instances if instances else ["No instances found"],
            width=300,
            command=self._on_instance_selected
        )
        self.instance_combobox.grid(row=row, column=1, sticky="ew", padx=(10, 0), pady=(0, 10))
        
        # Refresh button
        refresh_button = ctk.CTkButton(
            parent, 
            text="🔄",
            width=30,
            command=self._refresh_instances
        )
        refresh_button.grid(row=row, column=2, sticky="w", padx=(5, 0), pady=(0, 10))
        
        # Configure grid
        parent.columnconfigure(1, weight=1)
    
    def _create_neoforge_section(self, parent, row: int) -> None:
        """Create the NeoForge installation section.
        
        Args:
            parent: Parent widget
            row: Grid row
        """
        # NeoForge status label
        self.neoforge_status_label = ctk.CTkLabel(parent, text="NeoForge Status:")
        self.neoforge_status_label.grid(row=row, column=0, sticky="w", pady=(0, 10))
        
        # Install/Status frame
        install_frame = ctk.CTkFrame(parent, fg_color="transparent")
        install_frame.grid(row=row, column=1, columnspan=2, sticky="ew", padx=(10, 0), pady=(0, 10))
        
        # Status display
        self.neoforge_status_display = ctk.CTkLabel(
            install_frame, 
            text="Select an instance first",
            text_color="gray"
        )
        self.neoforge_status_display.pack(side="left", padx=(0, 10))
        
        # Install button
        self.install_neoforge_button = ctk.CTkButton(
            install_frame,
            text="Install NeoForge",
            command=self._install_neoforge,
            state="disabled"
        )
        self.install_neoforge_button.pack(side="right")
    
    def _refresh_instances(self) -> None:
        """Refresh the list of available instances."""
        instances = self.launcher_core.minecraft_service.get_available_instances()
        
        if instances:
            self.instance_combobox.configure(values=instances)
            # Keep current selection if it's still valid
            current = self.instance_combobox.get()
            if current not in instances:
                self.instance_combobox.set("")
        else:
            self.instance_combobox.configure(values=["No instances found"])
            self.instance_combobox.set("No instances found")
        
        self._update_neoforge_status()
    
    def _on_instance_selected(self, instance_name: str) -> None:
        """Handle instance selection.
        
        Args:
            instance_name: Name of the selected instance
        """
        if instance_name and instance_name != "No instances found":
            self.launcher_core.config.selected_instance = instance_name
            self.install_neoforge_button.configure(state="normal")
            # Save config immediately when instance changes
            self.launcher_core.save_config()
            # Emit config changed event to update main UI
            self.launcher_core.events.emit(EventType.CONFIG_CHANGED)
        else:
            self.launcher_core.config.selected_instance = ""
            self.install_neoforge_button.configure(state="disabled")
            self.launcher_core.save_config()
            self.launcher_core.events.emit(EventType.CONFIG_CHANGED)
        
        self._update_neoforge_status()
    
    def _update_neoforge_status(self) -> None:
        """Update the NeoForge installation status display."""
        if not self.launcher_core.config.selected_instance:
            self.neoforge_status_display.configure(
                text="Select an instance first",
                text_color="gray"
            )
            return
        
        instance_name = self.launcher_core.config.selected_instance
        is_installed = self.launcher_core.minecraft_service.is_neoforge_installed(instance_name)
        
        if is_installed:
            self.neoforge_status_display.configure(
                text="✓ NeoForge installed",
                text_color="green"
            )
            self.install_neoforge_button.configure(text="Reinstall NeoForge")
        else:
            self.neoforge_status_display.configure(
                text="✗ NeoForge not installed",
                text_color="red"
            )
            self.install_neoforge_button.configure(text="Install NeoForge")
    
    def _install_neoforge(self) -> None:
        """Install NeoForge to the selected instance."""
        if not self.launcher_core.config.selected_instance:
            UIUtils.show_error_dialog("No Instance Selected", "Please select a Minecraft instance first.")
            return
        
        instance_name = self.launcher_core.config.selected_instance
        
        # Show confirmation dialog
        if not UIUtils.ask_yes_no(
            "Install NeoForge",
            f"Install NeoForge 21.1.186 for Minecraft 1.21.1 to instance '{instance_name}'?\n\n"
            "This will modify the instance to add NeoForge support."
        ):
            return
        
        # Disable button during installation
        self.install_neoforge_button.configure(state="disabled", text="Installing...")
        self.neoforge_status_display.configure(text="Installing NeoForge...", text_color="orange")
        
        # Perform installation in a separate thread
        import threading
        
        def install_thread():
            try:
                success = self.launcher_core.minecraft_service.install_neoforge_to_instance(instance_name)
                
                # Update UI on main thread
                self.window.after(0, lambda: self._installation_completed(success))
                
            except Exception as e:
                self.window.after(0, lambda: self._installation_completed(False, str(e)))
        
        threading.Thread(target=install_thread, daemon=True).start()
    
    def _installation_completed(self, success: bool, error: str = None) -> None:
        """Handle installation completion.
        
        Args:
            success: Whether installation was successful
            error: Error message if installation failed
        """
        self.install_neoforge_button.configure(state="normal")
        
        if success:
            UIUtils.show_info_dialog(
                "Installation Complete",
                "NeoForge has been successfully installed to the selected instance."
            )
        else:
            error_msg = f"NeoForge installation failed"
            if error:
                error_msg += f":\n{error}"
            UIUtils.show_error_dialog("Installation Failed", error_msg)
        
        self._update_neoforge_status()
    
    def _load_current_settings(self) -> None:
        """Load current settings into the UI."""
        if not self.launcher_core.config:
            return
        
        config = self.launcher_core.config
        
        # Load instance selection
        if self.instance_combobox and config.selected_instance:
            self.instance_combobox.set(config.selected_instance)
            self.install_neoforge_button.configure(state="normal")
        
        # Load checkbox settings
        self.check_startup_var.set(config.check_on_startup)
        self.auto_update_var.set(config.auto_update)
        
        # Update NeoForge status
        self._update_neoforge_status()
    
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
        
        # Refresh instances and reload settings
        self._refresh_instances()
        
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
