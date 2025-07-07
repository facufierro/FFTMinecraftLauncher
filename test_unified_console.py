#!/usr/bin/env python3
"""Test script for the unified console interface."""

import sys
import os
from pathlib import Path

# Add src to path to enable imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.launcher import LauncherCore, LauncherError
from src.ui.main_window import MainWindow
from src.utils.logger import setup_logger
import logging
import datetime
import tkinter as tk
from tkinter import messagebox

# Simulate bootstrap messages
bootstrap_messages = [
    ("info", "FFT Minecraft Launcher Bootstrap Started"),
    ("info", "Bootstrap running from: test mode"), 
    ("info", "Checking for updates..."),
    ("info", "Launcher is up to date!"),
    ("info", "Starting unified launcher..."),
    ("info", "Loading launcher components...")
]

def simulate_bootstrap_messages(main_window):
    """Simulate bootstrap messages being sent to the GUI."""
    for i, (level, message) in enumerate(bootstrap_messages):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        # Schedule each message with a small delay
        main_window.root.after(i * 500, lambda l=level, m=message, t=timestamp: 
                             main_window._add_bootstrap_log(l, m, t))

def main():
    """Main test function."""
    try:
        # Setup logging for the main launcher (no console output in unified mode)
        log_file = "test_launcher.log"
        setup_logger(logging.INFO, log_file, console_output=False)
        
        # Initialize launcher core
        launcher_core = LauncherCore()
        
        # Create main window
        main_window = MainWindow(launcher_core)
        
        # Set up the launcher logging callback
        def launcher_to_gui_callback(message):
            """Send launcher messages to the GUI log."""
            # Extract timestamp and message
            if message.startswith('[') and '] ' in message:
                timestamp_end = message.find('] ')
                timestamp = message[1:timestamp_end]
                msg_part = message[timestamp_end + 2:]
            else:
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                msg_part = message
            
            # Determine log level from message content
            level = "info"
            if "error" in msg_part.lower() or "failed" in msg_part.lower():
                level = "error"
            elif "warning" in msg_part.lower() or "warn" in msg_part.lower():
                level = "warning"
            elif "success" in msg_part.lower() or "completed" in msg_part.lower() or "ready" in msg_part.lower():
                level = "success"
            
            main_window._add_launcher_log(level, msg_part, timestamp)
        
        # Set up the launcher logging callback
        launcher_core.logger.set_ui_callback(launcher_to_gui_callback)
        
        # Add a welcome message
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        main_window._add_bootstrap_log("info", "Testing unified console interface", timestamp)
        main_window._add_bootstrap_log("success", "Bootstrap messages will appear in blue", timestamp)
        main_window._add_launcher_log("success", "Launcher messages will appear in green", timestamp)
        main_window._add_launcher_log("warning", "Warning messages appear in yellow", timestamp)
        main_window._add_launcher_log("error", "Error messages appear in red", timestamp)
        
        # Simulate bootstrap messages over time
        simulate_bootstrap_messages(main_window)
        
        print("Starting unified console test...")
        print("Check the GUI Activity Console for colored, formatted output")
        print("This console window should be hidden in the final build")
        
        # Run the main window
        main_window.run()
        
    except LauncherError as e:
        messagebox.showerror("Launcher Error", f"Launcher error: {e}")
        sys.exit(1)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
