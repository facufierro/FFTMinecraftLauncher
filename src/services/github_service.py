import logging
import os
import json
import requests
from ..models.constants import Urls


class GitHubService:
    def __init__(self):
        self.repo_url = Urls.GITHUB_REPO.value
        logging.debug("Initializing GitHubService with repo URL: %s", self.repo_url)
        self.launcher_version, self.loader_version, self.minecraft_version = (
            self._get_versions()
        )

    def _get_versions(self):
        logging.info("Fetching versions from GitHub repository: %s", self.repo_url)
        repo_url = self.repo_url.rstrip("/")
        for branch in ["main", "dev", "refactor"]:
            raw_url = (
                repo_url.replace("github.com", "raw.githubusercontent.com")
                + f"/{branch}/versions.json"
            )
            try:
                response = requests.get(raw_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    launcher_version = data.get("launcher")
                    loader_version = data.get("loader")
                    minecraft_version = data.get("minecraft")
                    logging.debug(
                        "Current Versions: \nLauncher version: %s, \nLoader version: %s, \nMinecraft version: %s",
                        launcher_version,
                        loader_version,
                        minecraft_version,
                    )
                    return (
                        launcher_version,
                        loader_version,
                        minecraft_version,
                    )
                else:
                    logging.warning(
                        f"Failed to fetch versions.json from {branch}, status code: {response.status_code}"
                    )
            except Exception as e:
                logging.error(f"Error fetching versions.json from {raw_url}: {e}")
        logging.error("Could not fetch versions.json from any known branch.")
        return (None, None, None)

    def get_mods(self):
        logging.debug("Fetching mods from GitHub")
        # Logic to fetch the list of mods from GitHub
        # This could involve making an API call to the GitHub repository
        # and parsing the response to get the list of mods.
        return ["mod1", "mod2", "mod3"]
