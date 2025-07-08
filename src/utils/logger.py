"""Logging utilities for the FFT Minecraft Launcher."""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from ..services.logging_service import LoggingService


# Global logging service instance
_logging_service: Optional[LoggingService] = None


def setup_logger(log_level: int = logging.INFO) -> LoggingService:
    """Setup and return the global logger instance.
    
    Args:
        log_level: Logging level
        
    Returns:
        LoggingService instance
    """
    global _logging_service
    
    if _logging_service is None:
        _logging_service = LoggingService("FFTLauncher")
    
    return _logging_service


def get_logger() -> LoggingService:
    """Get the global logger instance.
    
    Returns:
        LoggingService instance
    """
    global _logging_service
    
    if _logging_service is None:
        _logging_service = setup_logger()
    
    return _logging_service


# For backwards compatibility with the old API
class LauncherLogger:
    """Compatibility wrapper for LoggingService."""
    
    def __init__(self, name: str = "FFTLauncher"):
        """Initialize the logger wrapper.
        
        Args:
            name: Logger name
        """
        self.service = get_logger()
        self.logger = self.service.logger
    
    def setup(self, log_level: int = logging.INFO, log_file: Optional[str] = None, console_output: bool = True):
        """Setup the logger with file and console handlers.
        
        Args:
            log_level: Logging level
            log_file: Log file path (ignored, using service defaults)
            console_output: Whether to output to console
        """
        # Nothing to do - service handles this
        pass
    
    def set_ui_callback(self, callback):
        """Set a callback function for UI logging.
        
        Args:
            callback: UI callback function
        """
        self.service.set_ui_callback(callback)
    
    def debug(self, message: str):
        """Log a debug message.
        
        Args:
            message: Message to log
        """
        self.service.debug(message)
    
    def info(self, message: str):
        """Log an info message.
        
        Args:
            message: Message to log
        """
        self.service.info(message)
    
    def warning(self, message: str):
        """Log a warning message.
        
        Args:
            message: Message to log
        """
        self.service.warning(message)
    
    def error(self, message: str):
        """Log an error message.
        
        Args:
            message: Message to log
        """
        self.service.error(message)
    
    def critical(self, message: str):
        """Log a critical message.
        
        Args:
            message: Message to log
        """
        self.service.critical(message)
