# handles instance operations, including creation, deletion, and management of Minecraft instances.

import logging
import os
import json

from ..models.constants import Paths


class InstanceService:
    def __init__(self):
        logging.debug("Initializing InstanceService")
        self.instance_path = Paths.INSTANCE_DIR.value
        self.version_file = f"{self.instance_path}/versions.json"
        self.launcher_version, self.loader_version, self.minecraft_version = (
            self.get_current_versions()
        )
        try:
            self.create_instance_folder()

        except Exception as e:
            logging.error("Failed to initialize InstanceService: %s", e)
            raise

    def create_instance_folder(self):
        try:
            if not os.path.exists(self.instance_path):
                os.makedirs(self.instance_path)
        except Exception as e:
            logging.error("Failed to create instance folder: %s", e)
            raise

    def delete_instance(self):
        import shutil

        logging.info("Deleting the instance")
        try:
            if os.path.exists(self.instance_path):
                shutil.rmtree(self.instance_path)
        except Exception as e:
            logging.error("Failed to delete instance: %s", e)
            raise

    def get_current_versions(self):
        logging.info("Retrieving current versions")
        try:
            # get versions from the versions.json file
            if os.path.exists(self.version_file):
                with open(self.version_file, "r") as f:
                    data = json.load(f)
                    return {
                        "launcher": data["launcher"],
                        "loader": data["loader"],
                        "minecraft": data["minecraft"],
                    }
                logging.info(
                    "Current versions retrieved: Launcher: %s, Loader: %s, Minecraft: %s",
                    data["launcher"],
                    data["loader"],
                    data["minecraft"],
                )
            else:
                logging.warning("Versions file not found, returning default versions")
                return {"launcher": None, "loader": None, "minecraft": None}

        except Exception as e:
            logging.error("Failed to retrieve current versions: %s", e)
            raise
