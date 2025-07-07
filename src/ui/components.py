"""UI components for the FFT Minecraft Launcher."""

import customtkinter as ctk
from typing import Callable, Optional
import tkinter as tk
from ..utils.ui_utils import UIUtils


class StatusFrame(ctk.CTkFrame):
    """Modern status frame with card-like design."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the status frame.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, corner_radius=12, **kwargs)
        
        self.columnconfigure(0, weight=1)
        
        # Main container with padding
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=15, pady=15)
        self.container.columnconfigure((0, 1, 2), weight=1)
        
        # Create status cards
        self.dir_card = self._create_status_card(
            self.container, "📁", "Local Directory", "Instance: FFTClient", 0
        )
        self.lastcheck_card = self._create_status_card(
            self.container, "🕒", "Last Check", "2025-07-06 18:42:34", 1
        )
        self.version_card = self._create_status_card(
            self.container, "🏷️", "Current Version", "1.1.3", 2
        )
    
    def _create_status_card(self, parent, icon: str, title: str, value: str, column: int) -> ctk.CTkFrame:
        """Create a modern status card.
        
        Args:
            parent: Parent widget
            icon: Unicode emoji icon
            title: Card title
            value: Card value
            column: Grid column
            
        Returns:
            The created card frame
        """
        card = ctk.CTkFrame(parent, corner_radius=8, height=80)
        card.grid(row=0, column=column, sticky="ew", padx=5)
        card.grid_propagate(False)
        
        # Icon
        icon_label = ctk.CTkLabel(
            card, 
            text=icon, 
            font=ctk.CTkFont(size=20)
        )
        icon_label.pack(pady=(10, 4), anchor="center")
        
        # Title
        title_label = ctk.CTkLabel(
            card, 
            text=title, 
            font=ctk.CTkFont(size=11, weight="normal"),
            text_color=("gray60", "gray40")
        )
        title_label.pack(anchor="center")
        
        # Value
        value_label = ctk.CTkLabel(
            card, 
            text=value, 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        value_label.pack(pady=(1, 10), anchor="center")
        
        # Store reference for updates (using type: ignore to suppress lint warnings)
        card.value_label = value_label  # type: ignore
        
        return card
    
    def update_directory(self, directory: str) -> None:
        """Update directory display."""
        self.dir_card.value_label.configure(text=directory)  # type: ignore
    
    def update_last_check(self, timestamp: str) -> None:
        """Update last check timestamp."""
        self.lastcheck_card.value_label.configure(text=timestamp)  # type: ignore
    
    def update_version(self, version: str) -> None:
        """Update current version display."""
        self.version_card.value_label.configure(text=version)  # type: ignore


class ProgressFrame(ctk.CTkFrame):
    """Modern progress frame with enhanced visual feedback."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the progress frame.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, corner_radius=12, **kwargs)
        
        self.columnconfigure(0, weight=1)
        
        # Container with padding
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=20, pady=15)
        self.container.columnconfigure(0, weight=1)
        
        # Status indicator with icon
        self.status_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.status_frame.columnconfigure(1, weight=1)
        
        # Status icon
        self.status_icon = ctk.CTkLabel(
            self.status_frame, 
            text="✅", 
            font=ctk.CTkFont(size=16)
        )
        self.status_icon.grid(row=0, column=0, padx=(0, 8))
        
        # Status text
        self.progress_label = ctk.CTkLabel(
            self.status_frame, 
            text="Up to date (Version: 1.1.3)",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.progress_label.grid(row=0, column=1, sticky="w")
        
        # Modern progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.container, 
            height=8, 
            corner_radius=4,
            progress_color="#28a745"
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew")
        self.progress_bar.set(1.0)  # Start as complete
    
    def update_progress(self, message: str, progress: Optional[float] = None, status_type: str = "info") -> None:
        """Update progress display with enhanced visual feedback.
        
        Args:
            message: Progress message
            progress: Progress value (0.0 to 1.0), None to show indeterminate
            status_type: Type of status ('info', 'success', 'warning', 'error', 'loading')
        """
        self.progress_label.configure(text=message)
        
        # Update icon based on status type
        icons = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'loading': '🔄'
        }
        self.status_icon.configure(text=icons.get(status_type, 'ℹ️'))
        
        # Update progress bar color based on status
        colors = {
            'info': '#3b8ed0',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'loading': '#17a2b8'
        }
        self.progress_bar.configure(progress_color=colors.get(status_type, '#3b8ed0'))
        
        if progress is not None:
            self.progress_bar.stop()
            self.progress_bar.set(progress)
        else:
            self.progress_bar.start()
    
    def reset_progress(self) -> None:
        """Reset progress to initial state."""
        self.progress_bar.stop()
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="Up to date (Version: 1.1.3)")
        self.status_icon.configure(text="✅")
        self.progress_bar.configure(progress_color="#28a745")


class ButtonFrame(ctk.CTkFrame):
    """Modern action button frame with enhanced styling."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the button frame.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        # Container for centered button
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(expand=True, fill="both", padx=10, pady=2)
        
        # Create enhanced launch button
        self.launch_button = ctk.CTkButton(
            self.container, 
            text="Launch", 
            width=240, 
            height=65, 
            state="normal",
            fg_color="#28a745",
            hover_color="#1e7e34",
            font=ctk.CTkFont(size=20, weight="bold"),
            corner_radius=16,
            border_width=2,
            border_color=("#ffffff", "#cccccc")
        )
        self.launch_button.pack(expand=True, pady=2)
        
        # Add subtle shadow effect (using a second frame)
        self.shadow_frame = ctk.CTkFrame(
            self.container,
            width=244,
            height=69,
            corner_radius=16,
            fg_color=("#e0e0e0", "#404040")
        )
        self.shadow_frame.place(x=-2, y=-2, relx=0.5, rely=0.5, anchor="center")
        self.shadow_frame.lower()  # Put shadow behind button
        
        # Bind hover effects
        self.launch_button.bind("<Enter>", self._on_button_enter)
        self.launch_button.bind("<Leave>", self._on_button_leave)
    
    def _on_button_enter(self, event=None) -> None:
        """Handle button hover enter."""
        if self.launch_button.cget("state") == "normal":
            self.launch_button.configure(
                border_color=("#ffffff", "#ffffff")
            )
    
    def _on_button_leave(self, event=None) -> None:
        """Handle button hover leave."""
        self.launch_button.configure(
            border_color=("#ffffff", "#cccccc")
        )
    
    def set_button_callbacks(self, callbacks: dict) -> None:
        """Set callbacks for buttons.
        
        Args:
            callbacks: Dictionary mapping button names to callback functions
        """
        if 'launch' in callbacks:
            self.launch_button.configure(command=callbacks['launch'])
    
    def set_button_states(self, states: dict) -> None:
        """Set button states with visual feedback.
        
        Args:
            states: Dictionary mapping button names to states ('normal'/'disabled')
        """
        if 'launch' in states:
            state = states['launch']
            self.launch_button.configure(state=state)
            
            if state == "disabled":
                self.launch_button.configure(
                    fg_color=("#cccccc", "#4a4a4a"),
                    hover_color=("#cccccc", "#4a4a4a"),
                    text_color=("#666666", "#888888")
                )
            else:
                self.launch_button.configure(
                    fg_color=("#28a745", "#28a745"),
                    hover_color=("#1e7e34", "#1e7e34"),
                    text_color=("#ffffff", "#ffffff")
                )
    
    def set_launch_button_text(self, text: str) -> None:
        """Set the text of the launch button.
        
        Args:
            text: Text to display on the button
        """
        self.launch_button.configure(text=text)
    
    def set_launch_button_color(self, fg_color: str, hover_color: str) -> None:
        """Set the color of the launch button.
        
        Args:
            fg_color: Primary button color
            hover_color: Hover button color
        """
        self.launch_button.configure(fg_color=fg_color, hover_color=hover_color)


class LogFrame(ctk.CTkFrame):
    """Enhanced log frame with console-like styling and rich color support."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the log frame.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, corner_radius=12, **kwargs)
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Header with title and controls
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 3))
        self.header_frame.columnconfigure(0, weight=1)
        
        # Title with console icon
        self.title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="w")
        
        self.log_title = ctk.CTkLabel(
            self.title_frame,
            text="Activity Console",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.log_title.pack(side="left")
        
        # Controls frame
        self.controls_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.controls_frame.grid(row=0, column=1, sticky="e")
        
        # Auto-scroll toggle
        self.auto_scroll_var = ctk.BooleanVar(value=True)
        self.auto_scroll_cb = ctk.CTkCheckBox(
            self.controls_frame,
            text="Auto-scroll",
            variable=self.auto_scroll_var,
            width=80,
            height=20,
            font=ctk.CTkFont(size=10),
            checkbox_width=16,
            checkbox_height=16
        )
        self.auto_scroll_cb.pack(side="left", padx=(0, 10))
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            self.controls_frame,
            text="Clear",
            width=60,
            height=24,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=("#e0e0e0", "#333333"),
            text_color=("#666666", "#888888"),
            command=self.clear_log
        )
        self.clear_button.pack(side="left")
        
        # Enhanced log text widget with console styling
        self.log_text = ctk.CTkTextbox(
            self, 
            height=320,
            state="disabled",
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=11),
            scrollbar_button_color=("#cccccc", "#555555"),
            scrollbar_button_hover_color=("#aaaaaa", "#777777"),
            fg_color="#1a1a1a",  # Dark console background
            text_color="#e0e0e0"  # Light gray terminal text
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Configure text tags for different log levels
        self._configure_text_tags()
        
        # Message counter
        self.message_count = 0
    
    def _configure_text_tags(self):
        """Configure text tags for different log levels and sources."""
        try:
            # Bootstrap messages (blue)
            self.log_text._textbox.tag_configure("bootstrap", foreground="#4fc3f7")
            # Launcher messages (green)
            self.log_text._textbox.tag_configure("launcher", foreground="#66bb6a")
            # Info messages (white/light gray)
            self.log_text._textbox.tag_configure("info", foreground="#e0e0e0")
            # Warning messages (yellow) - consistent with progress frame
            self.log_text._textbox.tag_configure("warning", foreground="#ffc107")
            # Error messages (red)
            self.log_text._textbox.tag_configure("error", foreground="#f44336")
            # Success messages (bright green)
            self.log_text._textbox.tag_configure("success", foreground="#4caf50")
            # Debug messages (gray)
            self.log_text._textbox.tag_configure("debug", foreground="#9e9e9e")
            # Timestamp (light blue)
            self.log_text._textbox.tag_configure("timestamp", foreground="#81d4fa")
        except Exception:
            # If tag configuration fails, continue without colors
            pass
    
    def add_bootstrap_log(self, level: str, message: str, timestamp: str) -> None:
        """Add a bootstrap log message with color coding.
        
        Args:
            level: Log level ('info', 'warning', 'error', etc.)
            message: Message to add
            timestamp: Timestamp string
        """
        self._add_console_message("bootstrap", level, message, timestamp)
    
    def add_launcher_log(self, level: str, message: str, timestamp: str) -> None:
        """Add a launcher log message with color coding.
        
        Args:
            level: Log level ('info', 'warning', 'error', etc.)
            message: Message to add
            timestamp: Timestamp string
        """
        self._add_console_message("launcher", level, message, timestamp)
    
    def add_log_message(self, message: str, level: str = "info") -> None:
        """Add a general log message (backwards compatibility).
        
        Args:
            message: Message to add
            level: Log level ('info', 'warning', 'error', 'success')
        """
        # Extract timestamp if present
        timestamp = ""
        if message.startswith('[') and '] ' in message:
            timestamp_end = message.find('] ')
            timestamp = message[1:timestamp_end]
            message = message[timestamp_end + 2:]
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
        
        self._add_console_message("launcher", level, message, timestamp)
    
    def _add_console_message(self, source: str, level: str, message: str, timestamp: str) -> None:
        """Add a message to the console with rich formatting.
        
        Args:
            source: Message source ('bootstrap' or 'launcher')
            level: Log level
            message: Message text
            timestamp: Timestamp string
        """
        try:
            self.log_text.configure(state='normal')
            
            # Message counter for line numbers
            self.message_count += 1
            
            # Get level prefix and tag
            level_prefixes = {
                'info': '[INFO]',
                'warning': '[WARN]',
                'error': '[ERROR]',
                'success': '[OK]',
                'debug': '[DEBUG]'
            }
            
            level_prefix = level_prefixes.get(level, '[INFO]')
            level_tag = level if level in ['warning', 'error', 'success', 'debug'] else 'info'
            
            # Format: [timestamp] [INFO] message
            formatted_line = f"[{timestamp}] {level_prefix} {message}\n"
            
            # Insert with tags for colors
            start_pos = self.log_text.index('end-1c')
            self.log_text.insert('end', formatted_line)
            
            # Apply color tags
            try:
                # Calculate positions for each part
                line_start = f"{start_pos.split('.')[0]}.0"
                timestamp_start = f"{line_start}+1c"
                timestamp_end = f"{timestamp_start}+{len(timestamp)+1}c"
                level_start = f"{timestamp_end}+2c"
                level_end = f"{level_start}+{len(level_prefix)}c"
                message_start = f"{level_end}+1c"
                message_end = f"{line_start} lineend"
                
                # Apply tags (use source for different colors)
                self.log_text._textbox.tag_add("timestamp", timestamp_start, timestamp_end)
                self.log_text._textbox.tag_add(source, level_start, level_end)  # Color level prefix by source
                self.log_text._textbox.tag_add(level_tag, message_start, message_end)
            except Exception:
                # If tagging fails, at least the message is visible
                pass
            
            # Auto-scroll if enabled
            if self.auto_scroll_var.get():
                self.log_text.see('end')
            
            self.log_text.configure(state='disabled')
            
        except Exception:
            # If we can't add to the log widget, just ignore it
            # This prevents crashes during shutdown or widget destruction
            pass
    
    def clear_log(self) -> None:
        """Clear all log messages."""
        try:
            self.log_text.configure(state='normal')
            self.log_text.delete('1.0', 'end')
            self.message_count = 0
            self.log_text.configure(state='disabled')
        except Exception:
            pass


class ThemeToggleButton:
    """Professional theme toggle using CustomTkinter's built-in switch."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the theme toggle button.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments
        """
        self.parent = parent
        self.callback: Optional[Callable[[], None]] = None
        
        # Use CTkSwitch for a clean, professional toggle
        self.switch = ctk.CTkSwitch(
            parent,
            text="",
            width=50,
            height=24,
            switch_width=50,
            switch_height=24,
            corner_radius=12,
            border_width=0,
            fg_color=("#cccccc", "#4a4a4a"),  # Track color when OFF
            progress_color=("#ffd700", "#1e3a5f"),  # Track color when ON (light mode gold, dark mode blue)
            button_color=("#ffffff", "#ffffff"),  # Button color
            button_hover_color=("#e0e0e0", "#e0e0e0"),  # Button hover color
            command=self._on_toggle
        )
        
        # Set initial state based on current theme
        current_mode = ctk.get_appearance_mode()
        self.switch.select() if current_mode == "Dark" else self.switch.deselect()
        
        # Update colors immediately after creation
        self._update_colors()
    
    def place(self, **kwargs):
        """Place the toggle button."""
        self.switch.place(**kwargs)
    
    def grid(self, **kwargs):
        """Grid the toggle button."""
        self.switch.grid(**kwargs)
    
    def pack(self, **kwargs):
        """Pack the toggle button."""
        self.switch.pack(**kwargs)
    
    def set_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for theme toggle.
        
        Args:
            callback: Function to call when button is clicked
        """
        self.callback = callback
    
    def _on_toggle(self) -> None:
        """Handle toggle switch state change."""
        # Get switch state and toggle appearance mode
        if self.switch.get():
            # Switch is ON - set to Dark mode
            ctk.set_appearance_mode("Dark")
        else:
            # Switch is OFF - set to Light mode
            ctk.set_appearance_mode("Light")
        
        # Update colors after theme change
        self._update_colors()
        
        # Call user callback if set
        if self.callback:
            self.callback()
    
    def _update_colors(self) -> None:
        """Update switch colors based on current theme."""
        current_mode = ctk.get_appearance_mode()
        
        if current_mode == "Dark":
            # Dark mode - blue progress color
            self.switch.configure(
                progress_color=("#ffd700", "#1e3a5f"),  # Light mode gold, dark mode blue
                fg_color=("#cccccc", "#4a4a4a")
            )
        else:
            # Light mode - gold progress color  
            self.switch.configure(
                progress_color=("#ffd700", "#1e3a5f"),  # Light mode gold, dark mode blue
                fg_color=("#cccccc", "#4a4a4a")
            )
    
    def update_icon(self) -> None:
        """Update switch state based on current appearance mode."""
        current_mode = ctk.get_appearance_mode()
        
        # Update switch state without triggering callback
        if current_mode == "Dark" and not self.switch.get():
            self.switch.select()
        elif current_mode == "Light" and self.switch.get():
            self.switch.deselect()
        
        self._update_colors()


class SelfUpdateFrame(ctk.CTkFrame):
    """Frame for handling launcher self-updates."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the self-update frame.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, corner_radius=12, **kwargs)
        
        self.columnconfigure(0, weight=1)
        self.update_available = False
        self.update_info = None
        
        # Container with padding
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=15, pady=10)
        self.container.columnconfigure(1, weight=1)
        
        # Update icon
        self.update_icon = ctk.CTkLabel(
            self.container,
            text="🔄",
            font=ctk.CTkFont(size=16)
        )
        self.update_icon.grid(row=0, column=0, padx=(0, 10))
        
        # Update message
        self.update_label = ctk.CTkLabel(
            self.container,
            text="Checking for launcher updates...",
            font=ctk.CTkFont(size=13)
        )
        self.update_label.grid(row=0, column=1, sticky="w")
        
        # Update button (initially hidden)
        self.update_button = ctk.CTkButton(
            self.container,
            text="Update Launcher",
            width=120,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#007acc",
            hover_color="#005a9e",
            command=self.on_update_click
        )
        # Don't grid initially - will be shown when update is available
        
        self.update_callback: Optional[Callable] = None
        
        # Hide frame initially - don't grid it yet
        # It will be shown when needed
    
    def set_update_callback(self, callback: Callable) -> None:
        """Set callback for update button clicks.
        
        Args:
            callback: Function to call when update is requested
        """
        self.update_callback = callback
    
    def show_checking(self) -> None:
        """Show checking for updates state."""
        self.update_icon.configure(text="🔄")
        self.update_label.configure(text="Checking for launcher updates...")
        self.update_button.grid_remove()
        self.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
    
    def show_up_to_date(self) -> None:
        """Show up to date state briefly, then hide."""
        self.update_icon.configure(text="✅")
        self.update_label.configure(text="Launcher is up to date")
        self.update_button.grid_remove()
        self.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        # Hide after 3 seconds
        self.after(3000, self.grid_remove)
    
    def show_update_available(self, version: str, update_info: dict) -> None:
        """Show update available state.
        
        Args:
            version: New version string
            update_info: Update information dictionary
        """
        self.update_available = True
        self.update_info = update_info
        
        self.update_icon.configure(text="⬆️")
        self.update_label.configure(text=f"Launcher update available: v{version}")
        self.update_button.grid(row=0, column=2, padx=(10, 0))
        self.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
    
    def show_error(self, error_message: str = "Could not check for updates") -> None:
        """Show error state.
        
        Args:
            error_message: Error message to display
        """
        self.update_icon.configure(text="⚠️")
        self.update_label.configure(text=error_message)
        self.update_button.grid_remove()
        self.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        
        # Hide after 5 seconds
        self.after(5000, self.grid_remove)
    
    def show_downloading(self, progress: float = 0.0) -> None:
        """Show downloading state.
        
        Args:
            progress: Download progress (0.0 to 1.0)
        """
        self.update_icon.configure(text="⬇️")
        progress_percent = int(progress * 100)
        self.update_label.configure(text=f"Downloading update... {progress_percent}%")
        self.update_button.configure(state="disabled", text="Downloading...")
        self.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
    
    def show_installing(self) -> None:
        """Show installing state."""
        self.update_icon.configure(text="🔧")
        self.update_label.configure(text="Installing update... Please wait.")
        self.update_button.configure(state="disabled", text="Installing...")
        self.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
    
    def show_restart_required(self) -> None:
        """Show restart required state."""
        self.update_icon.configure(text="🔄")
        self.update_label.configure(text="Update downloaded. Launcher will restart shortly.")
        self.update_button.configure(state="disabled", text="Restarting...")
        self.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
    
    def on_update_click(self) -> None:
        """Handle update button click."""
        if self.update_callback and self.update_info:
            self.update_callback(self.update_info)
    
    def hide(self) -> None:
        """Hide the update frame."""
        self.grid_remove()
