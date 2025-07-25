import logging
import json
import requests
import zipfile
from tqdm import tqdm
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..models.game import Game
from ..utils import file_utils, version_utils


class GameService:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.instance_dir = Path(self.root_dir, "instance")
        self.indexes_dir = Path(self.instance_dir, "assets", "indexes")
        self.game = Game()

    def update(self):
        if self._is_update_required():
            logging.info("[ASSETS] Asset index missing or update required, installing...")
            self._install(self.instance_dir)
        else:
            # Validate asset index
            index_path = self.indexes_dir / f"{self.game.version}.json"
            try:
                with open(index_path, 'r') as f:
                    data = json.load(f)
                if "objects" not in data or not isinstance(data["objects"], dict) or not data["objects"]:
                    logging.warning("[ASSETS] Asset index exists but is invalid or empty. Forcing re-download.")
                    index_path.unlink(missing_ok=True)
                    self._install(self.instance_dir)
                else:
                    logging.info("[ASSETS] Asset index exists and is valid.")
            except Exception as e:
                logging.warning(f"[ASSETS] Failed to validate asset index: {e}. Forcing re-download.")
                index_path.unlink(missing_ok=True)
                self._install(self.instance_dir)

    def _is_update_required(self):
        logging.debug("Checking if game update is required")
        return not (self.indexes_dir / f"{self.game.version}.json").exists()

    def _install(self, target_dir):
        vjson = version_utils.get_version_json(self.game.version)
        client_url = vjson["downloads"]["client"]["url"]
        client_jar = target_dir / f"minecraft-{self.game.version}.jar"
        file_utils.download_file(client_url, client_jar)
        libs_dir = target_dir / "libraries"
        natives_dir = target_dir / "natives"
        natives_dir.mkdir(exist_ok=True)
        lib_tasks = []
        native_tasks = []
        native_files = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            for lib in vjson["libraries"]:
                # Download main jar
                if "downloads" in lib and "artifact" in lib["downloads"]:
                    url = lib["downloads"]["artifact"]["url"]
                    path = libs_dir / Path(lib["downloads"]["artifact"]["path"])
                    if not path.exists():
                        lib_tasks.append(
                            executor.submit(file_utils.download_file, url, path, False)
                        )
                # Download and extract natives if present
                if "downloads" in lib and "classifiers" in lib["downloads"] and "natives" in lib:
                    # Find correct classifier for this OS
                    import platform
                    system = platform.system().lower()
                    arch = platform.machine().lower()
                    native_key = None
                    if system == "windows" and "windows" in lib["natives"]:
                        native_key = lib["natives"]["windows"].replace("${arch}", "64")
                    elif system == "linux" and "linux" in lib["natives"]:
                        native_key = lib["natives"]["linux"].replace("${arch}", "64")
                    elif system == "darwin" and "osx" in lib["natives"]:
                        native_key = lib["natives"]["osx"].replace("${arch}", "64")
                    if native_key and native_key in lib["downloads"]["classifiers"]:
                        native_info = lib["downloads"]["classifiers"][native_key]
                        native_url = native_info["url"]
                        native_path = libs_dir / Path(native_info["path"])
                        if not native_path.exists():
                            native_tasks.append(
                                executor.submit(file_utils.download_file, native_url, native_path, False)
                            )
                        native_files.append(native_path)
            # Wait for library downloads
            for f in tqdm(
                as_completed(lib_tasks),
                total=len(lib_tasks),
                desc="Libraries",
                unit="lib",
            ):
                pass
            # Wait for native downloads
            for f in tqdm(
                as_completed(native_tasks),
                total=len(native_tasks),
                desc="Natives",
                unit="native",
            ):
                pass
        # Extract native files (zip/jar) to natives_dir
        for native_path in native_files:
            try:
                with zipfile.ZipFile(native_path, 'r') as zf:
                    zf.extractall(natives_dir)
                logging.info(f"[NATIVES] Extracted {native_path} to {natives_dir}")
            except Exception as e:
                logging.error(f"[NATIVES] Failed to extract {native_path}: {e}")
        assets_dir = target_dir / "assets"
        assets_index_url = vjson["assetIndex"]["url"]
        assets_index_path = assets_dir / "indexes" / f"{self.game.version}.json"
        logging.info(f"[ASSETS] Downloading asset index: {assets_index_url} -> {assets_index_path}")
        file_utils.download_file(assets_index_url, assets_index_path)
        try:
            with open(assets_index_path) as f:
                assets = json.load(f)["objects"]
            logging.info(f"[ASSETS] Asset index loaded, {len(assets)} assets found.")
        except Exception as e:
            logging.error(f"[ASSETS] Failed to load asset index: {e}")
            return
        asset_tasks = []
        failed_assets = []
        with ThreadPoolExecutor(max_workers=16) as executor:
            for name, obj in assets.items():
                h = obj["hash"]
                url = f"https://resources.download.minecraft.net/{h[:2]}/{h}"
                path = assets_dir / "objects" / h[:2] / h
                if not path.exists():
                    asset_tasks.append(executor.submit(file_utils.download_file, url, path, False))
            for future in as_completed(asset_tasks):
                try:
                    future.result()
                except Exception as e:
                    failed_assets.append(str(e))
        if failed_assets:
            print(f"[ASSETS] {len(failed_assets)} assets failed to download:")
            for err in failed_assets:
                print(f"  {err}")
            # Write to a log file
            log_path = Path("assets_failed.log")
            with open(log_path, "w", encoding="utf-8") as logf:
                logf.write(f"[ASSETS] {len(failed_assets)} assets failed to download:\n")
                for err in failed_assets:
                    logf.write(f"  {err}\n")
