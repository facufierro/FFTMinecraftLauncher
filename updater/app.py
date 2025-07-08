#!/usr/bin/env python3
"""
GitHub-based App Updater - Main Entry Point
-------------------------------------------
This service automatically updates applications by downloading the latest version
from GitHub and replacing the local executable.

Usage:
    python app.py          # Run with default configuration
    python app.py --config config.json  # Run with custom configuration
"""

import argparse
import json
import os
import sys
import importlib.util

# Add the project root to Python path to allow proper imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now we can import our modules
from src.models.app_updater import AppUpdater
from src.ui.updater_gui import UpdaterGUI
from src.services.updater_service import UpdaterService


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="GitHub-based Application Updater")
    parser.add_argument(
        "--config", 
        help="Path to configuration file (JSON)",
        default=None
    )
    parser.add_argument(
        "--headless", 
        action="store_true",
        help="Run in headless mode (no GUI)"
    )
    parser.add_argument(
        "--no-launch", 
        action="store_true",
        help="Don't launch application after update"
    )
    return parser.parse_args()


def load_config(config_path=None):
    """Load configuration from file or use defaults"""
    default_config = {
        "target_file": "app.exe",
        "github_repo": "facufierro/Updater",
        "github_file_path": "dist/app.exe",
        "auto_launch": True
    }
    
    if not config_path:
        return default_config
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults to ensure all keys exist
                default_config.update(config)
        else:
            print(f"Warning: Config file {config_path} not found. Using defaults.")
    except Exception as e:
        print(f"Error loading config: {e}")
        print("Using default configuration.")
    
    return default_config


def main():
    """Main application entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line args
    if args.no_launch:
        config["auto_launch"] = False
    
    # Initialize and run updater service
    service = UpdaterService(
        config=config,
        headless=args.headless
    )
    
    # Start the service
    exit_code = service.run()
    
    # Exit with appropriate code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
