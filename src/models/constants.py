from enum import Enum


class Window(Enum):
    MAIN = "MAIN"
    SETTINGS = "SETTINGS"


class Paths(Enum):
    MINECRAFT_DIR = "C:\\Users\\fierr\\AppData\\Roaming\\.minecraft"
    DEFAULT_PROFILE_FILE = f"{MINECRAFT_DIR}\\launcher_profiles.json"
    INSTANCE_DIR = "D:\\Games\\Minecraft\\FFTLauncher\\instance"


PROFILE_DATA = {
    "a4e7d1b6b0974c87bd556f8db97afda3": {
        "created": "2024-01-01T00:00:00.000Z",
        "gameDir": f"{Paths.INSTANCE_DIR.value}",
        "icon": "Furnace",
        "javaArgs": "-Xmx8G -Xms4G -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M",
        "lastUsed": "2025-07-11T16:45:20.8297Z",
        "lastVersionId": "neoforge-21.1.190",
        "name": "FFTClient",
        "type": "custom",
    }
}
