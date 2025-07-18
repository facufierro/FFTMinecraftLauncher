import logging
import os
import json
import re
import subprocess

from ..models.constants import Component
from ..services.github_service import GitHubService


class VersionService:
    def __init__(self, github_service: GitHubService):
        try:
            self.github_service = github_service
            self.versions_file = "versions.json"
            self.current_versions = self._get_current_versions()
            self.required_versions = self._get_required_versions()
            logging.debug("VersionService initialized")
        except Exception as e:
            logging.critical("Error initializing VersionService: %s", e)
            raise e

    def check_for_updates(self, component: Component, current_version=None):
        if current_version == Component.JAVA.value:
            current_version = self._get_java_current_version()
        if current_version is None:
            current_version = self.current_versions.get(component.value)

        required_version = self.required_versions.get(component.value)
        logging.info(
            "Checking for updates for %s: %s vs %s",
            component.value,
            current_version,
            required_version,
        )
        return current_version != required_version

    def _get_current_versions(self):
        try:
            if not os.path.exists(self.versions_file):
                logging.error("Versions file not found: %s", self.versions_file)
                return {
                    Component.LAUNCHER.value: None,
                    Component.LOADER.value: None,
                    Component.MINECRAFT.value: None,
                }
            with open(self.versions_file, "r") as file:
                versions = json.load(file)
                launcher_version = self._extract_version(
                    str(versions.get(Component.LAUNCHER.value, ""))
                )
                loader_version = self._extract_version(
                    str(versions.get(Component.LOADER.value, ""))
                )
                minecraft_version = self._extract_version(
                    str(versions.get(Component.MINECRAFT.value, ""))
                )
                return {
                    Component.LAUNCHER.value: launcher_version,
                    Component.LOADER.value: loader_version,
                    Component.MINECRAFT.value: minecraft_version,
                }
        except FileNotFoundError:
            logging.error("Versions file not found: %s", self.versions_file)
            return {
                Component.LAUNCHER.value: None,
                Component.LOADER.value: None,
                Component.MINECRAFT.value: None,
            }

    def _get_required_versions(self):
        try:
            versions = self.github_service.get_file(self.versions_file)
            launcher_version = self._extract_version(
                str(versions.get(Component.LAUNCHER.value, ""))
            )
            loader_version = self._extract_version(
                str(versions.get(Component.LOADER.value, ""))
            )
            minecraft_version = self._extract_version(
                str(versions.get(Component.MINECRAFT.value, ""))
            )
            return {
                Component.LAUNCHER.value: launcher_version,
                Component.LOADER.value: loader_version,
                Component.MINECRAFT.value: minecraft_version,
            }
        except json.JSONDecodeError as e:
            logging.error("Error decoding JSON from GitHub: %s", e)
        return {
            Component.LAUNCHER.value: None,
            Component.LOADER.value: None,
            Component.MINECRAFT.value: None,
        }

    def _get_java_current_version(self):
        # run 'java -version' command and parse the output
        result = subprocess.run(
            ["java", "-version"], capture_output=True, text=True, check=False
        )
        return result

    def _extract_version(self, version_string):
        match = re.search(
            r"(?:[a-zA-Z0-9]+-)?(\d+\.\d+(?:\.\d+)?)(?:-pre\d+)?", version_string
        )
        if match:
            return match.group(1)
        logging.warning("Could not extract version from string: %s", version_string)
        return None

    def _extract_major_version(self, version_string):
        match = re.search(r"(\d+)(?:\.\d+)?", version_string)
        if match:
            return match.group(1)
        logging.warning(
            "Could not extract major version from string: %s", version_string
        )
        return None
