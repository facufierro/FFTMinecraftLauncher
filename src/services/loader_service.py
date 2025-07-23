import logging
import os

import requests
from ..models.instance import Instance
from ..models.constants import Path, Url, Component, LOADER_FILE_NAME


class LoaderService:
    def __init__(self, instance: Instance):
        logging.debug("Initializing LoaderService")
        self.instance = instance
        self.minecraft_dir = Path.MINECRAFT_DIR.value
        from src.models.constants import get_downloads_dir
        self.downloads_dir = get_downloads_dir()
        self.loader_url = Url.LOADER_DOWNLOAD.value % (
            self.instance.required_versions.get(Component.LOADER.value),
            self.instance.required_versions.get(Component.LOADER.value),
        )
        self.update_finished_callbacks = []
        logging.debug("LoaderService initialized")

    def update(self):
        logging.debug("Updating Loader")
        if not self._is_download_required():
            logging.debug("No download needed for Loader")
        else:
            logging.debug("Download required for Loader")
            self._download()
        self._install()
        self._emit_update_finished()

    def _is_download_required(self):
        loader_jar = os.path.join(
            self.downloads_dir,
            LOADER_FILE_NAME
            % self.instance.required_versions.get(Component.LOADER.value),
        )
        if not os.path.exists(loader_jar):
            logging.debug("Loader JAR not found, download needed")
            return True
        logging.debug("Loader JAR already exists, no download needed")
        return False

    def _download(self):
        try:
            logging.debug("Downloading Loader...")
            os.makedirs(self.downloads_dir, exist_ok=True)
            filename = os.path.basename(self.loader_url)
            target_path = os.path.join(self.downloads_dir, filename)
            response = requests.get(self.loader_url, stream=True)
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
        loader_jar = os.path.join(
            self.downloads_dir,
            LOADER_FILE_NAME
            % self.instance.required_versions.get(Component.LOADER.value),
        )
        if not os.path.exists(loader_jar):
            logging.error(f"Loader JAR not found at {loader_jar}")
            raise FileNotFoundError(f"Loader JAR not found at {loader_jar}")
        # Run the loader JAR using java -jar with --installClient to avoid GUI
        import subprocess

        try:
            result = subprocess.run(
                ["java", "-jar", loader_jar, "--installClient"],
                cwd=self.minecraft_dir,
                check=True,
                capture_output=True,
                text=True,
            )
            logging.debug(f"Loader installed successfully: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to install Loader: {e.stderr}")
            raise

    def connect_update_finished(self, callback):
        self.update_finished_callbacks.append(callback)

    def _emit_update_finished(self):
        for cb in self.update_finished_callbacks:
            cb()
