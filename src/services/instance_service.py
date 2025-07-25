import logging
import os
from ..models.instance import Instance
from ..utils import file_utils, github_utils
from pathlib import Path


class InstanceService:
    def __init__(self, root_dir: str):
        logging.debug("Initializing InstanceService")
        self.instance_dir = os.path.join(root_dir, "instance")
        self.instance = Instance(instance_dir=self.instance_dir)
        self._create_instance_folder()
        self.client_repo = {
            "name": "facufierro/FFTClientMinecraft1211",
            "url": "https://github.com/facufierro/FFTClientMinecraft1211",
            "branch": "main",
        }

    def update(self):
        self.update_config()
        # self.update_kubejs()
        # self.update_modflared()
        # self.update_mods()
        # self.update_resourcepacks()
        # self.update_shaderpacks()

    def update_config(self):
        # get all the files and folders in the instance.defaultconfigs_dir and copy the to instance.configs_dir
        defaultconfigs = github_utils.fetch_all(
            self.client_repo["url"],
            "defaultconfigs",
            self.client_repo["branch"],
        )
        for file in defaultconfigs:
            dest = Path(self.instance.config_dir) / Path(file).relative_to("defaultconfigs")
            github_utils.download_repo_file(
                self.client_repo["url"],
                file,
                self.client_repo["branch"],
                dest=dest
            )

    def update_kubejs(self, zip_file):
        # replace kubejs folder with files from zip_file
        if zip_file is None:
            logging.warning("No zip file provided for kubejs update")
            return
        kubejs_folder = self.instance.kubejs_dir
        self.file_service.replace_folder(zip_file, kubejs_folder)

    def update_modflared(self, zip_file):
        # replace modflared folder with files from zip_file
        if zip_file is None:
            logging.warning("No zip file provided for modflared update")
            return
        modflared_folder = self.instance.modflared_dir
        self.file_service.replace_folder(zip_file, modflared_folder)

    def update_mods(self, zip_file):
        # replace mods folder with files from zip_file
        if zip_file is None:
            logging.warning("No zip file provided for mods update")
            return
        mods_folder = self.instance.mods_dir
        self.file_service.replace_folder(zip_file, mods_folder)

    def update_resourcepacks(self, zip_file):
        # look for files in resourcepacks folder that match the name in required_folder, and replace them, if the dont exist, add them
        if zip_file is None:
            logging.warning("No zip file provided for resourcepacks update")
            return
        resourcepacks_folder = self.instance.resourcepacks_dir
        self.file_service.add_files_to_folder(zip_file, resourcepacks_folder)

    def update_shaderpacks(self, zip_file):
        # look for files in shaderpacks folder that match the name in required_folder, and replace them, if the dont exist, add them
        if zip_file is None:
            logging.warning("No zip file provided for shaderpacks update")
            return
        shaderpacks_folder = self.instance.shaders_dir
        self.file_service.add_files_to_folder(zip_file, shaderpacks_folder)

    def _create_instance_folder(self):
        try:
            if not os.path.exists(self.instance.instance_dir):
                os.makedirs(self.instance.instance_dir)
        except Exception as e:
            logging.error("Failed to create instance folder: %s", e)
            raise
