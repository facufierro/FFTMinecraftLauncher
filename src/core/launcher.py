import logging

from ..ui.components.update_dialog import UpdateDialog

from ..services.ui_service import UIService, Window
from ..services.github_service import GitHubService
from ..services.version_service import VersionService
from ..services.launcher_service import LauncherService
from ..services.profile_service import ProfileService


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
        # self.instance_service = InstanceService()

    def start(self):
        self.ui_service.show(Window.MAIN)
        self._check_launcher_update()
        self._set_up_profile()
        # self._check_for_updates()

    def update(self):
        logging.info("Updating...")

    def launch(self):
        logging.info("Launching the game")

    def exit(self):
        logging.info("Exiting the launcher")
        self.ui_service.main_window.close()

    def _check_launcher_update(self):
        if self.version_service.check_for_updates("launcher"):
            update_dialog: UpdateDialog = self.ui_service.show(Window.UPDATE)
            self.ui_service.close(Window.MAIN)
            update_dialog.accept_pressed.connect(self.launcher_service.update)
            update_dialog.exec()
        else:
            logging.info("Launcher is up to date.")

    def _set_up_profile(self):
        logging.info("Setting up profile...")
        self.profile = self.profile_service.get_profile_data()
        if self.profile:
            logging.info("Profile loaded successfully: %s", self.profile.name)
            logging.debug("Profile data: \n%s", self.profile.__repr__())
        else:
            logging.warning("No profile found, creating a new one")
            self.profile_service.update_profile()
        self.profile_service.add_profile_to_instance()

    # def _check_for_updates(self):
    #     logging.info("Checking for updates")
    #     current_versions = self.instance_service.get_current_versions()
    #     if current_versions:
    #         logging.debug("Current versions: %s", current_versions)
    #         self.github_service.check_for_updates(current_versions)
    #     else:
    #         logging.warning("Could not retrieve current versions")

    # def _set_up_neoforge(self):
    #     logging.info("Setting up NeoForge")
