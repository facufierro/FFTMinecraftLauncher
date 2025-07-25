import logging
import json
import requests
import zipfile
from tqdm import tqdm
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..models.game import Game


class GameService:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.instance_dir = Path(self.root_dir, "instance")
        self.indexes_dir = Path(self.instance_dir, "assets", "indexes")
        self.game = Game()

    def update(self):
        if self._is_update_required():
            self._install(self.instance_dir)

    def _is_update_required(self):
        logging.debug("Checking if game update is required")
        return not (self.indexes_dir / f"{self.game.version}.json").exists()

    def _install(self, target_dir):
        vjson = self.get_version_json(self.game.version)
        client_url = vjson["downloads"]["client"]["url"]
        client_jar = target_dir / f"minecraft-{self.game.version}.jar"
        self.download_file(client_url, client_jar)
        libs_dir = target_dir / "libraries"
        lib_tasks = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            for lib in vjson["libraries"]:
                if "downloads" in lib and "artifact" in lib["downloads"]:
                    url = lib["downloads"]["artifact"]["url"]
                    path = libs_dir / Path(lib["downloads"]["artifact"]["path"])
                    if not path.exists():
                        lib_tasks.append(
                            executor.submit(self.download_file, url, path, False)
                        )
            for f in tqdm(
                as_completed(lib_tasks),
                total=len(lib_tasks),
                desc="Libraries",
                unit="lib",
            ):
                pass
        assets_dir = target_dir / "assets"
        assets_index_url = vjson["assetIndex"]["url"]
        assets_index_path = assets_dir / "indexes" / f"{self.game.version}.json"
        self.download_file(assets_index_url, assets_index_path)
        with open(assets_index_path) as f:
            assets = json.load(f)["objects"]
        asset_tasks = []
        with ThreadPoolExecutor(max_workers=16) as executor:
            for name, obj in assets.items():
                h = obj["hash"]
                url = f"https://resources.download.minecraft.net/{h[:2]}/{h}"
                path = assets_dir / "objects" / h[:2] / h
                if not path.exists():
                    asset_tasks.append(
                        executor.submit(self.download_file, url, path, False)
                    )
            for f in tqdm(
                as_completed(asset_tasks),
                total=len(asset_tasks),
                desc="Assets",
                unit="asset",
            ):
                pass

    def get_version_json(self, version):
        manifest = requests.get(self.game.manifest_url).json()
        for v in manifest["versions"]:
            if v["id"] == version:
                return requests.get(v["url"]).json()
        raise Exception(f"Version {version} not found")

    def download_file(self, url, dest, show_progress=True, max_retries=3):
        """Download a file with progress bar and validate as zip if .jar/.zip. Retries on failure."""
        for attempt in range(1, max_retries + 1):
            dest.parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(url, stream=True)
            total = int(r.headers.get("content-length", 0))
            print(
                f"[DEBUG] Downloading {url} (attempt {attempt}/{max_retries}), HTTP status: {r.status_code}"
            )
            if show_progress:
                bar = tqdm(
                    desc=dest.name, total=total, unit="B", unit_scale=True, leave=False
                )
            else:
                bar = None
            with open(dest, "wb") as f:
                for chunk in r.iter_content(1024 * 32):
                    f.write(chunk)
                    if bar:
                        bar.update(len(chunk))
            if bar:
                bar.close()
            # Print file size after download
            try:
                size = dest.stat().st_size
                print(f"[DEBUG] Downloaded file size: {size} bytes")
            except Exception:
                print(f"[DEBUG] Could not stat file {dest}")
            # Validate as zip if .jar or .zip
            is_zip = str(dest).endswith(".jar") or str(dest).endswith(".zip")
            valid = True
            if is_zip:
                try:
                    with zipfile.ZipFile(dest, "r") as zf:
                        bad = zf.testzip()
                        if bad is not None:
                            print(
                                f"[WARN] Corrupt zip entry {bad} in {dest}, retrying..."
                            )
                            valid = False
                except Exception as e:
                    print(
                        f"[WARN] Downloaded file {dest} is not a valid zip: {e}, retrying..."
                    )
                    # Print first 200 bytes of file for debugging
                    try:
                        with open(dest, "rb") as f:
                            snippet = f.read(200)
                            print(f"[DEBUG] First 200 bytes of file: {snippet}")
                    except Exception:
                        print(f"[DEBUG] Could not read file {dest}")
                    valid = False
            if valid:
                return
            else:
                try:
                    dest.unlink()
                except Exception:
                    pass
                if attempt == max_retries:
                    # Print first 200 bytes of HTTP response if not valid
                    try:
                        r2 = requests.get(url)
                        print(f"[DEBUG] HTTP status: {r2.status_code}")
                        print(
                            f"[DEBUG] First 200 bytes of HTTP response: {r2.content[:200]}"
                        )
                    except Exception:
                        print(f"[DEBUG] Could not fetch HTTP response for {url}")
                    raise Exception(
                        f"Failed to download a valid file from {url} after {max_retries} attempts."
                    )
