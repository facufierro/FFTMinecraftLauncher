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

                launcher_version = versions.get("launcher", {})
                loader_version = versions.get("loader", {})
                minecraft_version = versions.get("minecraft", {})
                logging.debug(
                    "Current Versions: \nLauncher version: %s, \nLoader version: %s, \nMinecraft version: %s",
                    launcher_version,
                    loader_version,
                    minecraft_version,
                )
                return launcher_version, loader_version, minecraft_version

        except FileNotFoundError:
            logging.error("Versions file not found: %s", self.versions_file)
            return None, None, None
