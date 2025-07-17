import logging
import json
import re


class VersionService:
    def __init__(self):
        logging.debug("Initializing VersionService")
        self.versions_file = "versions.json"
        self.launcher_version, self.loader_version, self.minecraft_version = (
            self.get_versions()
        )

    def get_versions(self):
        logging.info("Retrieving versions from %s", self.versions_file)
        try:
            with open(self.versions_file, "r") as file:
                versions = json.load(file)
                logging.debug("Versions retrieved: %s", versions)

                launcher_version = versions.get("launcher", {})

                loader_version = self._extract_version_number(
                    versions.get("loader", {})
                )

                minecraft_version = versions.get("minecraft", {})

                return launcher_version, loader_version, minecraft_version

        except FileNotFoundError:
            logging.error("Versions file not found: %s", self.versions_file)
            return None, None, None

    def _extract_version_number(self, version_str):
        match = re.search(r"(\d+(?:\.\d+)+)", version_str)
        return match.group(1) if match else version_str
