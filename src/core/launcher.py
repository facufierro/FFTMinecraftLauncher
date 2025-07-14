import logging
from ..services.ui_service import UIService, Window


class Launcher:
    def __init__(self):
        logging.debug("Initializing Launcher")
        self.ui = UIService()

    def run(self):
        logging.info("Running Launcher")
        self.ui.show(Window.MAIN)
