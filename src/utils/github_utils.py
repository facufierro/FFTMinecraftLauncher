import logging
import requests


def get_release_file(file_name: str, repo: str):
    try:
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        for asset in data.get("assets", []):
            if asset["name"] == file_name:
                download_url = asset["browser_download_url"]
                file_response = requests.get(download_url)
                file_response.raise_for_status()
                return file_response.content
        logging.warning(f"File '{file_name}' not found in the latest release.")
        return None
    except requests.RequestException as e:
        logging.error(f"Failed to fetch release file: {e}")
        return None


def get_release_version(repo_url):
    """
    Fetch the latest release version (tag name) from the GitHub repo.
    Returns the tag name as a string, or None if not found.
    """
    repo_url = repo_url.rstrip("/")
    owner_repo = repo_url.replace("https://github.com/", "")
    api_url = f"https://api.github.com/repos/{owner_repo}/releases/latest"
    try:
        response = requests.get(api_url, timeout=15)
        if response.status_code != 200:
            logging.warning(
                f"Failed to fetch release info, status code: {response.status_code}"
            )
            return None
        release = response.json()
        tag_name = release.get("tag_name")
        if tag_name:
            # Remove leading 'v' if present (e.g., v2.0.0 -> 2.0.0)
            return tag_name.lstrip("v")
        return None
    except Exception as e:
        logging.error(f"Error fetching latest release version: {e}")
    return None


def get_all_config_files(repo_url, branch="main"):
    """
    Recursively get all file paths inside the 'config' folder of a GitHub repo using the tree API.
    Returns a list of file paths (relative to repo root).
    """
    repo_url = repo_url.rstrip("/")
    owner_repo = repo_url.replace("https://github.com/", "")
    api_url = f"https://api.github.com/repos/{owner_repo}/git/trees/{branch}?recursive=1"
    try:
        response = requests.get(api_url, timeout=15)
        response.raise_for_status()
        data = response.json()
        files = [item["path"] for item in data.get("tree", [])
                 if item["type"] == "blob" and item["path"].startswith("config/")]
        return files
    except Exception as e:
        logging.error(f"Error fetching config files recursively: {e}")
        return []
