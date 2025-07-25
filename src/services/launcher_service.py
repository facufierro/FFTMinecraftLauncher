import logging
import subprocess
import os
import json
import requests
import uuid
import sys
from pathlib import Path
from tqdm import tqdm
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed

from csv import __version__
from ..utils import github_utils
from ..models.loader import Loader


class LauncherService:
    def __init__(self, root_dir: str, minecraft_dir: str, loader: Loader):
        import pathlib

        try:
            self.root_dir = pathlib.Path(root_dir)
            self.minecraft_version = "1.21.1"
            self.instance_dir = self.root_dir / "instance"

            self.manifest_url = (
                "https://launchermeta.mojang.com/mc/game/version_manifest.json"
            )
            self.minecraft_dir = pathlib.Path(minecraft_dir)
            self.downloads_dir = self.root_dir / "downloads"
            self.loader = loader
            self.launcher_repo = {
                "name": "facufierro/FFTMinecraftLauncher",
                "url": "https://github.com/facufierro/FFTMinecraftLauncher",
                "branch": "main",
            }
            self.client_repo = {
                "name": "facufierro/FFTClientMinecraft",
                "url": "https://github.com/facufierro/FFTClientMinecraft",
                "branch": "main",
            }
        except Exception as e:
            logging.critical("Error initializing LauncherService: %s", e)
            raise e

    def update(self):
        try:
            self._fetch_updater_file()
            with open("Updater.exe", "wb") as f:
                f.write(self.updater_file)
            logging.info("Updater replaced successfully.")
            if self._is_update_required():
                logging.info("Update is required.")
                self._fetch_launcher_file()
                subprocess.Popen(["Updater.exe", self.root_dir], cwd=".")
                sys.exit(0)
            else:
                logging.info("No update required, continuing with launcher.")
        except Exception as e:
            logging.error(f"Failed to replace updater: {e}")

    def _fetch_updater_file(self):
        try:
            self.updater_file = github_utils.get_release_file(
                "Updater.exe", self.launcher_repo.get("name")
            )
        except Exception as e:
            logging.error(f"Failed to fetch Updater.exe: {e}")
            raise e

    def _fetch_launcher_file(self):
        try:
            self.launcher_file = github_utils.get_release_file(
                "FFTLauncher.exe", self.launcher_repo.get("name")
            )
            downloads_dir = self.downloads_dir
            os.makedirs(downloads_dir, exist_ok=True)
            with open(os.path.join(downloads_dir, "FFTLauncher.exe"), "wb") as f:
                f.write(self.launcher_file)
            logging.info("Launcher file downloaded successfully.")
        except Exception as e:
            logging.error(f"Failed to fetch FFTLauncher.exe: {e}")
            raise e

    def _is_update_required(self):
        requiered_version = github_utils.get_release_version(
            self.launcher_repo.get("url")
        )
        current_version = __version__
        logging.info(
            f"Current launcher version: {current_version}, Latest release: {requiered_version}"
        )
        return requiered_version and current_version != requiered_version

    def download_file(self, url, dest, show_progress=True, max_retries=3):
        """Download a file with progress bar and validate as zip if .jar/.zip. Retries on failure."""
        for attempt in range(1, max_retries + 1):
            dest.parent.mkdir(parents=True, exist_ok=True)
            r = requests.get(url, stream=True)
            total = int(r.headers.get("content-length", 0))
            print(
                f"[DEBUG] Downloading {url} (attempt {attempt}/{max_retries}), HTTP status: {r.status_code}"
            )
            if show_progress:
                bar = tqdm(
                    desc=dest.name, total=total, unit="B", unit_scale=True, leave=False
                )
            else:
                bar = None
            with open(dest, "wb") as f:
                for chunk in r.iter_content(1024 * 32):
                    f.write(chunk)
                    if bar:
                        bar.update(len(chunk))
            if bar:
                bar.close()
            # Print file size after download
            try:
                size = dest.stat().st_size
                print(f"[DEBUG] Downloaded file size: {size} bytes")
            except Exception:
                print(f"[DEBUG] Could not stat file {dest}")
            # Validate as zip if .jar or .zip
            is_zip = str(dest).endswith(".jar") or str(dest).endswith(".zip")
            valid = True
            if is_zip:
                try:
                    with zipfile.ZipFile(dest, "r") as zf:
                        bad = zf.testzip()
                        if bad is not None:
                            print(
                                f"[WARN] Corrupt zip entry {bad} in {dest}, retrying..."
                            )
                            valid = False
                except Exception as e:
                    print(
                        f"[WARN] Downloaded file {dest} is not a valid zip: {e}, retrying..."
                    )
                    # Print first 200 bytes of file for debugging
                    try:
                        with open(dest, "rb") as f:
                            snippet = f.read(200)
                            print(f"[DEBUG] First 200 bytes of file: {snippet}")
                    except Exception:
                        print(f"[DEBUG] Could not read file {dest}")
                    valid = False
            if valid:
                return
            else:
                try:
                    dest.unlink()
                except Exception:
                    pass
                if attempt == max_retries:
                    # Print first 200 bytes of HTTP response if not valid
                    try:
                        r2 = requests.get(url)
                        print(f"[DEBUG] HTTP status: {r2.status_code}")
                        print(
                            f"[DEBUG] First 200 bytes of HTTP response: {r2.content[:200]}"
                        )
                    except Exception:
                        print(f"[DEBUG] Could not fetch HTTP response for {url}")
                    raise Exception(
                        f"Failed to download a valid file from {url} after {max_retries} attempts."
                    )

    def get_version_json(self, version):
        manifest = requests.get(self.manifest_url).json()
        for v in manifest["versions"]:
            if v["id"] == version:
                return requests.get(v["url"]).json()
        raise Exception(f"Version {version} not found")

    def ensure_java(self):
        for cmd in ["java", "java.exe"]:
            if any(
                os.access(os.path.join(path, cmd), os.X_OK)
                for path in os.environ["PATH"].split(os.pathsep)
            ):
                return cmd
        print("Java not found in PATH. Please install Java 17+ and add to PATH.")
        sys.exit(1)

    def install_vanilla_to_dir(self, target_dir):
        if (target_dir / "vanilla_installed").exists():
            print(
                f"Vanilla Minecraft {self.minecraft_version} already present in {target_dir}."
            )
            return
        print(
            f"Installing vanilla Minecraft {self.minecraft_version} to {target_dir}..."
        )
        vjson = self.get_version_json(self.minecraft_version)
        client_url = vjson["downloads"]["client"]["url"]
        client_jar = target_dir / f"minecraft-{self.minecraft_version}.jar"
        self.download_file(client_url, client_jar)
        libs_dir = target_dir / "libraries"
        lib_tasks = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            for lib in vjson["libraries"]:
                if "downloads" in lib and "artifact" in lib["downloads"]:
                    url = lib["downloads"]["artifact"]["url"]
                    path = libs_dir / Path(lib["downloads"]["artifact"]["path"])
                    if not path.exists():
                        lib_tasks.append(
                            executor.submit(self.download_file, url, path, False)
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
        assets_index_path = assets_dir / "indexes" / f"{self.minecraft_version}.json"
        self.download_file(assets_index_url, assets_index_path)
        with open(assets_index_path) as f:
            assets = json.load(f)["objects"]
        asset_tasks = []
        with ThreadPoolExecutor(max_workers=16) as executor:
            for name, obj in assets.items():
                h = obj["hash"]
                url = f"https://resources.download.minecraft.net/{h[:2]}/{h}"
                path = assets_dir / "objects" / h[:2] / h
                if not path.exists():
                    asset_tasks.append(
                        executor.submit(self.download_file, url, path, False)
                    )
            for f in tqdm(
                as_completed(asset_tasks),
                total=len(asset_tasks),
                desc="Assets",
                unit="asset",
            ):
                pass
        (target_dir / "vanilla_installed").touch()
        print(f"Vanilla install complete in {target_dir}.")

    def ensure_launcher_profiles_json(self, target_dir):
        lp = target_dir / "launcher_profiles.json"
        if not lp.exists():
            with open(lp, "w") as f:
                json.dump({"profiles": {}, "settings": {}, "version": 1}, f)

    def install_neoforge(self):
        if (self.instance_dir / "installed").exists():
            print(
                f"NeoForge {self.loader.required_version} for Minecraft {self.minecraft_version} already installed."
            )
            return
        self.install_vanilla_to_dir(self.instance_dir)
        self.ensure_launcher_profiles_json(self.instance_dir)
        print(
            f"Installing NeoForge {self.loader.required_version} for Minecraft {self.minecraft_version}..."
        )
        self.instance_dir.mkdir(parents=True, exist_ok=True)
        installer_jar = (
            self.instance_dir / f"neoforge-{self.loader.required_version}-installer.jar"
        )
        if not installer_jar.exists():
            print(f"Downloading NeoForge installer {self.loader.required_version}...")
            self.download_file(self.loader.download_url, installer_jar)
        print("Running NeoForge installer...")
        java = self.ensure_java()
        subprocess.run(
            [
                java,
                "-jar",
                str(installer_jar),
                "--installClient",
                str(self.instance_dir),
            ],
            check=True,
        )
        (self.instance_dir / "installed").touch()
        print("NeoForge install complete.")

    def launch_neoforge(self):
        # --- Find NeoForge version directory and load version JSON ---
        versions_dir = self.instance_dir / "versions"
        version_folder = None
        for d in versions_dir.iterdir():
            if d.is_dir() and d.name.startswith("neoforge-"):
                version_folder = d
                break
        if not version_folder:
            print("Could not find NeoForge version folder after install.")
            sys.exit(1)
        version_json = version_folder / f"{version_folder.name}.json"
        with open(version_json) as f:
            vjson = json.load(f)

        # --- Download all libraries and assets if missing (self-repair) ---
        libs_dir = self.instance_dir / "libraries"
        missing_libs = []
        for lib in vjson["libraries"]:
            if "downloads" in lib and "artifact" in lib["downloads"]:
                path = libs_dir / Path(lib["downloads"]["artifact"]["path"])
                if not path.exists():
                    missing_libs.append((lib["downloads"]["artifact"]["url"], path))
        if missing_libs:
            print(f"[INFO] Downloading {len(missing_libs)} missing libraries...")
            for url, path in missing_libs:
                print(f"[INFO] Downloading {url} -> {path}")
                self.download_file(url, path)

        # --- Download assets index and all assets if missing ---
        assets_dir = self.instance_dir / "assets"
        assets_index_path = assets_dir / "indexes" / f"{self.minecraft_version}.json"
        if not assets_index_path.exists():
            vjson_vanilla = self.get_version_json(self.minecraft_version)
            assets_index_url = vjson_vanilla["assetIndex"]["url"]
            self.download_file(assets_index_url, assets_index_path)
        with open(assets_index_path) as f:
            assets = json.load(f)["objects"]
        asset_tasks = []
        with ThreadPoolExecutor(max_workers=16) as executor:
            for name, obj in assets.items():
                h = obj["hash"]
                url = f"https://resources.download.minecraft.net/{h[:2]}/{h}"
                path = assets_dir / "objects" / h[:2] / h
                if not path.exists():
                    asset_tasks.append(
                        executor.submit(self.download_file, url, path, False)
                    )
            for f in tqdm(
                as_completed(asset_tasks),
                total=len(asset_tasks),
                desc="Assets",
                unit="asset",
            ):
                pass

        # --- Extract all native jars to natives directory ---
        natives_dir = self.instance_dir / "natives"
        natives_dir.mkdir(parents=True, exist_ok=True)
        for lib in vjson["libraries"]:
            if "downloads" in lib and "artifact" in lib["downloads"]:
                path = libs_dir / Path(lib["downloads"]["artifact"]["path"])
                if (
                    path.name.endswith(".jar")
                    and "-natives-" in path.name
                    and path.exists()
                ):
                    try:
                        with zipfile.ZipFile(path, "r") as zf:
                            zf.extractall(natives_dir)
                    except Exception as e:
                        print(f"[WARN] Failed to extract natives from {path}: {e}")

        # --- Build classpath and module-path strictly from version JSON, inject bootstraplauncher/securejarhandler ---
        cp_jars = []
        bl_jar = None
        sjh_jar = None
        asm_jars = []
        jarjarfs_jar = None
        lwjgl_jars = []
        vjson["libraries"] = [
            lib
            for lib in vjson["libraries"]
            if not (
                lib["name"].startswith("cpw.mods.bootstraplauncher:")
                or lib["name"].startswith("cpw.mods.securejarhandler:")
            )
        ]
        BOOTSTRAPLAUNCHER_VERSION = "2.0.2"
        SECUREJARHANDLER_VERSION = "3.0.8"
        FORGE_MAVEN = "https://maven.minecraftforge.net/"
        bl_path = f"cpw/mods/bootstraplauncher/{BOOTSTRAPLAUNCHER_VERSION}/bootstraplauncher-{BOOTSTRAPLAUNCHER_VERSION}.jar"
        sjh_path = f"cpw/mods/securejarhandler/{SECUREJARHANDLER_VERSION}/securejarhandler-{SECUREJARHANDLER_VERSION}.jar"
        vjson["libraries"].append(
            {
                "name": f"cpw.mods.bootstraplauncher:bootstraplauncher:{BOOTSTRAPLAUNCHER_VERSION}",
                "downloads": {
                    "artifact": {"path": bl_path, "url": FORGE_MAVEN + bl_path}
                },
            }
        )
        vjson["libraries"].append(
            {
                "name": f"cpw.mods.securejarhandler:securejarhandler:{SECUREJARHANDLER_VERSION}",
                "downloads": {
                    "artifact": {"path": sjh_path, "url": FORGE_MAVEN + sjh_path}
                },
            }
        )
        for lib in vjson["libraries"]:
            if "downloads" in lib and "artifact" in lib["downloads"]:
                path = libs_dir / Path(lib["downloads"]["artifact"]["path"])
                name = lib["name"]
                cp_jars.append(str(path))
                if name.startswith("cpw.mods.bootstraplauncher:"):
                    bl_jar = str(path)
                if name.startswith("cpw.mods.securejarhandler:"):
                    sjh_jar = str(path)
                if name.startswith("org.ow2.asm:"):
                    asm_jars.append(str(path))
                if name.startswith("net.neoforged.JarJarFileSystems:"):
                    jarjarfs_jar = str(path)
                if name.startswith("org.lwjgl:"):
                    lwjgl_jars.append(str(path))
        for url, path in [
            (FORGE_MAVEN + bl_path, libs_dir / bl_path),
            (FORGE_MAVEN + sjh_path, libs_dir / sjh_path),
        ]:
            if not path.exists():
                print(f"[INFO] Downloading injected {path.name}...")
                self.download_file(url, path)
        if (
            not bl_jar
            or not sjh_jar
            or not Path(bl_jar).exists()
            or not Path(sjh_jar).exists()
        ):
            print(
                "[ERROR] Still missing bootstraplauncher or securejarhandler jar after library download. Aborting launch."
            )
            return
        mp_jars = [j for j in [bl_jar, sjh_jar] if j] + asm_jars
        if jarjarfs_jar:
            mp_jars.append(jarjarfs_jar)

        vjson_vanilla = self.get_version_json(self.minecraft_version)
        vanilla_libs = [
            lib
            for lib in vjson_vanilla["libraries"]
            if "downloads" in lib and "artifact" in lib["downloads"]
        ]
        vanilla_jars = []
        missing_vanilla_libs = []
        for lib in vanilla_libs:
            path = libs_dir / Path(lib["downloads"]["artifact"]["path"])
            vanilla_jars.append(str(path))
            if not path.exists():
                missing_vanilla_libs.append((lib["downloads"]["artifact"]["url"], path))
        if missing_vanilla_libs:
            print(
                f"[INFO] Downloading {len(missing_vanilla_libs)} missing vanilla libraries..."
            )
            for url, path in missing_vanilla_libs:
                print(f"[INFO] Downloading {url} -> {path}")
                self.download_file(url, path)
        for jar in vanilla_jars:
            if jar not in cp_jars:
                cp_jars.append(jar)
        import zipfile

        all_lwjgl_jars = [j for j in cp_jars if r"org\lwjgl" in j or "org/lwjgl" in j]
        struct_found = False
        for jar in all_lwjgl_jars:
            try:
                with zipfile.ZipFile(jar, "r") as zf:
                    if any(
                        x.startswith("org/lwjgl/system/Struct") for x in zf.namelist()
                    ):
                        struct_found = True
                        break
            except Exception as e:
                print(f"[ERROR] LWJGL jar {jar} is corrupt or unreadable: {e}")
        if not struct_found:
            print(
                "[ERROR] None of the LWJGL jars (including vanilla) contain org/lwjgl/system/Struct. Your libraries may be corrupt or incomplete."
            )
            print("[DEBUG] Searched jars:")
            for jar in all_lwjgl_jars:
                print("  ", jar)
            print("[ERROR] Try deleting your libraries folder and reinstalling.")
            return

        classpath = ";".join(cp_jars)
        module_path = ";".join(mp_jars)
        print(f"[DEBUG] Module path: {module_path}")
        print(f"[DEBUG] Full classpath:")
        for j in cp_jars:
            print("  ", j)

        java = self.ensure_java()
        random_uuid = str(uuid.uuid4())
        natives_dir_str = str(natives_dir)
        args = [
            java,
            "-Xmx8192M",
            "-XX:MetaspaceSize=256M",
            "-Duser.language=en",
            "-Duser.country=US",
            "-XX:+UnlockExperimentalVMOptions",
            "-XX:+UseG1GC",
            "-XX:G1NewSizePercent=20",
            "-XX:G1ReservePercent=20",
            "-XX:MaxGCPauseMillis=50",
            "-XX:G1HeapRegionSize=32M",
            f"-Djava.library.path={natives_dir_str}",
            f"-Djna.tmpdir={natives_dir_str}",
            f"-Dorg.lwjgl.system.SharedLibraryExtractPath={natives_dir_str}",
            f"-Dio.netty.native.workdir={natives_dir_str}",
            f"-DlibraryDirectory={str(libs_dir)}",
            "-Dminecraft.launcher.brand=ATLauncher",
            "-Dminecraft.launcher.version=3.4.40.1",
            "-cp",
            classpath,
        ]
        if module_path:
            args += ["-p", module_path]
        args += [
            "--add-modules",
            "ALL-MODULE-PATH",
            "--add-opens",
            "java.base/java.util.jar=cpw.mods.securejarhandler",
            "--add-opens",
            "java.base/java.lang.invoke=cpw.mods.securejarhandler",
            "--add-opens",
            "java.base/java.lang.invoke=ALL-UNNAMED",
            "--add-exports",
            "java.base/sun.security.util=cpw.mods.securejarhandler",
            "--add-exports",
            "jdk.naming.dns/com.sun.jndi.dns=java.naming",
            vjson.get("mainClass", "cpw.mods.bootstraplauncher.BootstrapLauncher"),
            "--username",
            "Player",
            "--version",
            self.minecraft_version,
            "--gameDir",
            str(self.instance_dir),
            "--assetsDir",
            str(self.instance_dir / "assets"),
            "--assetIndex",
            self.minecraft_version,
            "--uuid",
            random_uuid,
            "--accessToken",
            "0",
            "--userType",
            "msa",
            "--versionType",
            "release",
            "--fml.neoForgeVersion",
            self.loader.required_version,
            "--fml.fmlVersion",
            "4.0.41",
            "--fml.mcVersion",
            self.minecraft_version,
            "--fml.neoFormVersion",
            "20240808.144430",
            "--launchTarget",
            "forgeclient",
        ]
        print(f"Launching NeoForge with UUID: {random_uuid}")
        subprocess.run(args, cwd=self.instance_dir)

    def launch_game(self):
        self.install_neoforge()
        self.launch_neoforge()
