import logging
from ..models.instance import Instance
from ..models.constants import Paths


class LoaderService:
    def __init__(self):
        logging.debug("Initializing LoaderService")
        self.minecraft_dir = Paths.MINECRAFT_DIR.value
        logging.debug("LoaderService initialized")

    def check_installation(self):
        logging.debug("Checking Loader installation...")
        # check if neoforge is installed at self.minecraft_dir

    def download_Loader(self):
        logging.debug("Downloading Loader...")
        # Simulate download process
        logging.debug("Loader downloaded successfully")

    def install_Loader(self):
        logging.debug("Installing Loader")
        logging.debug("Loader installation complete")

    def uninstall_Loader(self):
        logging.debug("Uninstalling Loader")
        logging.debug("Loader uninstallation complete")

    def update_Loader(self):
        logging.debug("Updating Loader")
        logging.debug("Loader update complete")

    def check_for_updates(self):
        logging.debug("Checking for Loader updates...")

    def get_installed_version(self):
        logging.debug("Getting Loader version")
