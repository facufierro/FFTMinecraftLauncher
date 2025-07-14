import logging

from ..services.ui_service import UIService, Window
from ..services.instance_service import InstanceService
from ..services.profile_service import ProfileService
from ..services.github_service import GitHubService
from ..services.loader_service import LoaderService


class Launcher:
    def __init__(self):
        logging.debug("Initializing all services")
        self.ui = UIService()
        self.instance_service = InstanceService()
        self.profile_service = ProfileService()
        self.github_service = GitHubService()
        logging.debug("All services initialized")

        self.set_up_profile()
        self.check_for_updates()

    def run(self):
        self.ui.show(Window.MAIN)

    def set_up_profile(self):
        logging.info("Setting up profile...")
        self.profile = self.profile_service.get_profile_data()
        if self.profile:
            logging.info("Profile loaded successfully: %s", self.profile.name)
            logging.debug("Profile data: \n%s", self.profile.__repr__())
        else:
            logging.warning("No profile found, creating a new one")
            self.profile_service.update_profile()
        self.profile_service.add_profile_to_instance()

    def check_for_updates(self):
        logging.info("Checking for updates")
        current_versions = self.instance_service.get_current_versions()
        if current_versions:
            logging.debug("Current versions: %s", current_versions)
            self.github_service.check_for_updates(current_versions)
        else:
            logging.warning("Could not retrieve current versions")

    def set_up_neoforge(self):
        logging.info("Setting up NeoForge")
