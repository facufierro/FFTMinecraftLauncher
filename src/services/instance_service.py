import logging
import os
import shutil
from ..models.instance import Instance
from ..models.constants import Folder
from ..services.file_service import FileService


class InstanceService:
    def __init__(self, instance: Instance, file_service: FileService):
        logging.debug("Initializing InstanceService")
        self.instance = instance
        self.instance_path = self.instance.instance_path
        self.file_service = file_service
        self.create_instance_folder()

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

    def update_config(self, zip_file):
        try:
            # Look for files in configs folder that match the name in required_folder, and replace them
            configs_folder = Folder.CONFIGS.value
            self.file_service.add_files_to_folder(zip_file, configs_folder)
        except Exception as e:
            logging.error("Failed to update configs: %s", e)
            raise

    def update_kubejs(self, zip_file):
        # replace kubejs folder with files from zip_file
        kubejs_folder = Folder.KUBEJS.value
        self.file_service.replace_folder(zip_file, kubejs_folder)

    def update_modflared(self, zip_file):
        # replace modflared folder with files from zip_file
        modflared_folder = Folder.MODFLARED.value
        self.file_service.replace_folder(zip_file, modflared_folder)

    def update_mods(self, zip_file):
        # replace mods folder with files from zip_file
        mods_folder = Folder.MODS.value
        self.file_service.replace_folder(zip_file, mods_folder)

    def update_resourcepacks(self, zip_file):
        # look for files in resourcepacks folder that match the name in required_folder, and replace them, if the dont exist, add them
        resourcepacks_folder = Folder.RESOURCEPACKS.value
        self.file_service.add_files_to_folder(zip_file, resourcepacks_folder)

    def update_shaderpacks(self, zip_file):
        # look for files in shaderpacks folder that match the name in required_folder, and replace them, if the dont exist, add them
        shaderpacks_folder = Folder.SHADERPACKS.value
        self.file_service.add_files_to_folder(zip_file, shaderpacks_folder)
