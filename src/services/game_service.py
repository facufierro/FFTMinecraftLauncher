import logging
import json
import requests
import zipfile
from tqdm import tqdm
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..models.game import Game
from ..utils.file_utils import download_file


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
        download_file(client_url, client_jar)
        libs_dir = target_dir / "libraries"
        lib_tasks = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            for lib in vjson["libraries"]:
                if "downloads" in lib and "artifact" in lib["downloads"]:
                    url = lib["downloads"]["artifact"]["url"]
                    path = libs_dir / Path(lib["downloads"]["artifact"]["path"])
                    if not path.exists():
                        lib_tasks.append(
                            executor.submit(download_file, url, path, False)
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
        download_file(assets_index_url, assets_index_path)
        with open(assets_index_path) as f:
            assets = json.load(f)["objects"]
        asset_tasks = []
        with ThreadPoolExecutor(max_workers=16) as executor:
            for name, obj in assets.items():
                h = obj["hash"]
                url = f"https://resources.download.minecraft.net/{h[:2]}/{h}"
                path = assets_dir / "objects" / h[:2] / h
                if not path.exists():
                    asset_tasks.append(executor.submit(download_file, url, path, False))
            for f in tqdm(
                as_completed(asset_tasks),
                total=len(asset_tasks),
                desc="Assets",
                unit="asset",
            ):
                pass
