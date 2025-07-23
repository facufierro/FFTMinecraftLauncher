import logging
import os
import requests
import zipfile
import io
from ..models.constants import Url, Branch
import json


class GitHubService:

    def list_files_in_folder(self, folder, branch, repo_url):
        """List files in a folder of the repo using the GitHub API."""
        import requests
        import logging
        try:
            parts = repo_url.rstrip('/').split('/')
            owner, repo = parts[-2], parts[-1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{folder}?ref={branch}"
            resp = requests.get(api_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {item['name']: item for item in data if item['type'] == 'file'}
            else:
                logging.warning(f"GitHub API returned status {resp.status_code} for {api_url}")
                return None
        except Exception as e:
            logging.error(f"Error listing files in {folder}: {e}")
            return None

    def download_file_from_repo(self, path, branch, repo_url):
        """Download a single file from the repo using the raw URL."""
        import requests
        import logging
        try:
            parts = repo_url.rstrip('/').split('/')
            owner, repo = parts[-2], parts[-1]
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
            resp = requests.get(raw_url, timeout=20)
            if resp.status_code == 200:
                return resp.content
            else:
                logging.warning(f"Failed to download {path} (status {resp.status_code})")
                return None
        except Exception as e:
            logging.error(f"Error downloading {path}: {e}")
            return None

    def get_mod_filenames_from_github(self, branch, repo_url):
        """Fetch the list of mod filenames in the mods folder from the GitHub repo using the API (no zip download)."""
        import requests
        import logging
        # repo_url: e.g. https://github.com/facufierro/FFTClientMinecraft1211
        try:
            parts = repo_url.rstrip('/').split('/')
            owner, repo = parts[-2], parts[-1]
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/mods?ref={branch}"
            resp = requests.get(api_url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                # Only include files (not directories)
                filenames = set(item['name'] for item in data if item['type'] == 'file')
                logging.info(f"Fetched {len(filenames)} mod filenames from GitHub API.")
                return filenames
            else:
                logging.warning(f"GitHub API returned status {resp.status_code} for {api_url}")
                return None
        except Exception as e:
            logging.error(f"Error fetching mod filenames from GitHub: {e}")
            return None

    def get_latest_release_version(self, repo_url):
        """
        Fetch the latest release version (tag name) from the GitHub repo.
        Returns the tag name as a string, or None if not found.
        """
        repo_url = repo_url.rstrip("/")
        owner_repo = repo_url.replace("https://github.com/", "")
        api_url = f"https://api.github.com/repos/{owner_repo}/releases/latest"
        try:
            response = self.session.get(api_url, timeout=15)
            if response.status_code != 200:
                logging.warning(f"Failed to fetch release info, status code: {response.status_code}")
                return None
            release = response.json()
            tag_name = release.get("tag_name")
            if tag_name:
                # Remove leading 'v' if present (e.g., v2.0.0 -> 2.0.0)
                return tag_name.lstrip('v')
            return None
        except Exception as e:
            logging.error(f"Error fetching latest release version: {e}")
        return None
    def __init__(self, progress_callback=None):
        logging.debug("GitHubService initialized")
    # Removed cache: always download fresh
        self.progress_callback = progress_callback  # Callback for progress updates
        
        # Create optimized session for faster downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FFT-Minecraft-Launcher/2.0.0',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        # Configure connection pooling for better performance
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=10,
            pool_maxsize=20,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

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
            response = self.session.get(raw_url, timeout=10)
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
        # For single folder requests, use a temporary directory approach
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            success = self.extract_folders_directly([folder_name], branch, repo_url, temp_dir)
            if not success:
                return None
            
            # Create a zip from the extracted folder
            local_folder_name = self._get_local_folder_name(folder_name)
            folder_path = os.path.join(temp_dir, local_folder_name)
            
            if not os.path.exists(folder_path):
                return None
            
            # Create zip in memory
            output_zip = io.BytesIO()
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, folder_path)
                        zip_file.write(file_path, arcname)
            
            output_zip.seek(0)
            return output_zip.getvalue()

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
            logging.debug(f"[RELEASE DEBUG] Fetching release info from: {api_url}")
            response = self.session.get(api_url, timeout=15)
            logging.debug(f"[RELEASE DEBUG] GitHub API status code: {response.status_code}")
            if response.status_code != 200:
                logging.warning(
                    f"Failed to fetch release info, status code: {response.status_code}"
                )
                return None
            release = response.json()
            asset_names = [asset.get("name") for asset in release.get("assets", [])]
            logging.debug(f"[RELEASE DEBUG] Searching for asset: '{asset_name}'")
            logging.debug(f"[RELEASE DEBUG] Assets found in latest release: {asset_names}")
            found = False
            for asset in release.get("assets", []):
                asset_name_actual = asset.get('name')
                logging.debug(f"[RELEASE DEBUG] Comparing asset: '{asset_name_actual}' to requested: '{asset_name}'")
                if asset_name_actual == asset_name:
                    found = True
                    download_url = asset.get("browser_download_url")
                    logging.debug(f"[RELEASE DEBUG] Downloading asset from: {download_url}")
                    asset_resp = self.session.get(download_url, timeout=30)
                    logging.debug(f"[RELEASE DEBUG] Asset download status code: {asset_resp.status_code}")
                    if asset_resp.status_code == 200:
                        logging.info(f"Downloaded release asset: {asset_name}")
                        return asset_resp.content
                    logging.error(
                        f"Failed to download asset {asset_name}, status code: {asset_resp.status_code}"
                    )
                    return None
            if not found:
                logging.warning(f"Asset '{asset_name}' not found in latest release. Assets available: {asset_names}")
        except Exception as e:
            logging.error(f"Error fetching release asset {asset_name}: {e}")
        return None

    def _get_repo_zip(self, branch, repo_url):
        """
        Always download the repository zip file fresh (no cache).
        Returns the zip content as bytes.
        """
        repo_url = repo_url.rstrip("/")
        zip_url = repo_url + f"/archive/refs/heads/{branch}.zip"
        try:
            logging.info(f"Downloading repository zip from {zip_url}")
            self._update_progress(0, "Starting download...", "Connecting to GitHub")
            response = self.session.get(zip_url, timeout=60, stream=True)
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                if total_size > 0:
                    size_mb = total_size / 1024 / 1024
                    logging.info(f"Repository size: {size_mb:.1f}MB")
                    self._update_progress(5, f"Downloading {size_mb:.1f}MB repository", "Download started")
                else:
                    logging.info("Repository size unknown, starting download...")
                    self._update_progress(5, "Downloading repository", "Download started")
                content = b""
                chunk_size = 1048576  # 1MB
                downloaded = 0
                last_progress_update = 0
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        content += chunk
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = 5 + int((downloaded / total_size) * 85)
                            current_mb = downloaded / 1024 / 1024
                            if current_mb >= last_progress_update + 10 or progress >= last_progress_update + 5 or downloaded == total_size:
                                last_progress_update = max(current_mb, progress)
                                mb_total = total_size / 1024 / 1024
                                self._update_progress(
                                    progress,
                                    f"Downloading repository ({current_mb:.1f}/{mb_total:.1f}MB)",
                                    f"{progress-5:.1f}% complete"
                                )
                        else:
                            current_mb = downloaded / 1024 / 1024
                            if current_mb >= last_progress_update + 10:
                                last_progress_update = current_mb
                                progress = min(5 + int(current_mb * 5), 85)
                                self._update_progress(
                                    progress,
                                    f"Downloading repository ({current_mb:.1f}MB)",
                                    "Download in progress..."
                                )
                download_mb = len(content) / 1024 / 1024
                logging.info(f"Downloaded {download_mb:.1f}MB for branch {branch}")
                self._update_progress(90, "Download complete", "Processing repository data")
                return content
            else:
                logging.warning(f"Failed to fetch zip from {branch}, status code: {response.status_code}")
                self._update_progress(0, "Download failed", f"HTTP {response.status_code}")
        except Exception as e:
            logging.error(f"Error fetching zip from {zip_url}: {e}")
            self._update_progress(0, "Download error", str(e))
        return None

    def extract_folders_directly(self, folder_names, branch, repo_url, base_extract_path):
        """
        Download repo once and extract folders directly to filesystem.
        Much more efficient than creating intermediate zip files.
        """
        repo_content = self._get_repo_zip(branch, repo_url)
        if repo_content is None:
            logging.error("Failed to download repository")
            return False
        
        repo_name = repo_url.split("/")[-1]
        expected_root = f"{repo_name}-{branch}/"
        
        try:
            self._update_progress(92, "Processing zip file...", "Reading repository structure")
            with zipfile.ZipFile(io.BytesIO(repo_content), 'r') as zip_ref:
                logging.info(f"Extracting {len(folder_names)} folders directly to filesystem...")
                self._update_progress(95, "Extracting folders...", f"Processing {len(folder_names)} folders")
                
                for i, folder_name in enumerate(folder_names):
                    folder_progress = 95 + int((i / len(folder_names)) * 5)  # 95-100%
                    self._update_progress(folder_progress, f"Extracting {folder_name}...", f"Folder {i+1}/{len(folder_names)}")
                    
                    target_folder_in_zip = f"{expected_root}{folder_name}/"
                    files_extracted = 0
                    
                    # Determine local folder mapping
                    local_folder_name = self._get_local_folder_name(folder_name)
                    extract_path = os.path.join(base_extract_path, local_folder_name)
                    
                    # Clear existing folder for clean update
                    if os.path.exists(extract_path):
                        import shutil
                        shutil.rmtree(extract_path)
                        logging.debug(f"Cleared existing folder: {local_folder_name}")
                    
                    # Create directory
                    os.makedirs(extract_path, exist_ok=True)
                    
                    # Extract files directly
                    for file_info in zip_ref.filelist:
                        if file_info.filename.startswith(target_folder_in_zip) and not file_info.is_dir():
                            # Get relative path within the folder
                            relative_path = file_info.filename[len(target_folder_in_zip):]
                            if relative_path:
                                # Full local path
                                local_file_path = os.path.join(extract_path, relative_path)
                                
                                # Create subdirectories if needed
                                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                                
                                # Extract file directly
                                with zip_ref.open(file_info) as source:
                                    with open(local_file_path, 'wb') as target:
                                        # Copy in chunks for memory efficiency
                                        while True:
                                            chunk = source.read(8192)
                                            if not chunk:
                                                break
                                            target.write(chunk)
                                
                                files_extracted += 1
                    
                    if files_extracted > 0:
                        logging.info(f"Extracted {files_extracted} files to {local_folder_name}/")
                    else:
                        logging.warning(f"No files found for folder {folder_name}")
                
                self._update_progress(100, "Extraction complete!", f"Successfully processed {len(folder_names)} folders")
                return True
                
        except Exception as e:
            logging.error(f"Error extracting folders: {e}")
            return False

    def _get_local_folder_name(self, repo_folder_name):
        """Map repository folder names to local folder names"""
        folder_mapping = {
            "configureddefaults": "configs",
            "kubejs": "kubejs", 
            "modflared": "modflared",
            "mods": "mods",
            "resourcepacks": "resourcepacks",
            "shaderpacks": "shaderpacks"
        }
        return folder_mapping.get(repo_folder_name, repo_folder_name)

    def clear_cache(self):
        """No-op: cache removed, always downloads fresh."""
        logging.debug("Repository cache cleared (noop, always downloads fresh)")

    def _update_progress(self, progress, status, details=None):
        """Update progress if callback is available"""
        if self.progress_callback:
            try:
                self.progress_callback(progress, status, details)
            except Exception as e:
                logging.warning(f"Progress callback failed: {e}")
