import logging
from ..models.constants import Window
from ..ui.components.main_window import MainWindow
from ..ui.components.settings_window import SettingsWindow
from ..ui.components.update_dialog import UpdateDialog


class UIService:
    def __init__(self):
        self.main_window = MainWindow()
        self.settings_window = SettingsWindow()
        self.update_dialog = UpdateDialog()
        logging.debug("UIService initialized")

    def show(self, window: Window):
        match window:
            case Window.MAIN:
                self.main_window.show()
                return self.main_window
            case Window.SETTINGS:
                self.settings_window.show()
                return self.settings_window
            case Window.UPDATE:
                self.update_dialog.show()
                return self.update_dialog
            case _:
                logging.warning(f"Unknown window: {window}")

    def close(self, window: Window):
        match window:
            case Window.MAIN:
                self.main_window.close()
            case Window.SETTINGS:
                self.settings_window.close()
            case Window.UPDATE:
                self.update_dialog.close()
            case _:
                logging.warning(f"Unknown window: {window}")
