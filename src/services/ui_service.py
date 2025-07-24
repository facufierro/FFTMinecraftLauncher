import logging
from ..ui.components.main_window import MainWindow
from ..ui.components.settings_window import SettingsWindow
from ..ui.components.update_dialog import UpdateDialog


class UIService:
    def __init__(self):
        self.main_window = MainWindow()
        self.settings_window = SettingsWindow()
        self.update_dialog = UpdateDialog()
        logging.debug("UIService initialized")

    def show_main(self):
        self.main_window.show()
        return self.main_window

    def show_settings(self):
        self.settings_window.show()
        return self.settings_window

    def show_update(self):
        self.update_dialog.show()
        return self.update_dialog

    def close_main(self):
        if self.main_window.isVisible():
            self.main_window.close()
            logging.debug("Main window closed")
        else:
            logging.warning("Main window is not visible, cannot close")

    def close_settings(self):
        if self.settings_window.isVisible():
            self.settings_window.close()
            logging.debug("Settings window closed")
        else:
            logging.warning("Settings window is not visible, cannot close")

    def close_update(self):
        if self.update_dialog.isVisible():
            self.update_dialog.close()
            logging.debug("Update dialog closed")
        else:
            logging.warning("Update dialog is not visible, cannot close")

    def get_progress_callback(self):
        def progress_callback(progress, status, details=None):
            logging.debug(f"Progress update: {progress}% - {status} - {details}")
            if hasattr(self.main_window, "progress_bar"):
                self.main_window.progress_bar.set_progress(progress, status, details)
                logging.debug(f"Progress bar updated: {progress}%")
            else:
                logging.warning("No progress bar found in main window")

        return progress_callback
