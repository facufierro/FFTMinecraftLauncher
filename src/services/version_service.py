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
                logging.info("Current Versions:")
                logging.info(f"  Launcher: {launcher_version}")
                logging.info(f"  Loader: {loader_version}")
                logging.info(f"  Minecraft: {minecraft_version}")
                return {
                    "launcher": launcher_version,
                    "loader": loader_version,
                    "minecraft": minecraft_version,
                }
        except FileNotFoundError:
            logging.error("Versions file not found: %s", self.versions_file)
            return {"launcher": None, "loader": None, "minecraft": None}

    def get_github_versions(self, content):
        if content:
            try:
                versions = json.loads(content)
                launcher_version = versions.get("launcher", {})
                loader_version = self._extract_version(versions.get("loader", ""))
                minecraft_version = versions.get("minecraft", {})
                logging.info("GitHub Versions:")
                logging.info(f"  Launcher: {launcher_version}")
                logging.info(f"  Loader: {loader_version}")
                logging.info(f"  Minecraft: {minecraft_version}")
                return {
                    "launcher": launcher_version,
                    "loader": loader_version,
                    "minecraft": minecraft_version,
                }

            except json.JSONDecodeError as e:
                logging.error("Error decoding JSON from GitHub: %s", e)
        return {"launcher": None, "loader": None, "minecraft": None}

    def check_for_updates(self, content):
        try:
            github_versions = self.get_github_versions(content)
            current_versions = self.get_current_versions()
            launcher_missmatch = (
                current_versions["launcher"] != github_versions["launcher"]
            )
            loader_missmatch = current_versions["loader"] != github_versions["loader"]
            minecraft_missmatch = (
                current_versions["minecraft"] != github_versions["minecraft"]
            )
            return {
                "launcher": launcher_missmatch,
                "loader": loader_missmatch,
                "minecraft": minecraft_missmatch,
            }
        except Exception as e:
            logging.error(f"Error checking for updates: {e}")
            return {"launcher": False, "loader": False, "minecraft": False}

    def _extract_version(self, version_string):
        match = re.search(
            r"(?:[a-zA-Z0-9]+-)?(\d+\.\d+(?:\.\d+)?)(?:-pre\d+)?", version_string
        )
        if match:
            return match.group(1)
        logging.warning("Could not extract version from string: %s", version_string)
        return None
