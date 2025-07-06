"""UI components for the FFT Minecraft Launcher."""

import customtkinter as ctk
from typing import Callable, Optional
from ..utils.ui_utils import UIUtils


class StatusFrame(ctk.CTkFrame):
    """Frame for displaying status information."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the status frame.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, corner_radius=8, **kwargs)
        
        self.columnconfigure(1, weight=1)
        
        # Status labels
        self.dir_title, self.dir_label = UIUtils.create_info_frame(
            self, "Local Directory", "Not set", 0
        )
        self.lastcheck_title, self.lastcheck_label = UIUtils.create_info_frame(
            self, "Last Check", "Never", 1
        )
        self.version_title, self.version_label = UIUtils.create_info_frame(
            self, "Current Version", "Unknown", 2
        )
    
    
    def update_directory(self, directory: str) -> None:
        """Update directory display."""
        self.dir_label.configure(text=directory)
    
    def update_last_check(self, timestamp: str) -> None:
        """Update last check timestamp."""
        self.lastcheck_label.configure(text=timestamp)
    
    def update_version(self, version: str) -> None:
        """Update current version display."""
        self.version_label.configure(text=version)


class ProgressFrame(ctk.CTkFrame):
    """Frame for displaying progress information."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the progress frame.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, corner_radius=8, **kwargs)
        
        self.columnconfigure(0, weight=1)
        
        # Progress elements
        self.progress_label = ctk.CTkLabel(self, text="Ready")
        self.progress_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.progress_bar.set(0)
    
    def update_progress(self, message: str, progress: Optional[float] = None) -> None:
        """Update progress display.
        
        Args:
            message: Progress message
            progress: Progress value (0.0 to 1.0), None to show indeterminate
        """
        self.progress_label.configure(text=message)
        
        if progress is not None:
            self.progress_bar.stop()
            self.progress_bar.set(progress)
        else:
            self.progress_bar.start()
    
    def reset_progress(self) -> None:
        """Reset progress to initial state."""
        self.progress_bar.stop()
        self.progress_bar.set(0)
        self.progress_label.configure(text="Ready")


class ButtonFrame(ctk.CTkFrame):
    """Frame for action buttons."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the button frame.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        # Create buttons
        self.check_button = ctk.CTkButton(
            self, text="Check for Updates", width=120
        )
        self.check_button.grid(row=0, column=0, padx=(0, 10))
        
        self.update_button = ctk.CTkButton(
            self, text="Update Files", width=120, state="disabled"
        )
        self.update_button.grid(row=0, column=1, padx=(0, 10))
        
        self.launch_button = ctk.CTkButton(
            self, text="Open Minecraft Launcher", width=140, state="disabled"
        )
        self.launch_button.grid(row=0, column=2, padx=(0, 10))
        
        self.force_button = ctk.CTkButton(
            self, text="Force Update", width=120
        )
        self.force_button.grid(row=0, column=3, padx=(0, 10))
        
        self.settings_button = ctk.CTkButton(
            self, text="Settings", width=120
        )
        self.settings_button.grid(row=0, column=4)
    
    def set_button_callbacks(self, callbacks: dict) -> None:
        """Set callbacks for buttons.
        
        Args:
            callbacks: Dictionary mapping button names to callback functions
        """
        if 'check' in callbacks:
            self.check_button.configure(command=callbacks['check'])
        if 'update' in callbacks:
            self.update_button.configure(command=callbacks['update'])
        if 'launch' in callbacks:
            self.launch_button.configure(command=callbacks['launch'])
        if 'force' in callbacks:
            self.force_button.configure(command=callbacks['force'])
        if 'settings' in callbacks:
            self.settings_button.configure(command=callbacks['settings'])
    
    def set_button_states(self, states: dict) -> None:
        """Set button states.
        
        Args:
            states: Dictionary mapping button names to states ('normal'/'disabled')
        """
        if 'check' in states:
            self.check_button.configure(state=states['check'])
        if 'update' in states:
            self.update_button.configure(state=states['update'])
        if 'launch' in states:
            self.launch_button.configure(state=states['launch'])
        if 'force' in states:
            self.force_button.configure(state=states['force'])
        if 'settings' in states:
            self.settings_button.configure(state=states['settings'])


class LogFrame(ctk.CTkFrame):
    """Frame for displaying log messages."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the log frame.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, corner_radius=8, **kwargs)
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Log text widget
        self.log_text = ctk.CTkTextbox(self, height=200, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    
    def add_log_message(self, message: str) -> None:
        """Add a log message.
        
        Args:
            message: Message to add
        """
        self.log_text.configure(state='normal')
        self.log_text.insert('end', f"{message}\n")
        self.log_text.see('end')
        self.log_text.configure(state='disabled')
    
    def clear_log(self) -> None:
        """Clear all log messages."""
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')


class ThemeToggleButton(ctk.CTkFrame):
    """Modern iOS-style theme toggle switch."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the theme toggle button.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, corner_radius=15, height=30, width=60, **kwargs)
        
        self.callback: Optional[Callable[[], None]] = None
        
        # Create the toggle switch background
        self.switch_bg = ctk.CTkFrame(
            self,
            corner_radius=13,
            height=26,
            width=56
        )
        self.switch_bg.pack(expand=True, fill="both", padx=2, pady=2)
        
        # Create the sliding circle
        self.slider = ctk.CTkFrame(
            self.switch_bg,
            width=22,
            height=22,
            corner_radius=11
        )
        
        # Position elements based on current theme
        self._update_position()
        
        # Bind click events to all components
        self.switch_bg.bind("<Button-1>", self._on_click)
        self.slider.bind("<Button-1>", self._on_click)
        self.bind("<Button-1>", self._on_click)
        
        # Add hover effect
        self.switch_bg.bind("<Enter>", self._on_enter)
        self.switch_bg.bind("<Leave>", self._on_leave)
        self.slider.bind("<Enter>", self._on_enter)
        self.slider.bind("<Leave>", self._on_leave)
    
    def set_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for theme toggle.
        
        Args:
            callback: Function to call when button is clicked
        """
        self.callback = callback
    
    def _on_enter(self, event=None) -> None:
        """Handle mouse enter for hover effect."""
        current = ctk.get_appearance_mode()
        if current == "Dark":
            self.switch_bg.configure(fg_color="#3a3a3a")
        else:
            self.switch_bg.configure(fg_color="#d0d0d0")
    
    def _on_leave(self, event=None) -> None:
        """Handle mouse leave for hover effect."""
        self._update_colors()
    
    def _on_click(self, event=None) -> None:
        """Handle button click."""
        self._toggle_appearance()
        if self.callback:
            self.callback()
    
    def _toggle_appearance(self) -> None:
        """Toggle between light and dark appearance."""
        current = ctk.get_appearance_mode()
        
        if current == "Dark":
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")
        
        # Update position and colors
        self._update_position()
    
    def _update_position(self) -> None:
        """Update slider position based on current theme."""
        current = ctk.get_appearance_mode()
        
        if current == "Dark":
            # Dark mode - slider on the right
            self.slider.place(x=32, y=2)
        else:
            # Light mode - slider on the left
            self.slider.place(x=2, y=2)
        
        self._update_colors()
    
    def _update_colors(self) -> None:
        """Update colors based on current theme."""
        current = ctk.get_appearance_mode()
        
        if current == "Dark":
            # Dark mode colors
            self.switch_bg.configure(fg_color="#2b2b2b")
            self.slider.configure(fg_color="white")
        else:
            # Light mode colors  
            self.switch_bg.configure(fg_color="#cccccc")
            self.slider.configure(fg_color="white")
    
    def update_icon(self) -> None:
        """Update position based on current appearance mode."""
        self._update_position()
