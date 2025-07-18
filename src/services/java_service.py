import logging
import webbrowser
from ..services.version_service import VersionService


class JavaService:
    def __init__(self, version_service: VersionService):
        logging.debug("Initializing JavaService")
        self.version_service = version_service

    def update(self):
        webbrowser.open("https://www.oracle.com/java/technologies/downloads/")
        try:
            pass
        except Exception as e:
            logging.error("Failed to update Java: %s", e)
            raise
