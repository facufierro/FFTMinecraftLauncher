"""Version check dialog for launcher updates."""

import customtkinter as ctk
from typing import Optional, Callable
from ..utils.ui_utils import UIUtils


class VersionCheckDialog:
    """Dialog for showing launcher version update information."""
    
    def __init__(self, parent, current_version: str, latest_version: str, 
                 on_update: Optional[Callable] = None, on_cancel: Optional[Callable] = None,
                 github_service=None, download_url: Optional[str] = None):
        """Initialize the version check dialog.
        
        Args:
            parent: Parent window
            current_version: Current launcher version
            latest_version: Latest available version
            on_update: Callback for update button
            on_cancel: Callback for cancel button
            github_service: GitHub service for downloading updates
            download_url: URL to download the launcher update
        """
        self.parent = parent
        self.current_version = current_version
        self.latest_version = latest_version
        self.on_update = on_update
        self.on_cancel = on_cancel
        self.github_service = github_service
        self.download_url = download_url
        self.result = None
        
        self._create_dialog()
    
    def _create_dialog(self):
        """Create and show the dialog."""
        # Create dialog window
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("Launcher Update Available")
        self.dialog.geometry("550x350")  # Increased height for progress bar
        self.dialog.resizable(False, False)
        
        # Set window icon
        UIUtils.set_window_icon(self.dialog)
        
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
            text="Launcher Update Available",
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
        
        # Progress frame (hidden by default)
        self.progress_frame = ctk.CTkFrame(main_frame)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=300,
            height=20
        )
        self.progress_bar.pack(pady=(10, 5))
        self.progress_bar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=(5, 10))
        
        # Buttons frame
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10)
        
        # Update button (opens updater and closes launcher)
        self.update_button = ctk.CTkButton(
            button_frame,
            text="Update",
            width=120,
            height=35,
            command=self._on_update_clicked,
            fg_color="#2B8D2B",
            hover_color="#1F6A1F"
        )
        self.update_button.pack(side="left", padx=(0, 10))
        
        # Not Now button (closes dialog)
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Not Now",
            width=120,
            height=35,
            command=self._on_cancel_clicked,
            fg_color="#5A5A5A",
            hover_color="#494949"
        )
        self.cancel_button.pack(side="right")
        
        # Initialize update state
        self.is_updating = False
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_window_close)
        
        # Focus the dialog
        self.dialog.focus()
    
    def _on_update_clicked(self):
        """Handle update button click - downloads new version and opens updater."""
        import subprocess
        import sys
        from pathlib import Path
        
        try:
            # Set updating state
            self.is_updating = True
            
            # Show progress frame and update button state
            self.progress_frame.pack(fill="x", padx=10, pady=(0, 20))
            self.update_button.configure(text="Updating...", state="disabled")
            self.cancel_button.configure(state="disabled")
            self.status_label.configure(text="Preparing download...")
            self.progress_bar.set(0.1)
            self.dialog.update()
            
            # Download the new launcher version as Launcher.update
            self._download_launcher_update()
            
            # Get the path to the updater executable
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller executable
                current_dir = Path(sys.executable).parent
                updater_path = current_dir / "Updater.exe"
            else:
                # Running as Python script
                current_dir = Path(__file__).parent.parent.parent.parent  # Go up to project root
                updater_path = current_dir / "dist" / "Updater.exe"
            
            if updater_path.exists():
                # Update progress
                self.status_label.configure(text="Starting updater...")
                self.progress_bar.set(0.9)
                self.dialog.update()
                
                # Start the updater
                subprocess.Popen([str(updater_path)], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                
                # Final progress
                self.status_label.configure(text="Update complete! Closing launcher...")
                self.progress_bar.set(1.0)
                self.dialog.update()
                
                # Brief pause to show completion
                self.dialog.after(1000, self._complete_update)
            else:
                # Show error if updater not found
                self._reset_ui()
                UIUtils.show_error_dialog("Updater Not Found", 
                                         f"Could not find Updater.exe at:\n{updater_path}")
        except Exception as e:
            self._reset_ui()
            UIUtils.show_error_dialog("Error Opening Updater", 
                                     f"Failed to open updater: {str(e)}")
    
    def _complete_update(self):
        """Complete the update process."""
        import sys
        
        # Close the dialog
        self.result = "update"
        self.dialog.destroy()
        
        # Exit the launcher completely
        sys.exit(0)
    
    def _reset_ui(self):
        """Reset UI to initial state on error."""
        self.is_updating = False
        self.progress_frame.pack_forget()
        self.update_button.configure(text="Update", state="normal")
        self.cancel_button.configure(state="normal")
    
    def _download_launcher_update(self):
        """Download the new launcher version as Launcher.update."""
        import sys
        import requests
        from pathlib import Path
        
        # Determine the download path - same directory as the current executable
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            current_dir = Path(sys.executable).parent
            download_path = current_dir / "FFTLauncher.update"
        else:
            # Running as Python script
            current_dir = Path(__file__).parent.parent.parent.parent  # Go up to project root
            download_path = current_dir / "dist" / "FFTLauncher.update"
        
        # Update progress
        self.status_label.configure(text="Fetching release information...")
        self.progress_bar.set(0.2)
        self.dialog.update()
        
        # Get the latest release download URL
        api_url = "https://api.github.com/repos/facufierro/FFTMinecraftLauncher/releases/latest"
        response = requests.get(api_url)
        response.raise_for_status()
        
        release_data = response.json()
        download_url = None
        
        # Find FFTLauncher.exe in assets
        for asset in release_data.get('assets', []):
            if asset['name'] == 'FFTLauncher.exe':
                download_url = asset['browser_download_url']
                break
        
        if not download_url:
            raise Exception("FFTLauncher.exe not found in latest release")
        
        # Update progress
        self.status_label.configure(text="Starting download...")
        self.progress_bar.set(0.3)
        self.dialog.update()
        
        # Download the file with progress tracking
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # Update progress bar (30% to 80% for download)
                    if total_size > 0:
                        download_progress = downloaded_size / total_size
                        progress_value = 0.3 + (download_progress * 0.5)  # 30% to 80%
                        self.progress_bar.set(progress_value)
                        
                        # Update status with download info
                        mb_downloaded = downloaded_size / (1024 * 1024)
                        mb_total = total_size / (1024 * 1024) if total_size > 0 else 0
                        if mb_total > 0:
                            self.status_label.configure(text=f"Downloading... {mb_downloaded:.1f} MB / {mb_total:.1f} MB")
                        else:
                            self.status_label.configure(text=f"Downloading... {mb_downloaded:.1f} MB")
                        
                        self.dialog.update()
        
        # Download complete
        self.status_label.configure(text="Download complete!")
        self.progress_bar.set(0.8)
        self.dialog.update()
    
    def _on_window_close(self):
        """Handle window close button - prevent closing during update."""
        if not self.is_updating:
            self._on_cancel_clicked()
    
    def _on_cancel_clicked(self):
        """Handle cancel button click."""
        if self.is_updating:
            return  # Don't allow cancel during update
        
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
                             on_cancel: Optional[Callable] = None,
                             github_service=None, download_url: Optional[str] = None) -> str:
    """Show version check dialog.
    
    Args:
        parent: Parent window
        current_version: Current launcher version
        latest_version: Latest available version
        on_update: Callback for update button
        on_cancel: Callback for cancel button
        github_service: GitHub service for downloading updates
        download_url: URL to download the launcher update
        
    Returns:
        "update" if user chose to update, "cancel" otherwise
    """
    dialog = VersionCheckDialog(parent, current_version, latest_version, on_update, on_cancel, github_service, download_url)
    return dialog.show()
