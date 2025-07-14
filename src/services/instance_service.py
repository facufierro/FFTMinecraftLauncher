# handles instance operations, including creation, deletion, and management of Minecraft instances.

import logging
import os

from ..models.constants import Paths


class InstanceService:
    def __init__(self):
        logging.debug("Initializing InstanceService")
        self.instance_path = Paths.INSTANCE_DIR.value
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

    def update_instance(self):
        logging.info("Updating the instance")
        try:
            # Logic to update the FFTClient instance
            pass
        except Exception as e:
            logging.error("Failed to update instance: %s", e)
            raise

    def get_instance(self):
        logging.info("Retrieving the instance")
        try:
            # Logic to retrieve the FFTClient instance
            pass
        except Exception as e:
            logging.error("Failed to retrieve instance: %s", e)
            raise
