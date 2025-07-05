"""Main entry point for the FFT Minecraft Launcher."""

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


def main():
    """Main entry point for the application."""
    try:
        # Setup logging
        log_file = "launcher.log"
        setup_logger(logging.INFO, log_file)
        
        # Initialize launcher core
        launcher_core = LauncherCore()
        
        # Create and run UI
        main_window = MainWindow(launcher_core)
        main_window.run()
        
    except LauncherError as e:
        print(f"Launcher error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
