import logging


from ..models.constants import Component
from ..ui.components.update_dialog import UpdateDialog

from ..services.ui_service import UIService, Window
from ..services.github_service import GitHubService
from ..services.version_service import VersionService
from ..services.launcher_service import LauncherService
from ..services.profile_service import ProfileService
from ..services.java_service import JavaService


class Launcher:
    def __init__(self):
        logging.info("Initializing Launcher...")
        self.ui_service = UIService()
        self.github_service = GitHubService()
        self.version_service = VersionService(self.github_service)
        self.launcher_service = LauncherService(
            self.version_service, self.github_service
        )
        self.profile_service = ProfileService()
        self.java_service = JavaService(self.version_service)
        # self.instance_service = InstanceService()

    def start(self):
        self.main_window = self.ui_service.show(Window.MAIN)
        self._check_launcher_update()
        self._set_up_profile()
        self._check_java_update()
        self._check_loader_update()

        # self._check_for_updates()

    def update(self):
        logging.info("Updating...")

    def launch(self):
        logging.info("Launching the game")

    def exit(self):
        logging.info("Exiting the launcher")
        self.ui_service.main_window.close()

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
                    f"Java {self.version_service.required_versions.get(Component.JAVA.value)}+ is needed. A browser window will open to the Java download page."
                )
                update_dialog.exec()
            else:
                logging.info("Java is up to date.")
        except Exception as e:
            logging.error(f"Failed to check Java update: {e}")

    def _check_loader_update(self):
        try:
            if self.version_service.check_for_updates(Component.LOADER):
                self.main_window.launch_button.text = "Update"
            else:
                logging.info("Loader is up to date.")
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
            self.profile_service.add_profile_to_instance()
        except Exception as e:
            logging.error(f"Failed to set up profile: {e}")
