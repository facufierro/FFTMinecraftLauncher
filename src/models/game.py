from dataclasses import dataclass


@dataclass
class Game:
    version: str = "1.21.1"
    manifest_url: str = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
