import logging
import os
import json
from ..models.constants import Urls


class GitHubService:
    def __init__(self):
        self.repo_url = Urls.GITHUB_REPO.value
        self.versions_file = "versions.json"
        self.launcher_version, self.loader_version, self.minecraft_version = (
            self.get_versions()
        )
        logging.debug("Initializing GitHubService with repo URL: %s", self.repo_url)
        # Initialize any necessary attributes or configurations
        pass

    def get_versions(self):
        logging.debug("Fetching versions from GitHub")
        with open(self.versions_file, "r") as f:
            data = json.load(f)
            return data["launcher"], data["loader"], data["minecraft"]

    @staticmethod
    def extract_version_number(version_str):
        """
        Extracts the numeric part of a version string, e.g. 'neoforge-21.1.192' -> '21.1.192'.
        If no numeric part is found, returns the original string.
        """
        import re

        match = re.search(r"(\d+(?:\.\d+)+)", version_str)
        return match.group(1) if match else version_str

    def check_for_updates(self, current_versions):
        logging.debug("Checking for updates")
        try:

            def version_tuple(v):
                vnum = self.extract_version_number(v)
                return tuple(int(x) for x in vnum.split("."))

            if version_tuple(self.launcher_version) > version_tuple(
                current_versions["launcher"]
            ):
                logging.info("Launcher update available: %s", self.launcher_version)
                return True
            if version_tuple(self.loader_version) > version_tuple(
                current_versions["loader"]
            ):
                logging.info("Loader update available: %s", self.loader_version)
                return True
            if version_tuple(self.minecraft_version) > version_tuple(
                current_versions["minecraft"]
            ):
                logging.info("Minecraft update available: %s", self.minecraft_version)
                return True
            logging.info("No updates available")
            return False
        except Exception as e:
            logging.error("Failed to check for updates: %s", e)
            raise

    def get_mods(self):
        logging.debug("Fetching mods from GitHub")
        # Logic to fetch the list of mods from GitHub
        # This could involve making an API call to the GitHub repository
        # and parsing the response to get the list of mods.
        return ["mod1", "mod2", "mod3"]
