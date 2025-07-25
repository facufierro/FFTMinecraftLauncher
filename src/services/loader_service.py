import logging
import os
import re
import subprocess
import requests
from ..models.loader import Loader


class LoaderService:
    def __init__(self, root_dir: str):
        logging.debug("Initializing LoaderService")
        self.root_dir = root_dir
        self.downloads_dir = os.path.join(root_dir, "downloads")
        self.instance_dir = os.path.join(root_dir, "instance")
        self.loader = Loader(
            self.instance_dir,
            self.downloads_dir,
        )
        self.update_finished_callbacks = []
        logging.debug("LoaderService initialized")

    def update(self):
        logging.debug("Updating Loader")
        if self._is_installer_update_required():
            logging.debug("Download required for Loader")
            self._download()
        if self._is_update_required():
            logging.debug("Installing Loader")
            self._install()
        self._emit_update_finished()

    def connect_update_finished(self, callback):
        self.update_finished_callbacks.append(callback)

    def _is_update_required(self):
        logging.debug("Checking if Launcher is already installed")
        if not os.path.exists(self.loader.launcher_dir):
            logging.debug("Launcher JAR not found, update needed")
            return True

    def _is_installer_update_required(self):
        # Check if the installer JAR exists
        installer_path = os.path.join(self.loader.downloads_dir, self.loader.installer)
        if not os.path.exists(installer_path):
            logging.debug("Loader installer JAR not found, download needed")
            return True
        # If versions do not match, download is needed
        logging.debug("Loader installer JAR version mismatch, download needed")
        return True

    def _download(self):
        try:
            logging.debug("Downloading Loader Installer...")
            os.makedirs(self.loader.downloads_dir, exist_ok=True)
            target_path = os.path.join(self.loader.downloads_dir, self.loader.installer)
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
        print("Running NeoForge installer...")
        subprocess.run(
            [
                "java",
                "-jar",
                str(self.loader.installer),
                "--installClient",
                str(self.instance_dir),
            ],
            check=True,
        )
        print("NeoForge install complete.")

    def _emit_update_finished(self):
        for cb in self.update_finished_callbacks:
            cb()
