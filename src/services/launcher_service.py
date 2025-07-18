import logging
import subprocess

from .versions_service import VersionsService
from ..services.github_service import GitHubService


class LauncherService:
    def __init__(self, version_service: VersionsService, github_service: GitHubService):
        try:
            self.version_service = version_service
            self.github_service = github_service
            self.updater_file = github_service.get_release_file("updater.exe")
            logging.debug("LauncherService initialized")
        except Exception as e:
            logging.critical("Error initializing LauncherService: %s", e)
            raise e

    def replace_updater(self):
        try:
            if self.updater_file:
                self.github_service.save_file(self.updater_file, "updater.exe")
                logging.info("Updater replaced successfully.")
        except Exception as e:
            logging.error(f"Failed to replace updater: {e}")

    def update(self):
        self._launch_updater()

    def _launch_updater(self):
        logging.info("Launching updater...")
        # subprocess.Popen(["updater.exe"], cwd=".")
