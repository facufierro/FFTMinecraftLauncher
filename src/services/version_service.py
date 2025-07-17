import logging
import json
import re


class VersionService:
    def __init__(self):
        self.versions_file = "versions.json"
        logging.info("VersionService initialized")

    def get_current_versions(self):
        try:
            with open(self.versions_file, "r") as file:
                versions = json.load(file)
                launcher_version = versions.get("launcher", {})
                loader_version = self._extract_version(versions.get("loader", ""))
                minecraft_version = versions.get("minecraft", {})
                return {
                    launcher_version,
                    loader_version,
                    minecraft_version,
                }
        except FileNotFoundError:
            logging.error("Versions file not found: %s", self.versions_file)
            return {None, None, None}

    def get_github_versions(self, content):
        if content:
            try:
                versions = json.loads(content)
                launcher_version = versions.get("launcher", {})
                loader_version = self._extract_version(versions.get("loader", ""))
                minecraft_version = versions.get("minecraft", {})
                return {
                    launcher_version,
                    loader_version,
                    minecraft_version,
                }
            except json.JSONDecodeError as e:
                logging.error("Error decoding JSON from GitHub: %s", e)
        return {None, None, None}

    def _extract_version(self, version_string):
        """
        Extracts the version number from a version string.
        The version string can be in the format '1.16.5', '1.17', or '1.18.2-pre1'.
        """
        match = re.match(r"(\d+\.\d+(\.\d+)?)(?:-pre\d+)?", version_string)
        if match:
            return match.group(1)
        logging.warning("Could not extract version from string: %s", version_string)
        return None
