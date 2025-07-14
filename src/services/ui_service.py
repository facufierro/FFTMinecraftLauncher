import logging
from enum import Enum
from ..ui.components.main_window import MainWindow
from ..ui.components.settings_window import SettingsWindow


class Window(Enum):
    MAIN = MainWindow
    SETTINGS = SettingsWindow


class UIService:
    def __init__(self):
        logging.debug("UIService initialized")
        self.main_window = MainWindow()
        self.settings_window = SettingsWindow()

    def show(self, window: Window):
        logging.debug(f"Showing window: {window.value}")
        if window == Window.MAIN:
            self.main_window.show()
        elif window == Window.SETTINGS:
            self.settings_window.show()
