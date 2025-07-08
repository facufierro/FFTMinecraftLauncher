"""Logging service for the FFT Minecraft Launcher."""

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable

class LoggingService:
    """Service for handling application logging with rotating file logs."""
    
    def __init__(self, app_name: str = "FFTLauncher"):
        """Initialize the logging service.
        
        Args:
            app_name: Name of the application for log files
        """
        self.app_name = app_name
        self.log_dir = self._get_log_directory()
        self.latest_log_path = os.path.join(self.log_dir, "latest.log")
        self.logger = self._setup_logger()
        self.ui_callback = None
        
        # Ensure log directory exists
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # Rotate logs at startup
        self._rotate_logs()
    
    def _get_log_directory(self) -> str:
        """Get the log directory path.
        
        Returns:
            Path to the log directory
        """
        # Determine base directory based on whether this is a frozen executable
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_dir = os.path.dirname(sys.executable)
        else:
            # Running in a normal Python environment
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        return os.path.join(base_dir, "logs")
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger.
        
        Returns:
            Configured logger
        """
        logger = logging.getLogger(self.app_name)
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler for the latest log
        file_handler = logging.FileHandler(self.latest_log_path, mode='w', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', 
                                      datefmt='%H:%M:%S')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _rotate_logs(self) -> None:
        """Rotate log files by renaming the previous latest.log file."""
        if os.path.exists(self.latest_log_path):
            try:
                # Read the first line of the log to extract the timestamp
                with open(self.latest_log_path, 'r', encoding='utf-8') as log_file:
                    first_line = log_file.readline().strip()
                
                # Extract timestamp from the log format [HH:MM:SS]
                timestamp = datetime.now().strftime("%Y-%m-%d")
                if first_line and '[' in first_line and ']' in first_line:
                    time_str = first_line.split(']')[0][1:]
                    try:
                        # Try to parse time from the log
                        log_time = datetime.strptime(time_str, "%H:%M:%S")
                        today = datetime.now()
                        log_date = datetime(today.year, today.month, today.day, 
                                           log_time.hour, log_time.minute, log_time.second)
                        timestamp = log_date.strftime("%Y-%m-%d_%H-%M-%S")
                    except ValueError:
                        # If parsing fails, use current time
                        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                
                # Create a new filename with the timestamp
                new_log_path = os.path.join(self.log_dir, f"{timestamp}.log")
                
                # Make sure we don't overwrite an existing log
                counter = 1
                while os.path.exists(new_log_path):
                    new_log_path = os.path.join(self.log_dir, f"{timestamp}_{counter}.log")
                    counter += 1
                
                # Rename the log file
                os.rename(self.latest_log_path, new_log_path)
                self.info(f"Rotated previous log to: {os.path.basename(new_log_path)}")
            except Exception as e:
                # If rotation fails, just create a new log
                # The old one will be overwritten
                self.error(f"Failed to rotate log file: {str(e)}")
    
    def set_ui_callback(self, callback: Callable[[str], None]) -> None:
        """Set a callback function for log messages to be displayed in the UI.
        
        Args:
            callback: Function to call with log messages
        """
        self.ui_callback = callback
        
    def _log(self, level: int, message: str, **kwargs) -> None:
        """Log a message with the specified level.
        
        Args:
            level: Logging level
            message: Message to log
            **kwargs: Additional logging parameters
        """
        # Send to standard logger
        self.logger.log(level, message, **kwargs)
        
        # If UI callback is set, send to UI
        if self.ui_callback:
            # Format the message similar to the file logger
            now = datetime.now().strftime('%H:%M:%S')
            level_name = logging.getLevelName(level)
            formatted_message = f"[{now}] [{level_name}] {message}"
            try:
                self.ui_callback(formatted_message)
            except Exception as e:
                # If the UI callback fails, log to console but don't create a loop
                print(f"UI callback failed: {str(e)}")
    
    def debug(self, message: str, **kwargs) -> None:
        """Log a debug message.
        
        Args:
            message: Message to log
            **kwargs: Additional logging parameters
        """
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log an info message.
        
        Args:
            message: Message to log
            **kwargs: Additional logging parameters
        """
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log a warning message.
        
        Args:
            message: Message to log
            **kwargs: Additional logging parameters
        """
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log an error message.
        
        Args:
            message: Message to log
            **kwargs: Additional logging parameters
        """
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log a critical message.
        
        Args:
            message: Message to log
            **kwargs: Additional logging parameters
        """
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, exc_info=True, **kwargs) -> None:
        """Log an exception message.
        
        Args:
            message: Message to log
            exc_info: Whether to include exception info
            **kwargs: Additional logging parameters
        """
        self.logger.exception(message, exc_info=exc_info, **kwargs)
        
        # If UI callback is set, send to UI
        if self.ui_callback:
            # Format the message similar to the file logger
            now = datetime.now().strftime('%H:%M:%S')
            formatted_message = f"[{now}] [ERROR] {message} (see log file for details)"
            try:
                self.ui_callback(formatted_message)
            except Exception as e:
                print(f"UI callback failed: {str(e)}")
    
    def get_log_files(self) -> list:
        """Get a list of log files in the log directory.
        
        Returns:
            List of log file paths
        """
        if not os.path.exists(self.log_dir):
            return []
        
        log_files = []
        for filename in os.listdir(self.log_dir):
            if filename.endswith(".log"):
                log_files.append(os.path.join(self.log_dir, filename))
        
        return sorted(log_files, key=os.path.getmtime, reverse=True)
    
    def cleanup_old_logs(self, max_logs: int = 10) -> None:
        """Clean up old log files, keeping only the specified number.
        
        Args:
            max_logs: Maximum number of log files to keep
        """
        log_files = self.get_log_files()
        
        # Always keep latest.log
        if self.latest_log_path in log_files:
            log_files.remove(self.latest_log_path)
        
        # Delete oldest logs if we have too many
        if len(log_files) > max_logs:
            for log_file in log_files[max_logs:]:
                try:
                    os.remove(log_file)
                    self.debug(f"Deleted old log file: {os.path.basename(log_file)}")
                except Exception as e:
                    self.warning(f"Failed to delete old log file {os.path.basename(log_file)}: {str(e)}")
