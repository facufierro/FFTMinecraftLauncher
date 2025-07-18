import logging
from ..models.constants import Window
from ..ui.components.main_window import MainWindow
from ..ui.components.settings_window import SettingsWindow


class UIService:
    def __init__(self):
        self.main_window = MainWindow()
        self.settings_window = SettingsWindow()
        logging.debug("UIService initialized")

    def show(self, window: Window):
        try:
            if window == Window.MAIN:
                self.main_window.show()
            elif window == Window.SETTINGS:
                self.settings_window.show()
        except Exception as e:
            logging.error(f"Failed to show window {window}: {e}")
