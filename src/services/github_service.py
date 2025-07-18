import logging
import os
import requests
import zipfile
import io
from ..models.constants import Url, Branch
import json


class GitHubService:
    def __init__(self):
        logging.debug("GitHubService initialized")

    def get_file(self, file_path, branch, repo_url):
        repo_url = repo_url.rstrip("/")
        
        # Extract just the filename from the full path
        # e.g., "d:\path\to\instance\servers.dat" -> "servers.dat"
        filename = os.path.basename(file_path)
        
        branch = branch
        raw_url = (
            repo_url.replace("github.com", "raw.githubusercontent.com")
            + f"/{branch}/{filename}"
        )
        try:
            response = requests.get(raw_url, timeout=10)
            if response.status_code == 200:
                logging.debug(f"Downloaded {filename} from {branch} branch.")
                
                # Return JSON for .json files, raw content for others
                if filename.endswith('.json'):
                    return json.loads(response.text)
                else:
                    return response.content
            else:
                logging.warning(
                    f"Failed to fetch {filename} from {branch}, status code: {response.status_code}"
                )
        except Exception as e:
            logging.error(f"Error fetching {filename} from {raw_url}: {e}")
        logging.error(f"Could not fetch {filename} from branch {branch}.")
        return None

    def get_folder(self, folder_name, branch, repo_url):
        """
        Download a specific folder from the GitHub repo.
        Returns a zip file containing only the requested folder content, else None.
        """
        repo_url = repo_url.rstrip("/")
        
        # folder_name should now be the actual repository folder name
        # e.g., "configureddefaults", "mods", etc.
        
        branch = branch
        zip_url = repo_url + f"/archive/refs/heads/{branch}.zip"
        
        try:
            response = requests.get(zip_url, timeout=20)
            if response.status_code == 200:
                logging.debug(f"Downloaded zip for branch {branch}.")
                
                # Extract the repository name from the URL
                repo_name = repo_url.split("/")[-1]
                expected_root = f"{repo_name}-{branch}/"
                target_folder_in_zip = f"{expected_root}{folder_name}/"
                
                logging.debug(f"Looking for folder: {target_folder_in_zip}")
                
                # Create a new zip containing only the requested folder
                output_zip = io.BytesIO()
                files_found = 0
                
                with zipfile.ZipFile(io.BytesIO(response.content), 'r') as input_zip:
                    # Log all files to see what's actually in the zip
                    logging.debug(f"Files in zip: {[f.filename for f in input_zip.filelist[:10]]}")  # Show first 10
                    
                    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as output_zip_file:
                        for file_info in input_zip.filelist:
                            if file_info.filename.startswith(target_folder_in_zip):
                                # Remove the repository root and folder path from the filename
                                relative_path = file_info.filename[len(target_folder_in_zip):]
                                if relative_path and not file_info.is_dir():  # Skip directories and empty paths
                                    file_data = input_zip.read(file_info.filename)
                                    output_zip_file.writestr(relative_path, file_data)
                                    files_found += 1
                                    logging.debug(f"Added file: {relative_path}")
                
                output_zip.seek(0)
                result = output_zip.getvalue()
                
                if files_found > 0:
                    logging.debug(f"Extracted {files_found} files from folder {folder_name} from {branch} branch.")
                    return result
                else:
                    logging.warning(f"No files found in folder {folder_name} from {branch} branch.")
                    return None
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

    def get_release_file(self, asset_name, repo_url):
        """
        Download a file (asset) from the latest GitHub release by asset name.
        Returns the file content as bytes if found, else None.
        """
        repo_url = repo_url.rstrip("/")
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
