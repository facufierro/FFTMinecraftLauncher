import requests


def get_version_json(version):
    manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    manifest = requests.get(manifest_url).json()
    for v in manifest["versions"]:
        if v["id"] == version:
            return requests.get(v["url"]).json()
    raise Exception(f"Version {version} not found")
