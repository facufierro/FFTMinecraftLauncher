import os
from dataclasses import dataclass, field
from ..version import __loader_version__


@dataclass
class Loader:
    minecraft_dir: str
    downloads_dir: str
    required_version: str = __loader_version__
    download_url: str = field(init=False)
    installer: str = field(init=False)
    launcher: str = field(init=False)

    def __post_init__(self):
        self.download_url = (
            f"https://maven.neoforged.net/releases/net/neoforged/neoforge/"
            f"{self.required_version}/neoforge-{self.required_version}-installer.jar"
        )
        self.installer = os.path.join(
            self.downloads_dir, f"neoforge-{self.required_version}-installer.jar"
        )
        self.launcher_dir = os.path.join(
            self.minecraft_dir, "versions", f"neoforge-{self.required_version}"
        )
        self.launcher = os.path.join(
            self.launcher_dir,
            f"neoforge-{self.required_version}.jar",
        )
