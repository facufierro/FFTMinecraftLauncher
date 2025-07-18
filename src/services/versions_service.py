import logging
import os
import json
import re
import subprocess
from typing import Dict
from ..models.instance import Instance
from ..models.constants import Component, Url, Branch
from .github_service import GitHubService


class VersionsService:
    def __init__(self, instance: Instance, github_service: GitHubService):
        try:
            self.github_service = github_service
            self.instance = instance
            self.instance.current_versions = self._get_current_versions()
            self.instance.required_versions = self._get_required_versions()
            logging.debug("VersionService initialized")
        except Exception as e:
            logging.critical("Error initializing VersionService: %s", e)
            raise e

    def check_for_updates(self, component: Component, current_version=None):
        try:
            if current_version is None:
                current_version = self.instance.current_versions.get(component.value)
            if component == Component.JAVA:
                return next(self._check_java_update())
            required_version = self.instance.required_versions.get(component.value)
            logging.info(
                "Checking for updates for %s: %s vs %s",
                component.value,
                current_version,
                required_version,
            )
            return current_version != required_version
        except Exception as e:
            logging.error("Error checking for updates: %s", e)
            return False

    def _check_java_update(self):
        try:
            current_version = self._get_java_current_version()
            required_version = self.instance.required_versions.get(Component.JAVA.value)
            logging.info(
                "Checking for updates for java: %s vs %s",
                current_version,
                required_version,
            )
            if not current_version or not required_version:
                logging.error("Current or required Java version is not set.")
                yield True
            else:
                yield int(current_version) < int(required_version)
        except Exception as e:
            logging.error("Error checking Java update: %s", e)
            yield False

    def _get_current_versions(self):
        try:
            if not os.path.exists(self.instance.versions_file):
                logging.error(
                    "Versions file not found: %s", self.instance.versions_file
                )
                return {
                    Component.LAUNCHER.value: None,
                    Component.LOADER.value: None,
                    Component.MINECRAFT.value: None,
                }
            with open(self.instance.versions_file, "r") as file:
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
            logging.error("Versions file not found: %s", self.instance.versions_file)
            return {
                Component.LAUNCHER.value: None,
                Component.LOADER.value: None,
                Component.MINECRAFT.value: None,
            }

    def _get_required_versions(self) -> Dict[str, str]:
        """Fetches the required versions and returns them as a dictionary.
        Returns:
            Dict[str, str]: Launcher, Loader, Minecraft, and Java versions.
        """
        try:
            versions = self.github_service.get_file(
                self.instance.versions_file,
                Branch.LAUNCHER.value,
                Url.LAUNCHER_REPO.value,
            )
            launcher_version = self._extract_version(
                str(versions.get(Component.LAUNCHER.value, ""))
            )
            loader_version = self._extract_version(
                str(versions.get(Component.LOADER.value, ""))
            )
            minecraft_version = self._extract_version(
                str(versions.get(Component.MINECRAFT.value, ""))
            )
            java_version = self._extract_major_version(
                str(versions.get(Component.JAVA.value, ""))
            )
            return {
                Component.LAUNCHER.value: launcher_version,
                Component.LOADER.value: loader_version,
                Component.MINECRAFT.value: minecraft_version,
                Component.JAVA.value: java_version,
            }
        except json.JSONDecodeError as e:
            logging.error("Error decoding JSON from GitHub: %s", e)
        return {
            Component.LAUNCHER.value: None,
            Component.LOADER.value: None,
            Component.MINECRAFT.value: None,
            Component.JAVA.value: None,
        }

    def _get_java_current_version(self):
        try:
            result = subprocess.run(
                ["java", "-version"], capture_output=True, text=True, check=False
            )
            if result.stderr:
                version_output = result.stderr.splitlines()[0]
                match = re.search(r"\d+\.\d+\.\d+", version_output)
                if match:
                    return self._extract_major_version(match.group(0))
            return None
        except FileNotFoundError:

            logging.error("Java executable not found.")
            return None

    def _extract_version(self, version_string):
        try:
            match = re.search(
                r"(?:[a-zA-Z0-9]+-)?(\d+\.\d+(?:\.\d+)?)(?:-pre\d+)?", version_string
            )
            if match:
                return match.group(1)
            logging.warning("Could not extract version from string: %s", version_string)
            return None
        except Exception as e:
            logging.error("Error extracting version: %s", e)
            return None

    def _extract_major_version(self, version_string):
        try:
            match = re.search(r"(\d+)(?:\.\d+)?", version_string)
            if match:
                return match.group(1)
            logging.warning(
                "Could not extract major version from string: %s", version_string
            )
            return None
        except Exception as e:
            logging.error("Error extracting major version: %s", e)
            return None
