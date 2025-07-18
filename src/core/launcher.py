import logging

from ..services.ui_service import UIService, Window
from ..services.version_service import VersionService
from ..services.instance_service import InstanceService
from ..services.profile_service import ProfileService
from ..services.github_service import GitHubService
from ..services.loader_service import LoaderService


class Launcher:
    def __init__(self):
        logging.info("Initializing services...")
        self.ui_service = UIService()
        self.github_service = GitHubService()
        self.version_service = VersionService()
        # self.instance_service = InstanceService()
        # self.profile_service = ProfileService()
        logging.info("All services initialized")

    def start(self):
        self.ui_service.show(Window.MAIN)
        self.versions_content = self.github_service.get_file("versions.json")

        launcher_mismatch, loader_mismatch, minecraft_mismatch = (
            self.version_service.check_for_updates(self.versions_content)
        )
        if launcher_mismatch:
            logging.info("Launcher version mismatch detected.")
            self._update_launcher()
        elif loader_mismatch:
            logging.info("Loader version mismatch detected.")
        elif minecraft_mismatch:
            logging.info("Minecraft version mismatch detected.")
        else:
            logging.info("No version mismatches detected.")

        # self._set_up_profile()
        # self._check_for_updates()

    def update(self):
        logging.info("Updating...")

    def launch(self):
        logging.info("Launching the game")

    def exit(self):
        logging.info("Exiting the launcher")
        self.ui_service.main_window.close()

    def _replace_updater(self):
        try:
            updater_content = self.github_service.get_release_file("updater.exe")
            if updater_content:
                self.github_service.save_file(updater_content, "updater.exe")
                logging.info("Updater replaced successfully.")
        except Exception as e:
            logging.error(f"Failed to replace updater: {e}")

    def _check_for_updates(self):
        logging.info("Checking for updates...")
        self.version_service.check_for_updates(self.versions_content)

    def _update_launcher(self):
        logging.info("Updating launcher...")
        self.ui_service.show(Window.UPDATE)

    # def _set_up_profile(self):
    #     logging.info("Setting up profile...")
    #     self.profile = self.profile_service.get_profile_data()
    #     if self.profile:
    #         logging.info("Profile loaded successfully: %s", self.profile.name)
    #         logging.debug("Profile data: \n%s", self.profile.__repr__())
    #     else:
    #         logging.warning("No profile found, creating a new one")
    #         self.profile_service.update_profile()
    #     self.profile_service.add_profile_to_instance()

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
