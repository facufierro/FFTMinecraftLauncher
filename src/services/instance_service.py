import logging
import os
import shutil
from ..models.instance import Instance


class InstanceService:
    def __init__(self, instance: Instance):
        logging.debug("Initializing InstanceService")
        self.instance = instance
        self.instance_path = self.instance.instance_path
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

    def delete_instance_folder(self):
        logging.info("Deleting the instance")
        try:
            if os.path.exists(self.instance_path):
                shutil.rmtree(self.instance_path)
        except Exception as e:
            logging.error("Failed to delete instance: %s", e)
            raise
