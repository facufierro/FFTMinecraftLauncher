import logging
from ..models.constants import Window
from ..ui.components.main_window import MainWindow
from ..ui.components.settings_window import SettingsWindow


class UIService:
    def __init__(self):
        logging.debug("Initializing UIService")
        self.main_window = MainWindow()
        self.settings_window = SettingsWindow()
        logging.debug("UIService initialized")

    def show(self, window: Window):
        logging.debug(f"Showing window: {window.value}")
        if window == Window.MAIN:
            self.main_window.show()
        elif window == Window.SETTINGS:
            self.settings_window.show()
