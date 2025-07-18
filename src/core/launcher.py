import logging
from PySide6.QtCore import QThread, QObject, Signal


from ..models.constants import INSTANCE_NAME, Component, Folder, File, Url, Branch, RepoFolder
from ..models.instance import Instance

from ..ui.components.update_dialog import UpdateDialog

from ..services.ui_service import UIService, Window
from ..services.github_service import GitHubService
from ..services.versions_service import VersionsService
from ..services.launcher_service import LauncherService
from ..services.profile_service import ProfileService
from ..services.java_service import JavaService
from ..services.loader_service import LoaderService
from ..services.instance_service import InstanceService
from ..services.file_service import FileService


class Launcher:
    def __init__(self):
        logging.info("Initializing Launcher...")
        self.instance = Instance(INSTANCE_NAME)
        self.ui_service = UIService()
        
        # Initialize GitHub service after UI is ready
        self._set_up_github_service()
        
        self.version_service = VersionsService(self.instance, self.github_service)
        self.launcher_service = LauncherService(
            self.version_service, self.github_service
        )
        self.profile_service = ProfileService()
        self.java_service = JavaService(self.version_service)
        self.loader_service = LoaderService(self.instance)
        self.file_service = FileService()
        self.instance_service = InstanceService(self.instance, self.file_service)

    def start(self):
        self.main_window = self.ui_service.show(Window.MAIN)
        self._check_launcher_update()
        self._set_up_profile()
        self._check_java_update()
        self._check_loader_update()

    def launch(self):
        logging.info("Launching the game")

    def exit(self):
        logging.info("Exiting the launcher")
        self.ui_service.main_window.close()

    def _set_up_github_service(self):
        # Create progress callback that updates the UI
        def progress_callback(progress, status, details=None):
            logging.debug(f"Progress update: {progress}% - {status} - {details}")
            if hasattr(self, 'ui_service') and hasattr(self.ui_service, 'main_window'):
                main_window = self.ui_service.main_window
                if hasattr(main_window, 'progress_bar'):
                    main_window.progress_bar.set_progress(progress, status, details)
                    logging.debug(f"Progress bar updated: {progress}%")
                else:
                    logging.warning("No progress bar found in main window")
            else:
                logging.warning("UI service or main window not available for progress update")
        
        self.github_service = GitHubService(progress_callback)
        self.launcher_repo = Url.LAUNCHER_REPO.value
        self.client_repo = Url.CLIENT_REPO.value
        self.launcher_branch = Branch.LAUNCHER.value
        self.client_branch = Branch.CLIENT.value

    def _check_launcher_update(self):
        if self.version_service.check_for_updates(Component.LAUNCHER):
            update_dialog: UpdateDialog = self.ui_service.show(Window.UPDATE)
            self.ui_service.close(Window.MAIN)
            update_dialog.accept_pressed.connect(self.launcher_service.update)
            update_dialog.exec()
        else:
            logging.info("Launcher is up to date.")

    def _check_java_update(self):
        try:
            if self.version_service.check_for_updates(Component.JAVA):
                update_dialog: UpdateDialog = self.ui_service.show(Window.UPDATE)
                self.ui_service.close(Window.MAIN)
                update_dialog.accept_pressed.connect(self.java_service.update)
                update_dialog.label.setText(
                    f"Java {self.instance.required_versions.get(Component.JAVA.value)}+ is needed. \nA browser window will open to the Java download page."
                )
                update_dialog.exec()
            else:
                logging.info("Java is up to date.")
        except Exception as e:
            logging.error(f"Failed to check Java update: {e}")

    def _check_loader_update(self):
        try:
            if self.version_service.check_for_updates(Component.LOADER):
                logging.info("Loader update is needed.")
                self.loader_service.connect_update_finished(self.update_instance)
                self.main_window.on_launch_button_clicked(self.loader_service.update)
            else:
                logging.info("Loader is up to date.")
                self.main_window.on_launch_button_clicked(self.update_instance)
        except Exception as e:
            logging.error(f"Failed to check Loader update: {e}")

    def _set_up_profile(self):
        try:
            logging.info("Setting up profile...")
            self.profile = self.profile_service.get_profile_data()
            if self.profile:
                logging.info("Profile loaded successfully: %s", self.profile.name)
                logging.debug("Profile data: \n%s", self.profile.__repr__())
            else:
                logging.warning("No profile found, creating a new one")
                self.profile_service.update_profile()
        except Exception as e:
            logging.error(f"Failed to set up profile: {e}")

    def update_instance(self):
        # Show progress bar and reset it
        if hasattr(self, 'ui_service') and hasattr(self.ui_service, 'main_window'):
            main_window = self.ui_service.main_window
            if hasattr(main_window, 'progress_bar'):
                main_window.progress_bar.reset()
                main_window.progress_bar.start_multi_step(2, "Preparing instance update...")
                
                # Disable launch button during update
                if hasattr(main_window, 'launch_button'):
                    main_window.launch_button.setEnabled(False)
        
        # Create and start worker thread
        self.update_worker = UpdateWorker(self)
        self.update_worker.progress_update.connect(self._on_progress_update)
        self.update_worker.update_finished.connect(self._on_update_finished)
        self.update_worker.start()
    
    def _on_progress_update(self, progress, status, details):
        """Handle progress updates from worker thread"""
        if hasattr(self, 'ui_service') and hasattr(self.ui_service, 'main_window'):
            main_window = self.ui_service.main_window
            
            # Update progress bar
            if hasattr(main_window, 'progress_bar'):
                main_window.progress_bar.set_progress(progress, status, details)
            
            # Only log important progress milestones, not every update
            if progress in [0, 25, 50, 75, 90, 100] or "complete" in status.lower() or "error" in status.lower():
                if hasattr(main_window, 'console'):
                    main_window.console.append_message.emit(f"[{progress:3d}%] {status}", "INFO")
    
    def _on_update_finished(self, success):
        """Handle update completion"""
        if hasattr(self, 'ui_service') and hasattr(self.ui_service, 'main_window'):
            main_window = self.ui_service.main_window
            
            # Re-enable launch button
            if hasattr(main_window, 'launch_button'):
                main_window.launch_button.setEnabled(True)
            
            # Update progress bar
            if hasattr(main_window, 'progress_bar'):
                if success:
                    main_window.progress_bar.set_progress(100, "Update completed!", "All folders updated successfully")
                else:
                    main_window.progress_bar.set_error("Update failed - check console for details")
        
        logging.info(f"Instance update {'completed successfully' if success else 'failed'}")


class UpdateWorker(QThread):
    """Worker thread for instance updates to prevent UI freezing"""
    progress_update = Signal(int, str, str)  # progress, status, details
    update_finished = Signal(bool)  # success
    
    def __init__(self, launcher):
        super().__init__()
        self.launcher = launcher
    
    def run(self):
        """Run the update process in background thread"""
        try:
            logging.info("UpdateWorker started")
            # Connect progress callback to emit signals
            def progress_callback(progress, status, details=""):
                try:
                    self.progress_update.emit(progress, status, details)
                    # Only log important milestones to reduce log spam
                    if progress in [0, 25, 50, 75, 90, 100] or "complete" in status.lower() or "error" in status.lower():
                        logging.debug(f"Progress milestone: {progress}% - {status}")
                except Exception as e:
                    logging.error(f"Progress callback error: {e}")
            
            # Set up progress callback for GitHub service
            self.launcher.github_service.progress_callback = progress_callback
            
            # Clear cache to force fresh download with optimizations
            self.launcher.github_service.clear_cache()
            
            # Initial progress update
            self.progress_update.emit(0, "Starting update...", "Preparing to download files")
            
            # Extract all folders directly to filesystem - much faster!
            folder_names = [
                RepoFolder.DEFAULTCONFIGS.value,
                RepoFolder.KUBEJS.value, 
                RepoFolder.MODFLARED.value,
                RepoFolder.MODS.value,
                RepoFolder.RESOURCEPACKS.value,
                RepoFolder.SHADERPACKS.value
            ]
            
            logging.info("Updating instance folders...")
            success = self.launcher.github_service.extract_folders_directly(
                folder_names, 
                self.launcher.client_branch, 
                self.launcher.client_repo,
                self.launcher.instance.instance_path  # Extract directly to instance folder
            )
            
            if not success:
                logging.error("Failed to update instance folders")
                self.update_finished.emit(False)
                return
            
            # Download and save the servers.dat file
            self.progress_update.emit(95, "Downloading server list...", "Getting servers.dat")
            servers_content = self.launcher.github_service.get_file(
                File.SERVERS.value, self.launcher.client_branch, self.launcher.client_repo
            )
            if servers_content:
                self.launcher.file_service.save_file_content(servers_content, File.SERVERS.value)
                logging.info("servers.dat downloaded successfully")
            else:
                logging.warning("Failed to download servers.dat")
            
            self.update_finished.emit(True)
            
        except Exception as e:
            logging.error(f"Update failed with exception: {e}")
            self.update_finished.emit(False)
