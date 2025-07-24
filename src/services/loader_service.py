import logging
import os
import re
import subprocess
import requests
from ..models.loader import Loader


class LoaderService:
    def __init__(self, root_dir: str, minecraft_dir: str):
        logging.debug("Initializing LoaderService")
        self.downloads_dir = os.path.join(root_dir, "downloads")
        self.loader = Loader(self.downloads_dir)
        self.minecraft_dir = minecraft_dir
        self.loader.current_version = self._get_current_version()
        self.update_finished_callbacks = []
        logging.debug("LoaderService initialized")

    def update(self):
        logging.debug("Updating Loader")
        if not self._is_updaate_required():
            logging.debug("No download needed for Loader")
        else:
            logging.debug("Download required for Loader")
            self._download()
        self._install()
        self._emit_update_finished()

    def connect_update_finished(self, callback):
        self.update_finished_callbacks.append(callback)

    def _get_current_version(self):
        versions_dir = os.path.join(self.minecraft_dir, "versions")
        if not os.path.isdir(versions_dir):
            return None
        neoforge_versions = []
        for name in os.listdir(versions_dir):
            match = re.match(r"neoforge-(\d+\.\d+\.\d+)", name)
            if match:
                neoforge_versions.append(match.group(1))
        if not neoforge_versions:
            return None

        def version_key(v):
            return tuple(int(x) for x in v.split("."))

        return sorted(neoforge_versions, key=version_key)[-1]

    def _is_updaate_required(self):
        # Check if the loader JAR already exists
        if not os.path.exists(self.loader.existing_file):
            logging.debug("Loader JAR not found, download needed")
            return True
        # If current version is None, we need to download
        if self.loader.current_version is None:
            logging.debug("Loader JAR current version is None, download needed")
            return True
        # Check if the existing file matches the required version
        if self.loader.current_version == self.loader.required_version:
            logging.debug("Loader JAR matches required version, no download needed")
            return False
        # If versions do not match, download is needed
        logging.debug("Loader JAR version mismatch, download needed")
        return True

    def _download(self):
        try:
            logging.debug("Downloading Loader...")
            os.makedirs(self.loader.downloads_dir, exist_ok=True)
            target_path = os.path.join(self.loader.downloads_dir, self.loader.file_name)
            response = requests.get(self.loader.download_url, stream=True)
            response.raise_for_status()
            with open(target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            logging.debug(f"Loader downloaded to {target_path}")
        except requests.RequestException as e:
            logging.error(f"Failed to download Loader: {e}")
            raise

    def _install(self):
        logging.debug("Installing Loader...")
        if not os.path.exists(self.loader.existing_file):
            logging.error(f"Loader JAR not found at {self.loader.existing_file}")
            raise FileNotFoundError(
                f"Loader JAR not found at {self.loader.existing_file}"
            )
        try:
            result = subprocess.run(
                ["java", "-jar", self.loader.existing_file, "--installClient"],
                cwd=self.minecraft_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            logging.debug(f"Loader installed successfully: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install Loader: {e.stderr}")
            raise

    def _emit_update_finished(self):
        for cb in self.update_finished_callbacks:
            cb()
