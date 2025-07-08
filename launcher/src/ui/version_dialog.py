"""Version check dialog for launcher updates."""

import customtkinter as ctk
from typing import Optional, Callable


class VersionCheckDialog:
    """Dialog for showing launcher version update information."""
    
    def __init__(self, parent, current_version: str, latest_version: str, 
                 on_update: Optional[Callable] = None, on_cancel: Optional[Callable] = None):
        """Initialize the version check dialog.
        
        Args:
            parent: Parent window
            current_version: Current launcher version
            latest_version: Latest available version
            on_update: Callback for update button
            on_cancel: Callback for cancel button
        """
        self.parent = parent
        self.current_version = current_version
        self.latest_version = latest_version
        self.on_update = on_update
        self.on_cancel = on_cancel
        self.result = None
        
        self._create_dialog()
    
    def _create_dialog(self):
        """Create and show the dialog."""
        # Create dialog window
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Launcher Update Available")
        self.dialog.geometry("450x250")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center on parent
        self.dialog.update_idletasks()
        x = (self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 
             (self.dialog.winfo_width() // 2))
        y = (self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 
             (self.dialog.winfo_height() // 2))
        self.dialog.geometry(f"+{x}+{y}")
        
        # Main frame
        main_frame = ctk.CTkFrame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="🔄 Launcher Update Available",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # Version info
        version_frame = ctk.CTkFrame(main_frame)
        version_frame.pack(fill="x", padx=10, pady=(0, 20))
        
        current_label = ctk.CTkLabel(
            version_frame,
            text=f"Current Version: {self.current_version}",
            font=ctk.CTkFont(size=14)
        )
        current_label.pack(pady=(10, 5))
        
        latest_label = ctk.CTkLabel(
            version_frame,
            text=f"Latest Version: {self.latest_version}",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        latest_label.pack(pady=(5, 10))
        
        # Message
        message_label = ctk.CTkLabel(
            main_frame,
            text="A new version of the launcher is available.\nWould you like to update now?",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        message_label.pack(pady=(0, 20))
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10)
        
        # Update button
        update_button = ctk.CTkButton(
            button_frame,
            text="Update Now",
            width=120,
            height=35,
            command=self._on_update_clicked,
            fg_color="#2B8D2B",
            hover_color="#1F6A1F"
        )
        update_button.pack(side="left", padx=(0, 10))
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Not Now",
            width=120,
            height=35,
            command=self._on_cancel_clicked,
            fg_color="#8B4513",
            hover_color="#6B3410"
        )
        cancel_button.pack(side="right")
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel_clicked)
        
        # Focus the dialog
        self.dialog.focus()
    
    def _on_update_clicked(self):
        """Handle update button click."""
        self.result = "update"
        if self.on_update:
            self.on_update()
        self.dialog.destroy()
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        self.result = "cancel"
        if self.on_cancel:
            self.on_cancel()
        self.dialog.destroy()
    
    def show(self) -> str:
        """Show the dialog and wait for result.
        
        Returns:
            "update" if user chose to update, "cancel" otherwise
        """
        self.dialog.wait_window()
        return self.result or "cancel"


def show_version_check_dialog(parent, current_version: str, latest_version: str,
                             on_update: Optional[Callable] = None, 
                             on_cancel: Optional[Callable] = None) -> str:
    """Show version check dialog.
    
    Args:
        parent: Parent window
        current_version: Current launcher version
        latest_version: Latest available version
        on_update: Callback for update button
        on_cancel: Callback for cancel button
        
    Returns:
        "update" if user chose to update, "cancel" otherwise
    """
    dialog = VersionCheckDialog(parent, current_version, latest_version, on_update, on_cancel)
    return dialog.show()
