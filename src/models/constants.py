import os
from enum import Enum


INSTANCE_NAME = "instance"
LOADER_FILE_NAME = "neoforge-%s-installer.jar"


class Branch(Enum):
    CLIENT = "main"
    LAUNCHER = "main"


class Window(Enum):
    MAIN = "MAIN"
    SETTINGS = "SETTINGS"
    UPDATE = "UPDATE"


class Path(Enum):
    # Use the directory where this file resides as the root (the real install dir)
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    MINECRAFT_DIR = "C:\\Users\\fierr\\AppData\\Roaming\\.minecraft"
    PROFILE_FILE = f"{MINECRAFT_DIR}\\launcher_profiles.json"
    INSTANCE_DIR = f"{ROOT_DIR}\\instance"
    DOWNLOADS_DIR = f"{ROOT_DIR}\\downloads"


class Folder(Enum):
    DEFAULTCONFIGS = f"{Path.INSTANCE_DIR.value}\\defaultconfigs"
    CONFIGS = f"{Path.INSTANCE_DIR.value}\\configs"
    KUBEJS = f"{Path.INSTANCE_DIR.value}\\kubejs"
    MODFLARED = f"{Path.INSTANCE_DIR.value}\\modflared"
    MODS = f"{Path.INSTANCE_DIR.value}\\mods"
    RESOURCEPACKS = f"{Path.INSTANCE_DIR.value}\\resourcepacks"
    SHADERPACKS = f"{Path.INSTANCE_DIR.value}\\shaderpacks"


class RepoFolder(Enum):
    """Repository folder names (what exists in the GitHub repo)"""

    DEFAULTCONFIGS = "configureddefaults"
    CONFIGS = "configs"
    KUBEJS = "kubejs"
    MODFLARED = "modflared"
    MODS = "mods"
    RESOURCEPACKS = "resourcepacks"
    SHADERPACKS = "shaderpacks"


class File(Enum):
    VERSIONS = "versions.json"
    SERVERS = f"{Path.INSTANCE_DIR.value}\\servers.dat"


class Url(Enum):
    LAUNCHER_REPO = "https://github.com/facufierro/FFTMinecraftLauncher"
    CLIENT_REPO = "https://github.com/facufierro/FFTClientMinecraft1211"
    LOADER_DOWNLOAD = "https://maven.neoforged.net/releases/net/neoforged/neoforge/%s/neoforge-%s-installer.jar"


class Component(Enum):
    LAUNCHER = "launcher"
    MINECRAFT = "minecraft"
    LOADER = "loader"
    JAVA = "java"


PROFILE_DATA = {
    "a4e7d1b6b0974c87bd556f8db97afda3": {
        "created": "2024-01-01T00:00:00.000Z",
        "gameDir": f"{Path.INSTANCE_DIR.value}",
        "icon": "Furnace",
        "javaArgs": "-Xmx8G -Xms4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M",
        "lastUsed": "2025-07-11T16:45:20.8297Z",
        "lastVersionId": "neoforge-21.1.192",
        "name": "FFTClient",
        "type": "custom",
    }
}
