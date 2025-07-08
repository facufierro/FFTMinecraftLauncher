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
from src.utils.logger import setup_logger, get_logger
import logging


def main():
    """Main entry point for the application."""
    try:
        # Setup logging with the new logging service
        logger = setup_logger()
        
        # Log system information for diagnostics
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        logger.info(f"FFT Minecraft Launcher starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"OS: {platform.system()} {platform.version()}")
        logger.info(f"Python: {python_version}")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Check if running as executable or from source
        if getattr(sys, 'frozen', False):
            logger.info("Running as frozen executable")
            logger.info(f"Executable path: {sys.executable}")
        else:
            logger.info("Running from source")
            logger.info(f"Script path: {__file__}")
        
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
            logger.critical(f"Unexpected error: {e}", exc_info=True)
        except:
            print(f"Critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
