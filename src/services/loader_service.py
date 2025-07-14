import logging
from ..models.instance import Instance
from ..models.constants import Paths


class LoaderService:
    def __init__(self, instance: Instance):
        logging.debug("Initializing LoaderService")
        self.instance = instance
        self.minecraft_dir = Paths.MINECRAFT_DIR.value
        self.minecraft_version = instance.minecraft_version
        self.loader_version = instance.loader_version
        logging.debug("LoaderService initialized")

    def check_installation(self):
        logging.debug("Checking Loader installation...")
        # check if neoforge is installed at self.minecraft_dir
        if not self.instance.loader_version:
            logging.debug("Loader version not specified, assuming not installed")
            return False

        logging.debug(f"Checking Loader installation in {self.minecraft_dir}")

    def get_version(self):
        logging.debug("Getting Loader version")
        # Logic to retrieve the installed Loader version
        return self.loader_version

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
