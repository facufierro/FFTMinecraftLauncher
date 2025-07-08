"""
Updater Service Module
---------------------
Core service that manages the update process
"""

import os
import sys
from ..models.app_updater import AppUpdater
from ..ui.updater_gui import UpdaterGUI


class UpdaterService:
    """Main updater service that coordinates the update process and UI"""
    
    def __init__(self, config=None, headless=False):
        """
        Initialize the updater service
        
        Args:
            config (dict): Configuration dictionary with target_file, github_repo, etc.
            headless (bool): Whether to run without GUI
        """
        self.config = config or {}
        self.headless = headless
        self.updater = self._create_updater()
        
    def _create_updater(self):
        """Create the AppUpdater instance with configuration"""
        updater = AppUpdater()
        
        # Configure from config dict
        if 'target_file' in self.config:
            updater.target_file = self.config['target_file']
        
        if 'github_repo' in self.config:
            updater.github_repo = self.config['github_repo']
            
        if 'github_file_path' in self.config:
            updater.github_file_path = self.config['github_file_path']
            
        return updater
    
    def _run_headless(self):
        """Run update process without GUI"""
        try:
            print("Starting update in headless mode...")
            
            # Close running instances
            was_running = self.updater.close_target_app()
            if was_running:
                print("Closed running application instance")
            
            # Download new version
            print("Downloading update from GitHub...")
            temp_file = self.updater.download_from_github()
            
            # Replace file
            print("Installing update...")
            self.updater.replace_target_file(temp_file)
            
            print("Update completed successfully")
            
            # Launch updated app if configured
            if self.config.get('auto_launch', True):
                print("Launching application...")
                self.updater.launch_target_app()
            
            return 0  # Success
        except Exception as e:
            print(f"Update failed: {e}")
            
            # Try to launch existing app if configured
            if self.config.get('auto_launch', True):
                try:
                    print("Attempting to launch existing application...")
                    self.updater.launch_target_app()
                except Exception as launch_error:
                    print(f"Launch failed: {launch_error}")
            
            return 1  # Error
    
    def _run_gui(self):
        """Run update process with GUI"""
        gui = UpdaterGUI(self.updater, auto_launch=self.config.get('auto_launch', True))
        gui.run()
        return 0  # GUI handles errors internally
    
    def run(self):
        """Run the update service"""
        if self.headless:
            return self._run_headless()
        else:
            return self._run_gui()
