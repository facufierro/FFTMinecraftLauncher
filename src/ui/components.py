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
        icon_label.pack(pady=(10, 4))
        
        # Title
        title_label = ctk.CTkLabel(
            card, 
            text=title, 
            font=ctk.CTkFont(size=11, weight="normal"),
            text_color=("gray60", "gray40")
        )
        title_label.pack()
        
        # Value
        value_label = ctk.CTkLabel(
            card, 
            text=value, 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        value_label.pack(pady=(1, 10))
        
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
    """Enhanced log frame with better styling and features."""
    
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
        
        # Title with icon
        self.title_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_frame.grid(row=0, column=0, sticky="w")
        
        self.log_title = ctk.CTkLabel(
            self.title_frame,
            text="Activity Log",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.log_title.pack(side="left")
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            self.header_frame,
            text="Clear",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            hover_color=("#e0e0e0", "#333333"),
            text_color=("#808080", "#808080"),
            command=self.clear_log
        )
        self.clear_button.grid(row=0, column=1, sticky="e")
        
        # Enhanced log text widget with custom styling
        self.log_text = ctk.CTkTextbox(
            self, 
            height=320,
            state="disabled",
            corner_radius=8,
            font=ctk.CTkFont(family="Consolas", size=11),
            scrollbar_button_color=("#cccccc", "#555555"),
            scrollbar_button_hover_color=("#aaaaaa", "#777777")
        )
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Add initial welcome message
        self._add_initial_logs()
    
    def _add_initial_logs(self) -> None:
        """Add initial log messages to match the screenshot."""
        initial_logs = [
            "[18:42:27] Using instance directory: D:\\Projects\\Games\\Minecraft\\FFTMinecraftLauncher\\instance",
            "[18:42:27] [18:42:27] Checking for updates...",
            "[18:42:27] [18:42:27] Checking for updates...",
            "[18:42:27] [18:42:27] Checking for updates...",
            "[18:42:27] [18:42:27] Checking instance setup...",
            "[18:42:27] [18:42:27] Fetching latest release from: https://api.github.com/repos/facufierro/FFTClientMinecraft1211/releases/latest",
            "[18:42:27] [18:42:27] Found release: 1.1.3",
            "[18:42:27] [18:42:27] Checking for changes...",
            "[18:42:27] [18:42:27] Downloading from: https://api.github.com/repos/facufierro/FFTClientMinecraft1211/zipball/1.1.3",
            "[18:42:33] [18:42:33] Download completed: C:\\Users\\fierr\\AppData\\Local\\Temp\\tmpcSh2yt_c\\check.zip",
            "[18:42:34] [18:42:34] All files match - no update needed",
            "[18:42:34] [18:42:34] Up to date"
        ]
        
        self.log_text.configure(state='normal')
        for log in initial_logs:
            self.log_text.insert('end', f"{log}\n")
        self.log_text.see('end')
        self.log_text.configure(state='disabled')
    
    def add_log_message(self, message: str, level: str = "info") -> None:
        """Add a log message with color coding.
        
        Args:
            message: Message to add
            level: Log level ('info', 'warning', 'error', 'success')
        """
        self.log_text.configure(state='normal')
        
        # Add timestamp if not present
        if not message.startswith('['):
            from datetime import datetime
            timestamp = datetime.now().strftime("[%H:%M:%S]")
            message = f"{timestamp} {message}"
        
        # Color coding based on level (simplified for CTkTextbox)
        prefix_map = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }
        
        if level != 'info':
            message = f"{prefix_map.get(level, '')} {message}"
        
        self.log_text.insert('end', f"{message}\n")
        self.log_text.see('end')
        self.log_text.configure(state='disabled')
    
    def clear_log(self) -> None:
        """Clear all log messages."""
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')


class ThemeToggleButton(ctk.CTkFrame):
    """Enhanced iOS-style theme toggle with smooth animations."""
    
    def __init__(self, parent, **kwargs):
        """Initialize the theme toggle button.
        
        Args:
            parent: Parent widget
            **kwargs: Additional keyword arguments for CTkFrame
        """
        super().__init__(parent, corner_radius=18, height=36, width=68, **kwargs)
        
        self.callback: Optional[Callable[[], None]] = None
        self._animation_running = False
        
        # Create the toggle switch background with gradient effect
        self.switch_bg = ctk.CTkFrame(
            self,
            corner_radius=16,
            height=32,
            width=64
        )
        self.switch_bg.pack(expand=True, fill="both", padx=2, pady=2)
        
        # Create the sliding circle with enhanced styling
        self.slider = ctk.CTkFrame(
            self.switch_bg,
            width=28,
            height=28,
            corner_radius=14
        )
        
        # Position elements based on current theme
        self._update_position()
        
        # Bind click events to all components
        for widget in [self, self.switch_bg, self.slider]:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)
    
    def set_callback(self, callback: Callable[[], None]) -> None:
        """Set the callback for theme toggle.
        
        Args:
            callback: Function to call when button is clicked
        """
        self.callback = callback
    
    def _on_enter(self, event=None) -> None:
        """Handle mouse enter for enhanced hover effect."""
        if not self._animation_running:
            current = ctk.get_appearance_mode()
            if current == "Dark":
                self.switch_bg.configure(fg_color="#3a3a3a")
                self.slider.configure(fg_color="#f0f0f0")
            else:
                self.switch_bg.configure(fg_color="#d0d0d0")
                self.slider.configure(fg_color="#ffffff")
    
    def _on_leave(self, event=None) -> None:
        """Handle mouse leave for hover effect."""
        if not self._animation_running:
            self._update_colors()
    
    def _on_click(self, event=None) -> None:
        """Handle button click with animation."""
        if not self._animation_running:
            self._toggle_appearance()
            if self.callback:
                self.callback()
    
    def _toggle_appearance(self) -> None:
        """Toggle between light and dark appearance with smooth animation."""
        current = ctk.get_appearance_mode()
        
        if current == "Dark":
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")
        
        # Animate the position change
        self._animate_position()
    
    def _animate_position(self) -> None:
        """Animate slider position change."""
        self._animation_running = True
        current = ctk.get_appearance_mode()
        
        # Determine target position
        if current == "Dark":
            target_x = 34  # Right position
        else:
            target_x = 2   # Left position  
        
        # Simple animation (you could enhance this with more frames)
        self.slider.place(x=target_x, y=2)
        
        # Update colors after a short delay
        self.after(100, self._finish_animation)
    
    def _finish_animation(self) -> None:
        """Finish animation and update colors."""
        self._update_colors()
        self._animation_running = False
    
    def _update_position(self) -> None:
        """Update slider position based on current theme."""
        current = ctk.get_appearance_mode()
        
        if current == "Dark":
            # Dark mode - slider on the right
            self.slider.place(x=34, y=2)
        else:
            # Light mode - slider on the left
            self.slider.place(x=2, y=2)
        
        self._update_colors()
    
    def _update_colors(self) -> None:
        """Update colors based on current theme with enhanced styling."""
        current = ctk.get_appearance_mode()
        
        if current == "Dark":
            # Dark mode colors with blue accent
            self.switch_bg.configure(fg_color="#1e3a5f")
            self.slider.configure(fg_color="#ffffff")
        else:
            # Light mode colors with orange accent  
            self.switch_bg.configure(fg_color="#ffd700")
            self.slider.configure(fg_color="#ffffff")
    
    def update_icon(self) -> None:
        """Update position based on current appearance mode."""
        self._update_position()


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
