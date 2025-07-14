import logging
from ..models.constants import Urls


class GitHubService:
    def __init__(self):
        self.repo_url = Urls.GITHUB_REPO.value
        self.versions_file = "versions.json"
        logging.debug("Initializing GitHubService with repo URL: %s", self.repo_url)
        # Initialize any necessary attributes or configurations
        pass

    def get_minecraft_version(self):
        logging.debug("Fetching Minecraft version from GitHub")
        # Logic to fetch the latest Minecraft version from GitHub
        # This could involve making an API call to the GitHub repository
        # and parsing the response to get the version number.
        return "1.20.2"

    def get_loader_version(self):
        logging.debug("Fetching Loader version from GitHub")
        # Logic to fetch the latest Loader version from GitHub
        # This could involve making an API call to the GitHub repository
        # and parsing the response to get the version number.
        return "1.0.0"

    def get_mods(self):
        logging.debug("Fetching mods from GitHub")
        # Logic to fetch the list of mods from GitHub
        # This could involve making an API call to the GitHub repository
        # and parsing the response to get the list of mods.
        return ["mod1", "mod2", "mod3"]
