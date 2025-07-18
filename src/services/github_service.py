import logging
import requests
from ..models.constants import Url
import json


class GitHubService:
    def __init__(self):
        try:
            self.repo_url = Url.GITHUB_REPO.value
            self.branch = "refactor"
            logging.debug("GitHubService initialized")
        except Exception as e:
            logging.critical(f"Error initializing GitHubService: {e}")
            raise e

    def get_file(self, file_path):
        repo_url = self.repo_url.rstrip("/")
        branch = self.branch
        raw_url = (
            repo_url.replace("github.com", "raw.githubusercontent.com")
            + f"/{branch}/{file_path.lstrip('/')}"
        )
        try:
            response = requests.get(raw_url, timeout=10)
            if response.status_code == 200:
                logging.debug(f"Downloaded {file_path} from {branch} branch.")
                return json.loads(response.text)  # Parse response as JSON
            else:
                logging.warning(
                    f"Failed to fetch {file_path} from {branch}, status code: {response.status_code}"
                )
        except Exception as e:
            logging.error(f"Error fetching {file_path} from {raw_url}: {e}")
        logging.error(f"Could not fetch {file_path} from branch {branch}.")
        return None

    def get_folder(self, folder_path):
        """
        Download a zip archive of a folder from the GitHub repo, searching main, dev, refactor branches.
        Returns the zip file content as bytes if found, else None.
        """
        repo_url = self.repo_url.rstrip("/")
        folder_path = folder_path.strip("/")
        branch = self.branch
        zip_url = repo_url + f"/archive/refs/heads/{branch}.zip"
        try:
            response = requests.get(zip_url, timeout=20)
            if response.status_code == 200:
                logging.debug(f"Downloaded zip for branch {branch}.")
                return response.content
            else:
                logging.warning(
                    f"Failed to fetch zip from {branch}, status code: {response.status_code}"
                )
        except Exception as e:
            logging.error(f"Error fetching zip from {zip_url}: {e}")
        logging.error(f"Could not fetch zip for branch {branch}.")
        return None

    def save_file(self, content, dest_path):
        """
        Save text content to a file on disk.
        """
        try:
            with open(dest_path, "w", encoding="utf-8") as f:
                f.write(content)
            logging.info(f"Saved file to {dest_path}")
        except Exception as e:
            logging.error(f"Failed to save file to {dest_path}: {e}")

    def save_folder(self, content, dest_path):
        """
        Save binary content (e.g., zip) to a file on disk.
        """
        try:
            with open(dest_path, "wb") as f:
                f.write(content)
            logging.info(f"Saved folder (zip) to {dest_path}")
        except Exception as e:
            logging.error(f"Failed to save folder to {dest_path}: {e}")

    def get_release_file(self, asset_name):
        """
        Download a file (asset) from the latest GitHub release by asset name.
        Returns the file content as bytes if found, else None.
        """
        repo_url = self.repo_url.rstrip("/")
        owner_repo = repo_url.replace("https://github.com/", "")
        api_url = f"https://api.github.com/repos/{owner_repo}/releases/latest"
        try:
            response = requests.get(api_url, timeout=15)
            if response.status_code != 200:
                logging.error(
                    f"Failed to fetch release info, status code: {response.status_code}"
                )
                return None
            release = response.json()
            for asset in release.get("assets", []):
                if asset.get("name") == asset_name:
                    download_url = asset.get("browser_download_url")
                    asset_resp = requests.get(download_url, timeout=30)
                    if asset_resp.status_code == 200:
                        logging.info(f"Downloaded release asset: {asset_name}")
                        return asset_resp.content
                    logging.error(
                        f"Failed to download asset {asset_name}, status code: {asset_resp.status_code}"
                    )
                    return None
            logging.error(f"Asset {asset_name} not found in latest release.")
        except Exception as e:
            logging.error(f"Error fetching release asset {asset_name}: {e}")
        return None
