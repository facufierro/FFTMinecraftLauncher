import logging
import json
import re

from ..services.github_service import GitHubService


class VersionService:
    def __init__(self, github_service: GitHubService):
        try:
            self.github_service = github_service
            self.versions_file = "versions.json"
            self.current_versions = self._get_current_versions()
            self.github_versions = self._get_github_versions()
            logging.debug("VersionService initialized")
        except Exception as e:
            logging.critical("Error initializing VersionService: %s", e)
            raise e

    def check_for_updates(self, component):
        try:
            match (component):
                case "launcher":
                    current_version = self.current_versions.get("launcher")
                    github_version = self.github_versions.get("launcher")
                    logging.info(
                        "Checking for updates for launcher: %s vs %s",
                        current_version,
                        github_version,
                    )
                    return current_version != github_version
                case "loader":
                    current_version = self.current_versions.get("loader")
                    github_version = self.github_versions.get("loader")
                    logging.info(
                        "Checking for updates for loader: %s vs %s",
                        current_version,
                        github_version,
                    )
                    return current_version != github_version
                case "minecraft":
                    current_version = self.current_versions.get("minecraft")
                    github_version = self.github_versions.get("minecraft")
                    logging.info(
                        "Checking for updates for minecraft: %s vs %s",
                        current_version,
                        github_version,
                    )
                    return current_version != github_version
                case _:
                    logging.warning("Unknown component: %s", component)
                    return False
        except Exception as e:
            logging.error("Error checking for updates: %s", e)
            return False

    def _get_current_versions(self):
        try:
            with open(self.versions_file, "r") as file:
                versions = json.load(file)
                launcher_version = self._extract_version(
                    str(versions.get("launcher", ""))
                )
                loader_version = self._extract_version(str(versions.get("loader", "")))
                minecraft_version = self._extract_version(
                    str(versions.get("minecraft", ""))
                )
                return {
                    "launcher": launcher_version,
                    "loader": loader_version,
                    "minecraft": minecraft_version,
                }
        except FileNotFoundError:
            logging.error("Versions file not found: %s", self.versions_file)
            return {"launcher": None, "loader": None, "minecraft": None}

    def _get_github_versions(self):
        try:
            versions = self.github_service.get_file(self.versions_file)
            launcher_version = self._extract_version(str(versions.get("launcher", "")))
            loader_version = self._extract_version(str(versions.get("loader", "")))
            minecraft_version = self._extract_version(
                str(versions.get("minecraft", ""))
            )
            return {
                "launcher": launcher_version,
                "loader": loader_version,
                "minecraft": minecraft_version,
            }
        except json.JSONDecodeError as e:
            logging.error("Error decoding JSON from GitHub: %s", e)
        return {"launcher": None, "loader": None, "minecraft": None}

    def _extract_version(self, version_string):
        match = re.search(
            r"(?:[a-zA-Z0-9]+-)?(\d+\.\d+(?:\.\d+)?)(?:-pre\d+)?", version_string
        )
        if match:
            return match.group(1)
        logging.warning("Could not extract version from string: %s", version_string)
        return None
