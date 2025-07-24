import logging
import re
import subprocess
import webbrowser


class JavaService:
    def __init__(self):
        logging.debug("Initializing JavaService")
        self.required_version = "17"

    def update(self):
        try:
            if any(self._is_update_required()):
                logging.info("Java update is needed.")
                webbrowser.open("https://www.oracle.com/java/technologies/downloads/")
            else:
                logging.info("Java is up to date.")
        except Exception as e:
            logging.error("Failed to update Java: %s", e)
            raise

    def _is_update_required(self):
        try:
            required_version = self.required_version
            current_version = self._get_java_current_version()
            logging.info(
                "Checking for updates for java: current %s vs required %s",
                current_version,
                required_version,
            )
            if not current_version or not required_version:
                logging.error("Current or required Java version is not set.")
                yield True
            else:
                yield int(current_version) < int(required_version)
        except Exception as e:
            logging.error("Error checking Java update: %s", e)
            yield False

    def _get_java_current_version(self):
        try:
            result = subprocess.run(
                ["java", "-version"], capture_output=True, text=True, check=False
            )
            if result.stderr:
                version_output = result.stderr.splitlines()[0]
                match = re.search(r"\d+\.\d+\.\d+", version_output)
                if match:
                    return self._extract_major_version(match.group(0))
            return None
        except FileNotFoundError:

            logging.error("Java executable not found.")
            return None

    def _extract_major_version(self, version_string):
        try:
            match = re.search(r"(\d+)(?:\.\d+)?", version_string)
            if match:
                return match.group(1)
            logging.warning(
                "Could not extract major version from string: %s", version_string
            )
            return None
        except Exception as e:
            logging.error("Error extracting major version: %s", e)
            return None
