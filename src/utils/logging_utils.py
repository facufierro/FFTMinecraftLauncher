"""Logging utilities for the FFT Minecraft Launcher."""

import logging
import sys
import os
import time
from pathlib import Path
from typing import Optional, Callable
from datetime import datetime


class LoggingUtils:
    """Custom logger for the FFT Minecraft Launcher with both file and UI output."""
    
    def __init__(self, name: str = "FFTLauncher"):
        """Initialize the launcher logger.
        
        Args:
            name: Name of the application for log files
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.ui_callback = None
        self.log_dir = self._get_log_directory()
        self.latest_log_path = os.path.join(self.log_dir, "latest.log")
        
        # Ensure log directory exists
        if not os.path.exists(self.log_dir):
            try:
                os.makedirs(self.log_dir)
            except Exception as e:
                print(f"Failed to create log directory: {e}")
        
        # Setup the logger with default settings
        self._setup_logger()
        
        # Rotate logs at startup
        self._rotate_logs()
        
        # Set up exception handler for uncaught exceptions
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._on_exception
    
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
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        return os.path.join(base_dir, "logs")
    
    def _setup_logger(self, log_level: int = logging.INFO) -> None:
        """Setup the logger with file and console handlers.
        
        Args:
            log_level: Logging level
        """
        self.logger.setLevel(log_level)
        
        # Clear any existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create file handler for the latest log
        try:
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
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        except Exception as e:
            print(f"Failed to setup logger: {e}")
    
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
                print(f"Rotated previous log to: {os.path.basename(new_log_path)}")
            except Exception as e:
                # If rotation fails, just create a new log
                print(f"Failed to rotate log file: {e}")
    
    def set_ui_callback(self, callback: Callable[[str], None]) -> None:
        """Set a callback function for UI logging.
        
        Args:
            callback: Function to call with log messages
        """
        self.ui_callback = callback
    
    def _log_with_ui(self, level: int, message: str) -> None:
        """Log message and send to UI if callback is set.
        
        Args:
            level: Logging level
            message: Message to log
        """
        self.logger.log(level, message)
        
        if self.ui_callback:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                # Map logging levels to our level names
                level_names = {
                    logging.DEBUG: "DEBUG",
                    logging.INFO: "INFO", 
                    logging.WARNING: "WARN",
                    logging.ERROR: "ERROR",
                    logging.CRITICAL: "ERROR"
                }
                level_name = level_names.get(level, "INFO")
                formatted_message = f"[{timestamp}] [{level_name}] {message}"
                self.ui_callback(formatted_message)
            except Exception:
                # If UI callback fails, just ignore it to prevent crashes
                pass
    
    def debug(self, message: str) -> None:
        """Log a debug message.
        
        Args:
            message: Message to log
        """
        self._log_with_ui(logging.DEBUG, message)
    
    def info(self, message: str) -> None:
        """Log an info message.
        
        Args:
            message: Message to log
        """
        self._log_with_ui(logging.INFO, message)
    
    def warning(self, message: str) -> None:
        """Log a warning message.
        
        Args:
            message: Message to log
        """
        self._log_with_ui(logging.WARNING, message)
    
    def error(self, message: str) -> None:
        """Log an error message.
        
        Args:
            message: Message to log
        """
        self._log_with_ui(logging.ERROR, message)
    
    def critical(self, message: str) -> None:
        """Log a critical message.
        
        Args:
            message: Message to log
        """
        self._log_with_ui(logging.CRITICAL, message)
    
    def exception(self, message: str, exc_info=True) -> None:
        """Log an exception message.
        
        Args:
            message: Message to log
            exc_info: Whether to include exception info
        """
        self.logger.exception(message, exc_info=exc_info)
        
        # If UI callback is set, send to UI
        if self.ui_callback:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] [ERROR] {message} (see log file for details)"
                self.ui_callback(formatted_message)
            except Exception:
                # If UI callback fails, just ignore it
                pass
    
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
    
    def _on_exception(self, exc_type: type, exc_value: Exception, exc_traceback) -> None:
        """Handle uncaught exceptions.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        # Log the exception
        self.logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Call the original exception handler
        self._original_excepthook(exc_type, exc_value, exc_traceback)
    
    def capture_stdout_stderr(self) -> None:
        """Redirect stdout and stderr to the logger."""
        # Create logging wrappers for stdout and stderr
        class LoggerWriter:
            def __init__(self, logger_func):
                self.logger_func = logger_func
                self.buffer = ""
                
            def write(self, message):
                if message and message.strip():
                    if message.endswith('\n'):
                        self.buffer += message[:-1]
                        self.logger_func(self.buffer)
                        self.buffer = ""
                    else:
                        self.buffer += message
                        
            def flush(self):
                if self.buffer:
                    self.logger_func(self.buffer)
                    self.buffer = ""
        
        # Redirect stdout and stderr
        sys.stdout = LoggerWriter(self.info)
        sys.stderr = LoggerWriter(self.error)
    
    def log_system_info(self) -> None:
        """Log system information for diagnostics."""
        try:
            from datetime import datetime
            import platform
            
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            self.info(f"Application starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.info(f"OS: {platform.system()} {platform.version()}")
            self.info(f"Python: {python_version}")
            self.info(f"Platform: {platform.platform()}")
            self.info(f"Working directory: {os.getcwd()}")
            
            # Check if running as executable or from source
            if getattr(sys, 'frozen', False):
                self.info("Running as frozen executable")
                self.info(f"Executable path: {sys.executable}")
            else:
                self.info("Running from source")
                # Try to get the main script path
                main_module = sys.modules.get('__main__')
                if main_module and hasattr(main_module, '__file__'):
                    self.info(f"Main script: {main_module.__file__}")
            
            # Log Python path
            self.debug(f"Python path: {sys.path}")
            
        except Exception as e:
            self.error(f"Failed to log system info: {e}")


_logger_instance: Optional[LoggingUtils] = None


def setup_logger(log_level: int = logging.INFO, 
                 capture_output: bool = False,
                 max_logs: int = 10) -> LoggingUtils:
    """Setup and return the global logger instance.
    
    Args:
        log_level: Logging level
        capture_output: Whether to capture stdout and stderr
        max_logs: Maximum number of logs to keep
        
    Returns:
        LauncherLogger instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = LoggingUtils()
        
        # Set log level
        _logger_instance.logger.setLevel(log_level)
        
        # Clean up old logs
        _logger_instance.cleanup_old_logs(max_logs=max_logs)
        
        # Capture stdout/stderr if requested
        if capture_output:
            _logger_instance.capture_stdout_stderr()
    
    return _logger_instance


def get_logger() -> LoggingUtils:
    """Get the global logger instance.
    
    Returns:
        LauncherLogger instance
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = setup_logger()
    
    return _logger_instance
