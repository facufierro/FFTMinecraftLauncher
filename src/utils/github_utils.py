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


def fetch_all(repo_url, folder, branch="main"):
    """
    Recursively get all file paths inside the specified folder of a GitHub repo using the tree API.
    Returns a list of file paths (relative to repo root).
    """
    repo_url = repo_url.rstrip("/")
    owner_repo = repo_url.replace("https://github.com/", "")
    try:
        # 1. Get branch info to find commit SHA
        branch_url = f"https://api.github.com/repos/{owner_repo}/branches/{branch}"
        branch_resp = requests.get(branch_url, timeout=15)
        branch_resp.raise_for_status()
        commit_sha = branch_resp.json()["commit"]["sha"]

        # 2. Get the tree for the commit
        tree_url = f"https://api.github.com/repos/{owner_repo}/git/trees/{commit_sha}"
        tree_resp = requests.get(tree_url, timeout=15)
        tree_resp.raise_for_status()
        tree = tree_resp.json()["tree"]

        # 3. Find the folder in the tree
        folder_entry = next(
            (
                item
                for item in tree
                if item["path"] == folder and item["type"] == "tree"
            ),
            None,
        )
        if not folder_entry:
            logging.error(f"Folder '{folder}' not found in repo tree.")
            return []
        folder_sha = folder_entry["sha"]

        # 4. Get the tree for the folder
        folder_tree_url = (
            f"https://api.github.com/repos/{owner_repo}/git/trees/{folder_sha}"
        )
        folder_tree_resp = requests.get(folder_tree_url, timeout=15)
        folder_tree_resp.raise_for_status()
        folder_tree = folder_tree_resp.json()["tree"]

        # 5. List all files (blobs) in the folder (non-recursive)
        files = [item["path"] for item in folder_tree if item["type"] == "blob"]
        return [f"{folder}/{f}" for f in files]
    except Exception as e:
        logging.error(f"Error fetching config files recursively: {e}")
        return []


def download_repo_file(repo_url, file_path, branch="main", dest=None):
    """
    Download a single file from a GitHub repo (raw content) to dest.
    If dest is None, returns the content as bytes. Otherwise, writes to dest.
    """
    repo_url = repo_url.rstrip("/")
    owner_repo = repo_url.replace("https://github.com/", "")
    raw_url = f"https://raw.githubusercontent.com/{owner_repo}/{branch}/{file_path}"
    resp = requests.get(raw_url, timeout=15)
    resp.raise_for_status()
    if dest:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(resp.content)
        return dest
    return resp.content
