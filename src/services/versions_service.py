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
            # Only used for legacy or fallback; prefer direct inspection for loader/minecraft
            return {
                Component.LAUNCHER.value: None,
                Component.LOADER.value: self._get_installed_loader_version(),
                Component.MINECRAFT.value: self._get_installed_minecraft_version(),
            }
        except Exception as e:
            logging.error("Error getting current versions: %s", e)
            return {
                Component.LAUNCHER.value: None,
                Component.LOADER.value: None,
                Component.MINECRAFT.value: None,
            }

    def _get_required_versions(self) -> Dict[str, str]:
        """
        Returns the required versions as a dictionary. For loader and Minecraft, returns None (or implement as needed). Java is hardcoded to 17.
        """
        return {
            Component.LAUNCHER.value: None,
            Component.LOADER.value: None,
            Component.MINECRAFT.value: None,
            Component.JAVA.value: 17,
        }
    def _get_installed_loader_version(self):
        # Example: look for loader jar in the versions folder
        versions_dir = os.path.join(self.instance.game_dir, "versions")
        if not os.path.isdir(versions_dir):
            return None
        for name in os.listdir(versions_dir):
            if name.lower().startswith("neoforge-"):
                return name.replace("neoforge-", "")
        return None

    def _get_installed_minecraft_version(self):
        # Example: look for vanilla version folder in versions dir
        versions_dir = os.path.join(self.instance.game_dir, "versions")
        if not os.path.isdir(versions_dir):
            return None
        for name in os.listdir(versions_dir):
            # Assume vanilla versions are just numbers, e.g., 1.20.1
            if re.match(r"^\d+\.\d+", name):
                return name
        return None

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
