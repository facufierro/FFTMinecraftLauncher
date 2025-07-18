import os
from enum import Enum


INSTANCE_NAME = "instance"
LOADER_FILE_NAME = "neoforge-%s-installer.jar"


class Window(Enum):
    MAIN = "MAIN"
    SETTINGS = "SETTINGS"
    UPDATE = "UPDATE"


class Paths(Enum):
    MINECRAFT_DIR = "C:\\Users\\fierr\\AppData\\Roaming\\.minecraft"
    DEFAULT_PROFILE_FILE = f"{MINECRAFT_DIR}\\launcher_profiles.json"
    INSTANCE_DIR = f"{os.getcwd()}\\instance"
    VERSIONS_FILE = f"versions.json"
    DOWNLOADS_DIR = f"{os.getcwd()}\\downloads"


class Urls(Enum):
    GITHUB_REPO = "https://github.com/facufierro/FFTMinecraftLauncher"
    LOADER_DOWNLOAD = "https://maven.neoforged.net/releases/net/neoforged/neoforge/%s/neoforge-%s-installer.jar"


class Component(Enum):
    LAUNCHER = "launcher"
    MINECRAFT = "minecraft"
    LOADER = "loader"
    JAVA = "java"


PROFILE_DATA = {
    "a4e7d1b6b0974c87bd556f8db97afda3": {
        "created": "2024-01-01T00:00:00.000Z",
        "gameDir": f"{Paths.INSTANCE_DIR.value}",
        "icon": "Furnace",
        "javaArgs": "-Xmx8G -Xms4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M",
        "lastUsed": "2025-07-11T16:45:20.8297Z",
        "lastVersionId": "neoforge-21.1.192",
        "name": "FFTClient",
        "type": "custom",
    }
}
