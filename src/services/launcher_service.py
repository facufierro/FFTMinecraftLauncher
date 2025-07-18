import logging
import subprocess

from .versions_service import VersionsService
from ..services.github_service import GitHubService
from ..models.constants import Url


class LauncherService:
    def __init__(self, version_service: VersionsService, github_service: GitHubService):
        try:
            self.version_service = version_service
            self.github_service = github_service
            # Try to get updater file, but don't fail if it doesn't exist
            self.updater_file = github_service.get_release_file(
                "updater.exe", Url.LAUNCHER_REPO.value
            )
            if not self.updater_file:
                logging.warning(
                    "updater.exe not found in latest release - updater functionality will be disabled"
                )
            logging.debug("LauncherService initialized")
        except Exception as e:
            logging.critical("Error initializing LauncherService: %s", e)
            raise e

    def replace_updater(self):
        try:
            if self.updater_file:
                self.github_service.save_file(self.updater_file, "updater.exe")
                logging.info("Updater replaced successfully.")
            else:
                logging.warning("Cannot replace updater - updater.exe not available")
        except Exception as e:
            logging.error(f"Failed to replace updater: {e}")

    def update(self):
        self._launch_updater()

    def _launch_updater(self):
        logging.info("Launching updater...")
        # subprocess.Popen(["updater.exe"], cwd=".")

    def launch_game(self):
        logging.info("Launching game...")
