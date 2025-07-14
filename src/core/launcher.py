import logging

from ..services.profile_service import ProfileService
from ..services.loader_service import LoaderService
from ..services.ui_service import UIService, Window


class Launcher:
    def __init__(self):
        logging.debug("Initializing all services")
        self.ui = UIService()
        self.profile_service = ProfileService()
        logging.debug("All services initialized")

        self.set_up_profile()

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

    def set_up_neoforge(self):
        logging.info("Setting up NeoForge")
