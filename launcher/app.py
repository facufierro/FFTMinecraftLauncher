"""Main entry point for the FFT Minecraft Launcher."""

import sys
import os
import platform
from pathlib import Path
from datetime import datetime

# Add src to path to enable imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.core.launcher import LauncherCore, LauncherError
from src.ui.main_window import MainWindow
from src.utils.logging_utils import setup_logger, get_logger
import logging


def main():
    """Main entry point for the application."""
    try:
        # Setup logging with enhanced features
        logger = setup_logger(
            log_level=logging.DEBUG,  # Use DEBUG level for log file
            capture_output=True,      # Capture stdout/stderr to log
            max_logs=20               # Keep more logs for debugging
        )
        
        # Log system information
        logger.log_system_info()
        
        # Initialize launcher core
        launcher_core = LauncherCore()
        
        # Create and run UI
        main_window = MainWindow(launcher_core)
        logger.info("Starting main window...")
        main_window.run()
        
    except LauncherError as e:
        logger = get_logger()
        logger.critical(f"Launcher error: {e}")
        sys.exit(1)
    except Exception as e:
        try:
            logger = get_logger()
            logger.logger.critical(f"Unexpected error: {e}", exc_info=True)
        except:
            print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
