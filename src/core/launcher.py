import logging


from ..models.constants import INSTANCE_NAME, Component, Folder, File
from ..models.instance import Instance

from ..ui.components.update_dialog import UpdateDialog

from ..services.ui_service import UIService, Window
from ..services.github_service import GitHubService
from ..services.versions_service import VersionsService
from ..services.launcher_service import LauncherService
from ..services.profile_service import ProfileService
from ..services.java_service import JavaService
from ..services.loader_service import LoaderService
from ..services.instance_service import InstanceService
from ..services.file_service import FileService


class Launcher:
    def __init__(self):
        logging.info("Initializing Launcher...")
        self.instance = Instance(INSTANCE_NAME)
        self.ui_service = UIService()
        self.github_service = GitHubService()
        self.version_service = VersionsService(self.instance, self.github_service)
        self.launcher_service = LauncherService(
            self.version_service, self.github_service
        )
        self.profile_service = ProfileService()
        self.java_service = JavaService(self.version_service)
        self.loader_service = LoaderService(self.instance)
        self.file_service = FileService()
        self.instance_service = InstanceService(self.instance, self.file_service)

    def start(self):
        self.main_window = self.ui_service.show(Window.MAIN)
        self._check_launcher_update()
        self._set_up_profile()
        self._check_java_update()
        self._check_loader_update()

    def launch(self):
        logging.info("Launching the game")

    def exit(self):
        logging.info("Exiting the launcher")
        self.ui_service.main_window.close()

    def _check_launcher_update(self):
        if self.version_service.check_for_updates(Component.LAUNCHER):
            update_dialog: UpdateDialog = self.ui_service.show(Window.UPDATE)
            self.ui_service.close(Window.MAIN)
            update_dialog.accept_pressed.connect(self.launcher_service.update)
            update_dialog.exec()
        else:
            logging.info("Launcher is up to date.")

    def _check_java_update(self):
        try:
            if self.version_service.check_for_updates(Component.JAVA):
                update_dialog: UpdateDialog = self.ui_service.show(Window.UPDATE)
                self.ui_service.close(Window.MAIN)
                update_dialog.accept_pressed.connect(self.java_service.update)
                update_dialog.label.setText(
                    f"Java {self.instance.required_versions.get(Component.JAVA.value)}+ is needed. \nA browser window will open to the Java download page."
                )
                update_dialog.exec()
            else:
                logging.info("Java is up to date.")
        except Exception as e:
            logging.error(f"Failed to check Java update: {e}")

    def _check_loader_update(self):
        try:
            if self.version_service.check_for_updates(Component.LOADER):
                logging.info("Loader update is needed.")
                self.loader_service.update_finished.connect(self.update_instance)
                self.main_window.on_launch_button_clicked(self.loader_service.update)
            else:
                logging.info("Loader is up to date.")
                self.main_window.on_launch_button_clicked(self.update_instance)
        except Exception as e:
            logging.error(f"Failed to check Loader update: {e}")

    def _set_up_profile(self):
        try:
            logging.info("Setting up profile...")
            self.profile = self.profile_service.get_profile_data()
            if self.profile:
                logging.info("Profile loaded successfully: %s", self.profile.name)
                logging.debug("Profile data: \n%s", self.profile.__repr__())
            else:
                logging.warning("No profile found, creating a new one")
                self.profile_service.update_profile()
            self.profile_service.add_profile_to_instance()
        except Exception as e:
            logging.error(f"Failed to set up profile: {e}")

    def update_instance(self):
        self.instance_service.update_config(
            self.github_service.get_folder(Folder.DEFAULTCONFIGS.value)
        )
        self.instance_service.update_kubejs(
            self.github_service.get_folder(Folder.KUBEJS.value)
        )
        self.instance_service.update_modflared(
            self.github_service.get_folder(Folder.MODFLARED.value)
        )
        self.instance_service.update_mods(
            self.github_service.get_folder(Folder.MODS.value)
        )
        self.instance_service.update_resourcepacks(
            self.github_service.get_folder(Folder.RESOURCEPACKS.value)
        )
        self.instance_service.update_shaderpacks(
            self.github_service.get_folder(Folder.SHADERPACKS.value)
        )
        self.file_service.replace_file(
            File.SERVERS.value, self.github_service.get_file(File.SERVERS.value)
        )
