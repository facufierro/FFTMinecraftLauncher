import logging
from ..services.version_service import VersionService


class JavaService:
    def __init__(self, version_service: VersionService):
        logging.debug("Initializing JavaService")
        self.version_service = version_service

    def update(self):
        logging.info("Updating Java")
        try:
            pass
        except Exception as e:
            logging.error("Failed to update Java: %s", e)
            raise
