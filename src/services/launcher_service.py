import logging
import subprocess
import os
import json
import platform
import uuid
from pathlib import Path

from .versions_service import VersionsService
from ..services.github_service import GitHubService
from ..models.constants import Url, Path as AppPath


class LauncherService:
    def __init__(self, version_service: VersionsService, github_service: GitHubService):
        try:
            self.version_service = version_service
            self.github_service = github_service
            self.minecraft_dir = self._get_minecraft_directory()
            
            # Try to get updater file, but don't fail if it doesn't exist
            self.updater_file = github_service.get_release_file(
                "updater.exe", Url.LAUNCHER_REPO.value
            )
            if not self.updater_file:
                logging.warning(
                    "updater.exe not found in latest release - updater functionality will be disabled"
                )
            logging.debug("LauncherService initialized")
        except Exception as e:
            logging.critical("Error initializing LauncherService: %s", e)
            raise e

    def _get_minecraft_directory(self):
        """Get the standard Minecraft directory based on OS"""
        if platform.system() == "Windows":
            return Path(os.path.expandvars("%APPDATA%/.minecraft"))
        elif platform.system() == "Darwin":  # macOS
            return Path.home() / "Library/Application Support/minecraft"
        else:  # Linux
            return Path.home() / ".minecraft"

    def replace_updater(self):
        try:
            if self.updater_file:
                self.github_service.save_file(self.updater_file, "updater.exe")
                logging.info("Updater replaced successfully.")
            else:
                logging.warning("Cannot replace updater - updater.exe not available")
        except Exception as e:
            logging.error(f"Failed to replace updater: {e}")

    def update(self):
        self._launch_updater()

    def _launch_updater(self):
        logging.info("Launching updater...")
        # subprocess.Popen(["updater.exe"], cwd=".")

    def launch_game(self):
        """Launch Minecraft directly using Java like ATLauncher does"""
        try:
            logging.info("Starting direct Minecraft launch...")
            
            # Get version info
            version = "1.21.1"  # Default version
            version_data = self._get_version_data(version)
            if not version_data:
                logging.error(f"Failed to get version data for {version}")
                return False
            
            # Ensure all required files are present
            if not self._ensure_game_files(version_data, version):
                logging.error("Failed to ensure game files are present")
                return False
            
            # Build Java command arguments
            java_args = self._build_java_command(version_data, version)
            if not java_args:
                logging.error("Failed to build Java command")
                return False
            
            # Launch the process
            logging.info(f"Launching Minecraft with Java directly")
            logging.debug(f"Java command: {' '.join(java_args[:5])}... (truncated)")
            
            process = subprocess.Popen(
                java_args,
                cwd=self.minecraft_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            logging.info(f"Minecraft process started with PID: {process.pid}")
            return True
                
        except Exception as e:
            logging.error(f"Failed to launch game: {e}")
            return False

    def _get_version_data(self, version):
        """Get version manifest data"""
        try:
            version_manifest_path = self.minecraft_dir / "versions" / version / f"{version}.json"
            if version_manifest_path.exists():
                with open(version_manifest_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            logging.warning(f"Version manifest not found: {version_manifest_path}")
            return None
        except Exception as e:
            logging.error(f"Failed to load version data: {e}")
            return None

    def _ensure_game_files(self, version_data, version):
        """Ensure all required game files are present"""
        try:
            # Check if main JAR exists
            jar_path = self.minecraft_dir / "versions" / version / f"{version}.jar"
            if not jar_path.exists():
                logging.error(f"Minecraft JAR not found: {jar_path}")
                return False
            
            # Check if libraries directory exists
            libraries_dir = self.minecraft_dir / "libraries"
            if not libraries_dir.exists():
                logging.error(f"Libraries directory not found: {libraries_dir}")
                return False
            
            # Check if assets exist
            assets_dir = self.minecraft_dir / "assets"
            if not assets_dir.exists():
                logging.error(f"Assets directory not found: {assets_dir}")
                return False
            
            logging.info("All required game files are present")
            return True
            
        except Exception as e:
            logging.error(f"Failed to verify game files: {e}")
            return False

    def _build_java_command(self, version_data, version):
        """Build the complete Java command line arguments"""
        try:
            args = []
            
            # Java executable
            java_exe = "java"
            if platform.system() == "Windows":
                java_exe = "javaw"  # Use javaw on Windows to hide console
            args.append(java_exe)
            
            # Memory settings
            args.extend(["-Xmx2G", "-Xms1G"])
            
            # System properties
            args.append("-Duser.language=en")
            args.append("-Duser.country=US")
            
            # Minecraft-specific JVM args
            if 'jvm' in version_data.get('arguments', {}):
                for arg in version_data['arguments']['jvm']:
                    if isinstance(arg, str):
                        # Replace variables
                        arg = arg.replace('${natives_directory}', str(self.minecraft_dir / "versions" / version / "natives"))
                        arg = arg.replace('${launcher_name}', "FFTLauncher")
                        arg = arg.replace('${launcher_version}', "1.0.0")
                        arg = arg.replace('${classpath}', self._build_classpath(version_data, version))
                        args.append(arg)
            
            # Classpath
            args.extend(["-cp", self._build_classpath(version_data, version)])
            
            # Main class
            main_class = version_data.get('mainClass', 'net.minecraft.client.main.Main')
            args.append(main_class)
            
            # Game arguments
            args.extend(self._build_game_arguments(version_data, version))
            
            return args
            
        except Exception as e:
            logging.error(f"Failed to build Java command: {e}")
            return None

    def _build_classpath(self, version_data, version):
        """Build the classpath string with all libraries and main JAR"""
        try:
            classpath_parts = []
            
            # Add libraries
            libraries_dir = self.minecraft_dir / "libraries"
            if 'libraries' in version_data:
                for lib in version_data['libraries']:
                    if self._should_include_library(lib):
                        lib_path = self._get_library_path(lib, libraries_dir)
                        if lib_path and lib_path.exists():
                            classpath_parts.append(str(lib_path))
            
            # Add main Minecraft JAR
            jar_path = self.minecraft_dir / "versions" / version / f"{version}.jar"
            if jar_path.exists():
                classpath_parts.append(str(jar_path))
            
            # Join with appropriate separator
            separator = ";" if platform.system() == "Windows" else ":"
            return separator.join(classpath_parts)
            
        except Exception as e:
            logging.error(f"Failed to build classpath: {e}")
            return ""

    def _should_include_library(self, library):
        """Check if a library should be included based on rules"""
        if 'rules' not in library:
            return True
        
        # Simplified rule processing - in a real implementation you'd check OS, features, etc.
        for rule in library['rules']:
            action = rule.get('action', 'allow')
            if action == 'disallow':
                return False
        
        return True

    def _get_library_path(self, library, libraries_dir):
        """Get the path to a library file"""
        try:
            if 'downloads' in library and 'artifact' in library['downloads']:
                artifact_path = library['downloads']['artifact']['path']
                return libraries_dir / artifact_path
            
            # Fallback: construct path from name
            name = library.get('name', '')
            parts = name.split(':')
            if len(parts) >= 3:
                group, artifact, version = parts[0], parts[1], parts[2]
                path = '/'.join(group.split('.')) + f"/{artifact}/{version}/{artifact}-{version}.jar"
                return libraries_dir / path
            
            return None
            
        except Exception as e:
            logging.error(f"Failed to get library path: {e}")
            return None

    def _build_game_arguments(self, version_data, version):
        """Build game-specific arguments"""
        try:
            args = []
            
            # Username and session (fake for now - in a real launcher you'd use OAuth)
            username = "Player"
            uuid_str = str(uuid.uuid4())
            access_token = "fake_access_token"
            
            # Standard game arguments
            if 'game' in version_data.get('arguments', {}):
                for arg in version_data['arguments']['game']:
                    if isinstance(arg, str):
                        # Replace variables
                        arg = arg.replace('${auth_player_name}', username)
                        arg = arg.replace('${version_name}', version)
                        arg = arg.replace('${game_directory}', str(self.minecraft_dir))
                        arg = arg.replace('${assets_root}', str(self.minecraft_dir / "assets"))
                        arg = arg.replace('${assets_index_name}', version_data.get('assetIndex', {}).get('id', version))
                        arg = arg.replace('${auth_uuid}', uuid_str)
                        arg = arg.replace('${auth_access_token}', access_token)
                        arg = arg.replace('${user_type}', "legacy")
                        arg = arg.replace('${version_type}', version_data.get('type', 'release'))
                        args.append(arg)
            else:
                # Fallback for older versions
                args.extend([
                    "--username", username,
                    "--version", version,
                    "--gameDir", str(self.minecraft_dir),
                    "--assetsDir", str(self.minecraft_dir / "assets"),
                    "--assetIndex", version_data.get('assetIndex', {}).get('id', version),
                    "--uuid", uuid_str,
                    "--accessToken", access_token,
                    "--userType", "legacy"
                ])
            
            return args
            
        except Exception as e:
            logging.error(f"Failed to build game arguments: {e}")
            return []

