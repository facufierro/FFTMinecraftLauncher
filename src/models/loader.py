import os
from dataclasses import dataclass, field


@dataclass
class Loader:
    downloads_dir: str
    current_version: str = field(default=None)
    required_version: str = field(default=None)
    file_name: str = field(init=False)
    download_url: str = field(init=False)
    existing_file: str = field(init=False)

    def __post_init__(self):
        self.file_name = f"neoforge-{self.required_version}-installer.jar"
        self.download_url = (
            f"https://maven.neoforged.net/releases/net/neoforged/neoforge/"
            f"{self.required_version}/neoforge-{self.required_version}-installer.jar"
        )
        self.existing_file = os.path.join(self.downloads_dir, self.file_name)
