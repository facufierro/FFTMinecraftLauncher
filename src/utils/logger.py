"""Logging utilities for the FFT Minecraft Launcher."""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class LauncherLogger:
    """Custom logger for the launcher with both file and UI output."""
    
    def __init__(self, name: str = "FFTLauncher"):
        self.logger = logging.getLogger(name)
        self.ui_callback = None
        
    def setup(self, log_level: int = logging.INFO, log_file: Optional[str] = None, console_output: bool = True):
        """Setup the logger with file and console handlers."""
        self.logger.setLevel(log_level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Console handler (optional - may be disabled in unified mode)
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler (optional)
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def set_ui_callback(self, callback):
        """Set a callback function for UI logging."""
        self.ui_callback = callback
    
    def _log_with_ui(self, level: int, message: str):
        """Log message and send to UI if callback is set."""
        self.logger.log(level, message)
        
        if self.ui_callback:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] {message}"
                self.ui_callback(formatted_message)
            except Exception:
                # If UI callback fails, just ignore it to prevent crashes
                pass
    
    def debug(self, message: str):
        """Log a debug message."""
        self._log_with_ui(logging.DEBUG, message)
    
    def info(self, message: str):
        """Log an info message."""
        self._log_with_ui(logging.INFO, message)
    
    def warning(self, message: str):
        """Log a warning message."""
        self._log_with_ui(logging.WARNING, message)
    
    def error(self, message: str):
        """Log an error message."""
        self._log_with_ui(logging.ERROR, message)
    
    def critical(self, message: str):
        """Log a critical message."""
        self._log_with_ui(logging.CRITICAL, message)


# Global logger instance
_logger_instance: Optional[LauncherLogger] = None


def setup_logger(log_level: int = logging.INFO, log_file: Optional[str] = None, console_output: bool = True) -> LauncherLogger:
    """Setup and return the global logger instance."""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = LauncherLogger()
    
    _logger_instance.setup(log_level, log_file, console_output)
    return _logger_instance


def get_logger() -> LauncherLogger:
    """Get the global logger instance."""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = setup_logger()
    
    return _logger_instance
