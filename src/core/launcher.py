import os
import sys
import logging
import signal
from PySide6.QtCore import QThread, QCoreApplication, Signal

from ..ui.components.update_dialog import UpdateDialog
from ..services.ui_service import UIService
from ..services.launcher_service import LauncherService
from ..services.profile_service import ProfileService
from ..services.java_service import JavaService
from ..services.loader_service import LoaderService
from ..services.instance_service import InstanceService
from ..services.file_service import FileService
from ..version import __version__


class Launcher:
    def __init__(self, root_dir: str):
        logging.info("Initializing Launcher...")
        self.minecraft_dir = os.path.join(os.getenv("APPDATA", ""), ".minecraft")
        self.root_dir = root_dir

        self.ui_service = UIService()

        self.file_service = FileService()

        self.profile_service = ProfileService(self.root_dir)
        self.java_service = JavaService()
        self.loader_service = LoaderService(self.root_dir, self.minecraft_dir)
        self.instance_service = InstanceService(self.root_dir, self.file_service)
        self.launcher_service = LauncherService(
            self.root_dir, self.minecraft_dir, self.loader_service.loader
        )

    def start(self):
        self.main_window = self.ui_service.show_main()
        # self.launcher_service.update()
        self.main_window.on_launch_button_clicked(self.launch)

    def launch(self):
        self.main_window.set_launch_button_enabled(False)
        self.main_window.set_launch_button_text("Updating...")
        self.profile_service.update()
        self.java_service.update()
        # self.loader_service.update()
        self.main_window.set_launch_button_text("Launching...")

        # Get profile data from the ProfileService or models
        # Assuming ProfileService has a method get_active_profile() or similar
        if hasattr(self.profile_service, "get_active_profile"):
            profile_data = self.profile_service.get_active_profile()
        elif hasattr(self.profile_service, "profile"):
            profile_data = self.profile_service.profile
        else:
            profile_data = {}

        game_launched = self.launcher_service.launch_game()

        if game_launched:
            logging.info("Minecraft launched successfully")
            self.exit()
        else:
            logging.error("Failed to launch Minecraft")
            # Re-enable button after failed launch
            if hasattr(self, "ui_service") and hasattr(self.ui_service, "main_window"):
                main_window = self.ui_service.main_window
                if hasattr(main_window, "launch_button"):
                    main_window.launch_button.setEnabled(True)
                    main_window.launch_button.setText("Launch")

    def exit(self):
        logging.info("Exiting the launcher")
        self.ui_service.main_window.close()
        # Ensure Qt event loop and process exit
        QCoreApplication.quit()
        try:
            sys.exit(0)
        finally:
            # As a last resort, force kill the process
            os.kill(os.getpid(), signal.SIGTERM)
