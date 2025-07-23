import logging
from pathlib import Path
from PySide6.QtCore import QThread, QObject, Signal

from ..models.constants import (
    INSTANCE_NAME,
    Component,
    Folder,
    File,
    Url,
    Branch,
    RepoFolder,
)
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
from ..version import __version__


class Launcher:
    def __init__(self):
        logging.info("Initializing Launcher...")
        from src.models.constants import get_instance_dir, get_downloads_dir

        # Ensure instance and downloads directories exist in the real install dir
        instance_dir = Path(get_instance_dir())
        downloads_dir = Path(get_downloads_dir())
        instance_dir.mkdir(parents=True, exist_ok=True)
        downloads_dir.mkdir(parents=True, exist_ok=True)

        self.instance = Instance(INSTANCE_NAME)
        self.ui_service = UIService()

        # Initialize GitHub service after UI is ready
        self._set_up_github_service()

        self.version_service = VersionsService(self.instance, self.github_service)
        self.profile_service = ProfileService()
        self.java_service = JavaService(self.version_service)
        self.loader_service = LoaderService(self.instance)
        self.file_service = FileService()
        self.instance_service = InstanceService(self.instance, self.file_service)

        # Initialize LauncherService last so it can use other services
        self.launcher_service = LauncherService(
            self.version_service, self.github_service, self.loader_service
        )
        # Always replace Updater.exe on start
        self.launcher_service.replace_updater()

    def start(self):
        self.main_window = self.ui_service.show(Window.MAIN)
        # Connect the launch button to the smart_launch logic
        if hasattr(self, "main_window") and hasattr(
            self.main_window, "on_launch_button_clicked"
        ):
            self.main_window.on_launch_button_clicked(self.smart_launch)
        self._check_launcher_update()
        self._set_up_profile()
        self._check_java_update()
        self._check_loader_update()

    def launch(self):
        """Launch the game directly"""
        logging.info("Launching the game directly...")

        # Disable button and change text during launch
        if hasattr(self, "ui_service") and hasattr(self.ui_service, "main_window"):
            main_window = self.ui_service.main_window
            if hasattr(main_window, "launch_button"):
                main_window.launch_button.setEnabled(False)
                main_window.launch_button.setText("Launching...")

        game_launched = self.launcher_service.launch_game()

        if game_launched:
            logging.info("Minecraft launched successfully")
            self.exit()
        else:
            logging.error("Failed to launch Minecraft")
            # Re-enable button after failed launch
            if hasattr(self, "ui_service") and hasattr(self.ui_service, "main_window"):
                main_window = self.ui_service.main_window
                if hasattr(main_window, "launch_button"):
                    main_window.launch_button.setEnabled(True)
                    main_window.launch_button.setText("Launch")

    def exit(self):
        import sys
        import os
        import signal
        from PySide6.QtCore import QCoreApplication

        logging.info("Exiting the launcher")
        # Attempt to stop update worker if running
        if hasattr(self, "update_worker") and self.update_worker.isRunning():
            logging.info("Stopping update worker thread...")
            self.update_worker.quit()
            self.update_worker.wait(2000)  # Wait up to 2 seconds
        # Close the main window
        self.ui_service.main_window.close()
        # Ensure Qt event loop and process exit
        QCoreApplication.quit()
        try:
            sys.exit(0)
        finally:
            # As a last resort, force kill the process
            os.kill(os.getpid(), signal.SIGTERM)

    def _set_up_github_service(self):
        # Create progress callback that updates the UI
        def progress_callback(progress, status, details=None):
            logging.debug(f"Progress update: {progress}% - {status} - {details}")
            if hasattr(self, "ui_service") and hasattr(self.ui_service, "main_window"):
                main_window = self.ui_service.main_window
                if hasattr(main_window, "progress_bar"):
                    main_window.progress_bar.set_progress(progress, status, details)
                    logging.debug(f"Progress bar updated: {progress}%")
                else:
                    logging.warning("No progress bar found in main window")
            else:
                logging.warning(
                    "UI service or main window not available for progress update"
                )

        self.github_service = GitHubService(progress_callback)
        self.launcher_repo = Url.LAUNCHER_REPO.value
        self.client_repo = Url.CLIENT_REPO.value
        self.launcher_branch = Branch.LAUNCHER.value
        self.client_branch = Branch.CLIENT.value

    def _check_launcher_update(self):
        # Fetch latest release version from GitHub
        latest_version = self.github_service.get_latest_release_version(
            Url.LAUNCHER_REPO.value
        )
        logging.info(
            f"Current launcher version: {__version__}, Latest release: {latest_version}"
        )
        if latest_version and __version__ != latest_version:
            update_dialog: UpdateDialog = self.ui_service.show(Window.UPDATE)
            self.ui_service.close(Window.MAIN)

            # Ensure updater is replaced before launching it
            def on_accept():
                logging.debug("[Update] Accept pressed: starting update process.")
                # Download latest FFTLauncher.exe from GitHub and save to downloads/FFTLauncher.exe
                logging.info(
                    "[Update] Downloading latest FFTLauncher.exe from GitHub release..."
                )
                try:
                    update_bytes = self.github_service.get_release_file(
                        "FFTLauncher.exe", Url.LAUNCHER_REPO.value
                    )
                    logging.debug(
                        f"[Update] get_release_file returned: {type(update_bytes)} size={len(update_bytes) if update_bytes else 'None'}"
                    )
                except Exception as e:
                    logging.error(f"[Update] Exception during get_release_file: {e}")
                    return
                from src.models.constants import get_downloads_dir

                from pathlib import Path
                downloads_dir = Path(get_downloads_dir())
                logging.debug(f"[Update] Downloads dir resolved to: {downloads_dir}")
                try:
                    downloads_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logging.error(f"[Update] Failed to create downloads dir: {e}")
                    return
                update_path = downloads_dir / "FFTLauncher.exe"
                logging.debug(f"[Update] Update path: {update_path}")
                if update_bytes:
                    try:
                        with open(update_path, "wb") as f:
                            f.write(update_bytes)
                        logging.info(
                            f"[Update] Downloaded and saved update to {update_path}"
                        )
                    except Exception as e:
                        logging.error(f"[Update] Failed to save update file: {e}")
                        return
                else:
                    logging.error(
                        "[Update] Failed to download FFTLauncher.exe from GitHub release."
                    )
                    return
                logging.debug("[Update] Calling replace_updater()...")
                self.launcher_service.replace_updater()
                logging.debug(
                    "[Update] Calling launcher_service.update() to launch updater..."
                )
                self.launcher_service.update()

            def on_reject():
                logging.info("Update dialog closed or rejected. Exiting launcher.")
                self.exit()

            update_dialog.accept_pressed.connect(on_accept)
            update_dialog.rejected.connect(on_reject)
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
            else:
                logging.info("Loader is up to date.")
        except Exception as e:
            logging.error(f"Failed to check Loader update: {e}")

    def smart_launch(self):
        """Smart launch that always updates instance and checks loader, then launches."""
        try:
            logging.info("Smart launch initiated...")
            main_window = None
            if hasattr(self, "ui_service") and hasattr(self.ui_service, "main_window"):
                main_window = self.ui_service.main_window
            needs_loader_update = self.version_service.check_for_updates(
                Component.LOADER
            )
            if needs_loader_update:
                logging.info("Loader update needed - starting loader update...")
                if main_window and hasattr(main_window, "launch_button"):
                    main_window.launch_button.setEnabled(False)
                    main_window.launch_button.setText("Updating Loader...")
                self.loader_service.update()
            else:
                logging.info("Always updating instance - starting instance update...")
                self.update_instance()  # Always update instance before launch
        except Exception as e:
            logging.error(f"Smart launch failed: {e}")
            if main_window and hasattr(main_window, "launch_button"):
                main_window.launch_button.setEnabled(True)
                main_window.launch_button.setText("Launch")

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
        if hasattr(self, "ui_service") and hasattr(self.ui_service, "main_window"):
            main_window = self.ui_service.main_window
            if hasattr(main_window, "progress_bar"):
                main_window.progress_bar.reset()
                main_window.progress_bar.start_multi_step(
                    2, "Preparing instance update..."
                )

                # Disable launch button during update and change text
                if hasattr(main_window, "launch_button"):
                    main_window.launch_button.setEnabled(False)
                    main_window.launch_button.setText("Updating...")

        # Create and start worker thread
        self.update_worker = UpdateWorker(self)
        self.update_worker.progress_update.connect(self._on_progress_update)
        self.update_worker.update_finished.connect(self._on_update_finished)
        self.update_worker.start()

    def _on_progress_update(self, progress, status, details):
        """Handle progress updates from worker thread"""
        if hasattr(self, "ui_service") and hasattr(self.ui_service, "main_window"):
            main_window = self.ui_service.main_window

            # Update progress bar
            if hasattr(main_window, "progress_bar"):
                main_window.progress_bar.set_progress(progress, status, details)

            # Only log important progress milestones, not every update
            if (
                progress in [0, 25, 50, 75, 90, 100]
                or "complete" in status.lower()
                or "error" in status.lower()
            ):
                if hasattr(main_window, "console"):
                    main_window.console.append_message.emit(
                        f"[{progress:3d}%] {status}", "INFO"
                    )

    def _on_update_finished(self, success):
        """Handle update completion"""
        if hasattr(self, "ui_service") and hasattr(self.ui_service, "main_window"):
            main_window = self.ui_service.main_window

            # Update progress bar
            if hasattr(main_window, "progress_bar"):
                if success:
                    main_window.progress_bar.set_progress(
                        100, "Update completed!", "All folders updated successfully"
                    )
                else:
                    main_window.progress_bar.set_error(
                        "Update failed - check console for details"
                    )

        if success:
            logging.info(
                "Instance update completed successfully - launching Minecraft..."
            )
            # Update progress to show launching state and change button text
            if hasattr(main_window, "progress_bar"):
                main_window.progress_bar.set_progress(
                    100, "Launching Minecraft...", "Starting game with updated files"
                )
            if hasattr(main_window, "launch_button"):
                main_window.launch_button.setText("Launching...")

            # Launch the game after successful update
            game_launched = self.launcher_service.launch_game()

            if game_launched:
                logging.info("Minecraft launched successfully")
                if hasattr(main_window, "progress_bar"):
                    main_window.progress_bar.set_progress(
                        100, "Game launched!", "Minecraft is starting..."
                    )
                self.exit()
            else:
                logging.error("Failed to launch Minecraft")
                # Re-enable launch button and update text after failed launch
                if hasattr(main_window, "launch_button"):
                    main_window.launch_button.setEnabled(True)
                    main_window.launch_button.setText("Launch")
                if hasattr(main_window, "progress_bar"):
                    main_window.progress_bar.set_error(
                        "Launch failed - check console for details"
                    )
        else:
            logging.info("Instance update failed")
            # Re-enable launch button on failure
            if hasattr(main_window, "launch_button"):
                main_window.launch_button.setEnabled(True)
                main_window.launch_button.setText("Launch")


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
            logging.info("UpdateWorker started (dynamic per-file update)")

            def progress_callback(progress, status, details=""):
                try:
                    self.progress_update.emit(progress, status, details)
                    if (
                        progress in [0, 25, 50, 75, 90, 100]
                        or "complete" in status.lower()
                        or "error" in status.lower()
                    ):
                        logging.debug(f"Progress milestone: {progress}% - {status}")
                except Exception as e:
                    logging.error(f"Progress callback error: {e}")

            self.launcher.github_service.progress_callback = progress_callback
            self.launcher.github_service.clear_cache()
            self.progress_update.emit(0, "Starting update...", "Checking files")

            import os
            folders_to_check = [
                ("defaultconfigs", "config", True),  # (repo_folder, local_folder, replace_only_existing)
                ("kubejs", "kubejs", False),
                ("modflared", "modflared", False),
                ("mods", "mods", False),
                ("resourcepacks", "resourcepacks", False),
                ("shaderpacks", "shaderpacks", False),
            ]
            repo_url = self.launcher.client_repo
            branch = self.launcher.client_branch
            base_path = self.launcher.instance.instance_path
            file_service = self.launcher.file_service



            FILE_CHANGE_THRESHOLD = 20  # If more than this, do full folder update
            for idx, (repo_folder, local_folder, replace_only_existing) in enumerate(folders_to_check):
                self.progress_update.emit(5 + idx*10, f"Checking {repo_folder}...", "Comparing files")
                remote_files = self.launcher.github_service.list_files_in_folder(repo_folder, branch, repo_url)
                if remote_files is None:
                    logging.warning(f"Could not list files for {repo_folder}, skipping.")
                    continue
                local_folder_path = os.path.join(base_path, local_folder)
                os.makedirs(local_folder_path, exist_ok=True)
                local_files = set(os.listdir(local_folder_path))
                remote_file_set = set(remote_files.keys())
                files_to_delete = local_files - remote_file_set
                files_to_add = remote_file_set - local_files
                files_to_update = set()
                for fname in remote_file_set & local_files:
                    local_file_path = os.path.join(local_folder_path, fname)
                    try:
                        local_size = os.path.getsize(local_file_path)
                        if local_size != remote_files[fname].get('size', -1):
                            files_to_update.add(fname)
                    except Exception:
                        files_to_update.add(fname)
                total_changes = len(files_to_delete) + len(files_to_add) + len(files_to_update)
                if total_changes > FILE_CHANGE_THRESHOLD:
                    # Download and extract the whole folder (mirror)
                    self.progress_update.emit(10 + idx*10, f"Bulk updating {local_folder}", "Downloading full folder")
                    zip_bytes = self.launcher.github_service.get_folder(repo_folder, branch, repo_url)
                    if zip_bytes:
                        import zipfile, io, shutil
                        # Remove old folder
                        try:
                            shutil.rmtree(local_folder_path)
                        except Exception:
                            pass
                        os.makedirs(local_folder_path, exist_ok=True)
                        with zipfile.ZipFile(io.BytesIO(zip_bytes), 'r') as zip_ref:
                            zip_ref.extractall(local_folder_path)
                        logging.info(f"Bulk updated {local_folder} (full folder replaced)")
                    else:
                        logging.warning(f"Failed to bulk update {local_folder}")
                    # For defaultconfigs, only replace files that exist in config
                    if replace_only_existing and repo_folder == "defaultconfigs":
                        for fname in remote_files:
                            config_file = os.path.join(base_path, "config", fname)
                            if os.path.exists(config_file):
                                content = self.launcher.github_service.download_file_from_repo(f"{repo_folder}/{fname}", branch, repo_url)
                                if content is not None:
                                    file_service.save_file_content(content, config_file)
                                    logging.info(f"Replaced config/{fname} from defaultconfigs")
                    continue
                # Otherwise, do per-file update/delete
                for fname in files_to_delete:
                    try:
                        os.remove(os.path.join(local_folder_path, fname))
                        logging.info(f"Deleted {local_folder}/{fname} (not present in repo)")
                    except Exception as e:
                        logging.warning(f"Failed to delete {local_folder}/{fname}: {e}")
                for fname in files_to_add | files_to_update:
                    local_file_path = os.path.join(local_folder_path, fname)
                    self.progress_update.emit(10 + idx*10, f"Updating {local_folder}/{fname}", "Downloading file")
                    content = self.launcher.github_service.download_file_from_repo(f"{repo_folder}/{fname}", branch, repo_url)
                    if content is not None:
                        file_service.save_file_content(content, local_file_path)
                        logging.info(f"Updated {local_folder}/{fname}")
                    else:
                        logging.warning(f"Failed to download {repo_folder}/{fname}")
                # For defaultconfigs, only replace files that exist in config
                if replace_only_existing and repo_folder == "defaultconfigs":
                    for fname in remote_files:
                        config_file = os.path.join(base_path, "config", fname)
                        if os.path.exists(config_file):
                            content = self.launcher.github_service.download_file_from_repo(f"{repo_folder}/{fname}", branch, repo_url)
                            if content is not None:
                                file_service.save_file_content(content, config_file)
                                logging.info(f"Replaced config/{fname} from defaultconfigs")

            # Special handling for servers.dat
            self.progress_update.emit(90, "Updating servers.dat", "Downloading file")
            servers_content = self.launcher.github_service.download_file_from_repo("servers.dat", branch, repo_url)
            if servers_content:
                file_service.save_file_content(servers_content, os.path.join(base_path, "servers.dat"))
                logging.info("servers.dat downloaded and replaced")
            else:
                logging.warning("Failed to download servers.dat")

            self.progress_update.emit(100, "Update complete!", "All files checked and updated as needed.")
            self.update_finished.emit(True)
        except Exception as e:
            logging.error(f"Update failed with exception: {e}")
            self.update_finished.emit(False)
