import requests


def get_version_json(self, version):
    manifest = requests.get(self.game.manifest_url).json()
    for v in manifest["versions"]:
        if v["id"] == version:
            return requests.get(v["url"]).json()
    raise Exception(f"Version {version} not found")
