#!/usr/bin/env python3
"""Test script for the enhanced UI components."""

import customtkinter as ctk
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ui.components import StatusFrame, ProgressFrame, ButtonFrame, LogFrame, ThemeToggleButton

class TestApp(ctk.CTk):
    """Test application to showcase the enhanced components."""
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("FFT Launcher - Enhanced UI Test")
        self.geometry("980x700")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=2)  # Give more weight to the log section
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)
        
        # Create components
        self.create_widgets()
    
    def create_widgets(self):
        """Create and layout the test widgets."""
        
        # Header with theme toggle
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ctk.CTkLabel(
            self.header_frame, 
            text="FFT Launcher", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        # Theme toggle
        self.theme_toggle = ThemeToggleButton(self.header_frame)
        self.theme_toggle.grid(row=0, column=1, sticky="e")
        self.theme_toggle.set_callback(self.on_theme_change)
        
        # Status frame
        self.status_frame = StatusFrame(self)
        self.status_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        
        # Progress frame
        self.progress_frame = ProgressFrame(self)
        self.progress_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        # Button frame
        self.button_frame = ButtonFrame(self)
        self.button_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=2)
        self.button_frame.set_button_callbacks({'launch': self.on_launch_click})
        
        # Log frame
        self.log_frame = LogFrame(self)
        self.log_frame.grid(row=4, column=0, sticky="nsew", padx=20, pady=(10, 20))
    
    def on_theme_change(self):
        """Handle theme change."""
        print("Theme changed!")
        # Update any theme-dependent elements here
    
    def on_launch_click(self):
        """Handle launch button click."""
        self.log_frame.add_log_message("Launch button clicked!", "success")
        
        # Simulate progress updates
        self.progress_frame.update_progress("Launching Minecraft...", 0.5, "loading")
        self.after(2000, lambda: self.progress_frame.update_progress("Launch complete!", 1.0, "success"))

if __name__ == "__main__":
    try:
        app = TestApp()
        app.mainloop()
    except Exception as e:
        print(f"Error running test app: {e}")
        import traceback
        traceback.print_exc()
