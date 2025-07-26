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
        self.server_repo = {
            "name": "facufierro/FFTServerMinecraft1211",
            "url": "https://github.com/facufierro/FFTServerMinecraft1211",
            "branch": "main",
        }

    def update(self):
        self.update_config()
        self.update_kubejs()
        self.update_modflared()
        self.update_mods()
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
            dest = Path(self.instance.config_dir) / Path(file).relative_to(
                "defaultconfigs"
            )
            dest.parent.mkdir(parents=True, exist_ok=True)
            github_utils.download_repo_file(
                self.client_repo["url"], file, self.client_repo["branch"], dest=dest
            )

    def update_kubejs(self):
        # Fetch all files from the kubejs folder in the server repo and replace local kubejs folder
        kubejs_files = github_utils.fetch_all(
            self.server_repo["url"],
            "kubejs",
            self.server_repo["branch"],
        )
        for file in kubejs_files:
            dest = Path(self.instance.kubejs_dir) / Path(file).relative_to("kubejs")
            dest.parent.mkdir(parents=True, exist_ok=True)
            github_utils.download_repo_file(
                self.server_repo["url"], file, self.server_repo["branch"], dest=dest
            )

    def update_modflared(self):
        modflared_files = github_utils.fetch_all(
            self.client_repo["url"],
            "modflared",
            self.client_repo["branch"],
        )
        for file in modflared_files:
            dest = Path(self.instance.modflared_dir) / Path(file).relative_to(
                "modflared"
            )
            dest.parent.mkdir(parents=True, exist_ok=True)
            github_utils.download_repo_file(
                self.client_repo["url"], file, self.client_repo["branch"], dest=dest
            )

    def update_mods(self):
        """
        Make the instance mods folder exactly match the client repo's mods folder, ignoring the .connector folder:
        - Remove any local file not in the repo (except .connector and its contents)
        - Download/update every file from the repo (preserving subfolders, except .connector)
        """
        import os
        repo_mods = github_utils.fetch_all(
            self.client_repo["url"],
            "mods",
            self.client_repo["branch"],
        )
        # Filter out any files in the .connector folder
        repo_mods = [f for f in repo_mods if not f.startswith("mods/.connector/") and f != "mods/.connector"]
        repo_mods_set = set(repo_mods)

        # Get all local files (recursively, relative to mods_dir)
        local_mods = []
        for root, _, files in os.walk(self.instance.mods_dir):
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), self.instance.mods_dir)
                rel_path = rel_path.replace("\\", "/")  # Normalize for Windows
                # Ignore files in .connector folder
                if rel_path.startswith(".connector/") or rel_path == ".connector":
                    continue
                local_mods.append(f"mods/{rel_path}")
        local_mods_set = set(local_mods)

        # Remove local files not in the repo
        for mod in local_mods_set - repo_mods_set:
            try:
                abs_path = os.path.join(self.instance.mods_dir, mod[len("mods/"):])
                os.remove(abs_path)
                logging.info(f"Removed mod: {mod}")
            except Exception as e:
                logging.error(f"Failed to remove mod {mod}: {e}")

        # Only download files that are missing locally (by name)

        local_mod_names = {os.path.basename(mod) for mod in local_mods}

        for repo_mod in repo_mods:
            mod_name = os.path.basename(repo_mod)
            if mod_name not in local_mod_names:
                dest = Path(self.instance.mods_dir) / Path(repo_mod).relative_to("mods")
                dest.parent.mkdir(parents=True, exist_ok=True)
                github_utils.download_repo_file(
                    self.client_repo["url"], repo_mod, self.client_repo["branch"], dest=dest
                )
                logging.info(f"Downloaded/updated mod: {repo_mod}")

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
