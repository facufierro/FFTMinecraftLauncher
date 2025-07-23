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
from .auth_service import AuthService


class LauncherService:
    def __init__(
        self,
        version_service: VersionsService,
        github_service: GitHubService,
        loader_service=None,
    ):
        try:
            self.version_service = version_service
            self.github_service = github_service
            self.loader_service = loader_service
            self.minecraft_dir = self._get_minecraft_directory()
            self.auth_service = AuthService()

            # Try to get updater file, but don't fail if it doesn't exist
            self.updater_file = github_service.get_release_file(
                "Updater.exe", Url.LAUNCHER_REPO.value
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
                with open("Updater.exe", "wb") as f:
                    f.write(self.updater_file)
                logging.info("Updater replaced successfully.")
            else:
                logging.warning("Cannot replace updater - Updater.exe not available")
        except Exception as e:
            logging.error(f"Failed to replace updater: {e}")

    def update(self):
        self._launch_updater()

    def _launch_updater(self):
        logging.info("Launching updater...")
        subprocess.Popen(["Updater.exe"], cwd=".")
        # Ensure the launcher process exits after starting the updater
        import sys

        sys.exit(0)

    def launch_game(self):
        """Launch Minecraft with NeoForge support using existing constants"""
        try:
            logging.info("Starting Minecraft launch with NeoForge support...")

            # Try authentication first, but don't fail if it doesn't work
            auth_attempted = False
            if not self.auth_service.is_authenticated():
                logging.info("Authentication required - attempting Microsoft login...")
                auth_attempted = True
                if not self.auth_service.authenticate():
                    logging.warning(
                        "Microsoft authentication failed - continuing with offline mode"
                    )
                    print("Authentication failed, but continuing with offline mode...")

            if not auth_attempted:
                logging.info("Using cached authentication")

            # Get NeoForge version from your profile data
            from ..models.constants import PROFILE_DATA

            profile_data = list(PROFILE_DATA.values())[
                0
            ]  # Get the first (and likely only) profile
            neoforge_version = profile_data["lastVersionId"]  # "neoforge-21.1.192"

            logging.info(f"Using version from profile: {neoforge_version}")

            # First try NeoForge, then fallback to vanilla
            version_data = self._get_version_data(neoforge_version)
            if not version_data:
                logging.warning(
                    f"NeoForge version {neoforge_version} not found, trying vanilla Minecraft..."
                )
                # Extract base MC version from NeoForge version if possible
                base_version = (
                    "1.21.1"  # Could parse this from neoforge version in the future
                )
                version_data = self._get_version_data(base_version)
                neoforge_version = base_version

            if not version_data:
                logging.error("No valid Minecraft version found")
                return False

            # Ensure all required files are present
            if not self._ensure_game_files(version_data, neoforge_version):
                logging.error("Failed to ensure game files are present")
                return False

            # Ensure NeoForge is installed using LoaderService
            if not self._ensure_neoforge_installed_with_loader_service(
                neoforge_version
            ):
                logging.error("NeoForge installation failed")
                return False

            # Build Java command arguments using your profile's Java args
            java_args = self._build_java_command(
                version_data, neoforge_version, profile_data
            )
            if not java_args:
                logging.error("Failed to build Java command")
                return False

            # Launch the process using your instance directory
            logging.info(f"Launching Minecraft with Java directly")
            logging.info(f"Full Java command: {' '.join(java_args)}")

            # Use your instance directory as working directory
            instance_dir = Path(AppPath.INSTANCE_DIR.value)
            working_dir = instance_dir if instance_dir.exists() else self.minecraft_dir
            logging.info(f"Working directory: {working_dir}")

            process = subprocess.Popen(java_args, cwd=working_dir)

            logging.info(f"Minecraft process started with PID: {process.pid}")

            # Check if process is still running after a short delay
            import time

            time.sleep(2)
            return_code = process.poll()
            if return_code is not None:
                # Process has already terminated
                logging.error(
                    f"Minecraft process terminated early with return code: {return_code}"
                )
                return False
            else:
                logging.info("Minecraft process is running successfully")
                return True

        except Exception as e:
            logging.error(f"Failed to launch game: {e}")
            return False

    def _get_version_data(self, version):
        """Get version manifest data, handling inheritance"""
        try:
            version_manifest_path = (
                self.minecraft_dir / "versions" / version / f"{version}.json"
            )
            if version_manifest_path.exists():
                with open(version_manifest_path, "r", encoding="utf-8") as f:
                    version_data = json.load(f)

                # Handle version inheritance (like NeoForge inheriting from base Minecraft)
                if "inheritsFrom" in version_data:
                    base_version = version_data["inheritsFrom"]
                    logging.info(f"Version {version} inherits from {base_version}")

                    # Load base version data
                    base_version_data = self._get_version_data(base_version)
                    if base_version_data:
                        # Merge base version data with current version data
                        # Game arguments from base version
                        if "arguments" not in version_data:
                            version_data["arguments"] = {}
                        if "game" not in version_data["arguments"]:
                            version_data["arguments"]["game"] = []
                        if "jvm" not in version_data["arguments"]:
                            version_data["arguments"]["jvm"] = []

                        # Add base game arguments first, then NeoForge-specific ones
                        if (
                            "arguments" in base_version_data
                            and "game" in base_version_data["arguments"]
                        ):
                            version_data["arguments"]["game"] = (
                                base_version_data["arguments"]["game"]
                                + version_data["arguments"]["game"]
                            )

                        # Add base JVM arguments first, then NeoForge-specific ones
                        if (
                            "arguments" in base_version_data
                            and "jvm" in base_version_data["arguments"]
                        ):
                            version_data["arguments"]["jvm"] = (
                                base_version_data["arguments"]["jvm"]
                                + version_data["arguments"]["jvm"]
                            )

                        # Handle libraries with better deduplication
                        if "libraries" not in version_data:
                            version_data["libraries"] = []

                        if "libraries" in base_version_data:
                            # Create a combined list while avoiding duplicates by library name
                            seen_library_names = set()
                            combined_libraries = []

                            # Add NeoForge libraries first (they take precedence)
                            for lib in version_data["libraries"]:
                                lib_name = lib.get("name", "")
                                if lib_name and lib_name not in seen_library_names:
                                    combined_libraries.append(lib)
                                    seen_library_names.add(lib_name)

                            # Add base libraries that aren't already included
                            for lib in base_version_data["libraries"]:
                                lib_name = lib.get("name", "")
                                if lib_name and lib_name not in seen_library_names:
                                    combined_libraries.append(lib)
                                    seen_library_names.add(lib_name)

                            version_data["libraries"] = combined_libraries
                            logging.info(
                                f"Merged libraries: {len(combined_libraries)} total ({len(version_data.get('libraries', []))} NeoForge + {len(base_version_data['libraries'])} base, deduplicated)"
                            )

                        # Inherit other properties if not specified
                        for key in ["assetIndex", "assets", "minecraftArguments"]:
                            if key not in version_data and key in base_version_data:
                                version_data[key] = base_version_data[key]

                return version_data

            logging.warning(f"Version manifest not found: {version_manifest_path}")
            return None
        except Exception as e:
            logging.error(f"Failed to load version data: {e}")
            return None

    def _ensure_game_files(self, version_data, version):
        """Ensure all required game files are present, including NeoForge if needed"""
        try:
            # If this is a NeoForge version, ensure it's installed
            if version.startswith("neoforge-"):
                if not self._ensure_neoforge_installed(version):
                    logging.error(f"Failed to ensure NeoForge {version} is installed")
                    return False

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

    def _ensure_neoforge_installed_with_loader_service(self, neoforge_version):
        """Use LoaderService to ensure NeoForge is installed"""
        try:
            # First check if NeoForge is already installed
            neoforge_dir = self.minecraft_dir / "versions" / neoforge_version
            neoforge_json = neoforge_dir / f"{neoforge_version}.json"
            neoforge_jar = neoforge_dir / f"{neoforge_version}.jar"

            if neoforge_json.exists() and neoforge_jar.exists():
                logging.info(
                    f"NeoForge {neoforge_version} is already installed - skipping installation"
                )
                return True

            if self.loader_service:
                logging.info(
                    f"NeoForge {neoforge_version} not found, using LoaderService to install it"
                )
                self.loader_service.update()
                return True
            else:
                logging.warning(
                    "LoaderService not available, falling back to manual installation"
                )
                return self._ensure_neoforge_installed(neoforge_version)
        except Exception as e:
            logging.error(f"Failed to install NeoForge using LoaderService: {e}")
            return False

    def _ensure_neoforge_installed(self, neoforge_version):
        """Ensure NeoForge is installed in .minecraft, install if needed"""
        try:
            # Check if NeoForge version directory exists
            neoforge_dir = self.minecraft_dir / "versions" / neoforge_version
            neoforge_json = neoforge_dir / f"{neoforge_version}.json"
            neoforge_jar = neoforge_dir / f"{neoforge_version}.jar"

            if neoforge_json.exists() and neoforge_jar.exists():
                logging.info(f"NeoForge {neoforge_version} already installed")
                return True

            logging.info(
                f"NeoForge {neoforge_version} not found, attempting installation..."
            )

            # Look for NeoForge installer in downloads directory
            from ..models.constants import LOADER_FILE_NAME

            downloads_dir = Path(AppPath.DOWNLOADS_DIR.value)

            # Extract version number from neoforge version (e.g., "neoforge-21.1.192" -> "21.1.192")
            version_parts = neoforge_version.split("-")
            if len(version_parts) >= 2:
                version_number = "-".join(
                    version_parts[1:]
                )  # Everything after "neoforge-"
                installer_name = LOADER_FILE_NAME % version_number
                installer_path = downloads_dir / installer_name

                if installer_path.exists():
                    logging.info(f"Found NeoForge installer: {installer_path}")
                    return self._run_neoforge_installer(installer_path)
                else:
                    logging.error(f"NeoForge installer not found: {installer_path}")

            return False

        except Exception as e:
            logging.error(f"Failed to ensure NeoForge installation: {e}")
            return False

    def _run_neoforge_installer(self, installer_path):
        """Run the NeoForge installer"""
        try:
            logging.info(f"Running NeoForge installer: {installer_path}")

            # Run the installer with --install-client option
            cmd = [
                "java",
                "-jar",
                str(installer_path),
                "--install-client",
                "--minecraft-dir",
                str(self.minecraft_dir),
            ]

            result = subprocess.run(
                cmd,
                cwd=str(installer_path.parent),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode == 0:
                logging.info("NeoForge installer completed successfully")
                return True
            else:
                logging.error(f"NeoForge installer failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logging.error("NeoForge installer timed out")
            return False
        except Exception as e:
            logging.error(f"Failed to run NeoForge installer: {e}")
            return False

    def _build_java_command(self, version_data, version, profile_data=None):
        """Build the complete Java command line arguments using profile data"""
        try:
            args = []

            # Java executable - First check if we have Java 17 or 21 available
            java_exe = self._find_compatible_java()
            if not java_exe:
                logging.error(
                    "No compatible Java version found. Minecraft 1.21.1 with NeoForge requires Java 17 or 21, but Java 24 was found."
                )
                return None

            args.append(java_exe)

            # Use Java args from your profile if available
            if profile_data and "javaArgs" in profile_data:
                java_args_str = profile_data["javaArgs"]
                # Split the Java args string and add them
                for arg in java_args_str.split():
                    args.append(arg)
                logging.info(f"Using Java args from profile: {java_args_str}")
            else:
                # Fallback memory settings
                args.extend(["-Xmx2G", "-Xms1G"])

            # System properties
            args.append("-Duser.language=en")
            args.append("-Duser.country=US")

            # Add required properties for NeoForge
            if version.startswith("neoforge-"):
                args.append("-Dnet.minecraftforge.mergetool.version=1.1.5")
                args.append("-Dfml.readTimeout=180")
                args.append("-Dfml.queryResult=confirm")

            # Minecraft-specific JVM args from version manifest
            if "jvm" in version_data.get("arguments", {}):
                for arg in version_data["arguments"]["jvm"]:
                    if isinstance(arg, str):
                        # Replace variables like ATLauncher does
                        arg = arg.replace(
                            "${natives_directory}",
                            str(self.minecraft_dir / "versions" / version / "natives"),
                        )
                        arg = arg.replace("${launcher_name}", "FFTLauncher")
                        arg = arg.replace("${launcher_version}", "1.0.0")
                        arg = arg.replace(
                            "${classpath}", self._build_classpath(version_data, version)
                        )
                        arg = arg.replace(
                            "${library_directory}",
                            str(self.minecraft_dir / "libraries"),
                        )
                        arg = arg.replace(
                            "${classpath_separator}",
                            ";" if platform.system() == "Windows" else ":",
                        )
                        arg = arg.replace("${version_name}", version)
                        args.append(arg)

            # Classpath
            args.extend(["-cp", self._build_classpath(version_data, version)])

            # Main class - use NeoForge main class for NeoForge versions
            if version.startswith("neoforge-"):
                main_class = "cpw.mods.bootstraplauncher.BootstrapLauncher"
            else:
                main_class = version_data.get(
                    "mainClass", "net.minecraft.client.main.Main"
                )
            args.append(main_class)

            # Game arguments
            game_args = self._build_game_arguments(version_data, version, profile_data)
            logging.info(f"Game arguments: {' '.join(game_args)}")
            args.extend(game_args)

            return args

        except Exception as e:
            logging.error(f"Failed to build Java command: {e}")
            return None

    def _find_compatible_java(self):
        """Find a compatible Java version (17 or 21) for Minecraft 1.21.1"""
        try:
            # Check current Java version first
            result = subprocess.run(
                ["java", "-version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                version_output = result.stderr
                # Extract version number
                import re

                version_match = re.search(r'"(\d+)\.', version_output)
                if version_match:
                    major_version = int(version_match.group(1))
                    if major_version in [17, 21]:
                        logging.info(f"Using system Java {major_version}")
                        return "java"
                    else:
                        logging.warning(
                            f"System Java version {major_version} is not compatible. Need Java 17 or 21."
                        )

            # Try to find Java 21 in common locations
            java_paths = []
            if platform.system() == "Windows":
                java_paths = [
                    "C:\\Program Files\\Java\\jdk-21\\bin\\java.exe",
                    "C:\\Program Files\\Java\\jre-21\\bin\\java.exe",
                    "C:\\Program Files\\Eclipse Adoptium\\jdk-21*\\bin\\java.exe",
                    "C:\\Program Files\\OpenJDK\\jdk-21*\\bin\\java.exe",
                    "C:\\Program Files\\Java\\jdk-17\\bin\\java.exe",
                    "C:\\Program Files\\Java\\jre-17\\bin\\java.exe",
                    "C:\\Program Files\\Eclipse Adoptium\\jdk-17*\\bin\\java.exe",
                    "C:\\Program Files\\OpenJDK\\jdk-17*\\bin\\java.exe",
                ]

            import glob

            for path_pattern in java_paths:
                matches = glob.glob(path_pattern)
                for java_path in matches:
                    if os.path.exists(java_path):
                        # Verify this Java version
                        try:
                            result = subprocess.run(
                                [java_path, "-version"], capture_output=True, text=True
                            )
                            if result.returncode == 0:
                                version_output = result.stderr
                                version_match = re.search(r'"(\d+)\.', version_output)
                                if version_match:
                                    major_version = int(version_match.group(1))
                                    if major_version in [17, 21]:
                                        logging.info(
                                            f"Found compatible Java {major_version} at: {java_path}"
                                        )
                                        return java_path
                        except:
                            continue

            logging.error(
                "No compatible Java version (17 or 21) found. Please install Java 17 or 21."
            )
            return None

        except Exception as e:
            logging.error(f"Error finding compatible Java: {e}")
            return None

    def _build_classpath(self, version_data, version):
        """Build the classpath string with all libraries and main JAR"""
        try:
            classpath_parts = []
            seen_libraries = set()  # Track library names to avoid duplicates

            # Add libraries
            libraries_dir = self.minecraft_dir / "libraries"
            if "libraries" in version_data:
                for lib in version_data["libraries"]:
                    if self._should_include_library(lib):
                        lib_path = self._get_library_path(lib, libraries_dir)
                        if lib_path and lib_path.exists():
                            lib_path_str = str(lib_path)
                            # Check for duplicates by comparing the actual file path
                            if lib_path_str not in seen_libraries:
                                classpath_parts.append(lib_path_str)
                                seen_libraries.add(lib_path_str)
                            # Removed excessive debug logging for each library
                        else:
                            logging.warning(
                                f"Library not found: {lib.get('name', 'unknown')} at {lib_path}"
                            )

            # For NeoForge, also check for the NeoForge universal jar
            if version.startswith("neoforge-"):
                # Add NeoForge specific libraries that might be in the version folder
                version_dir = self.minecraft_dir / "versions" / version
                universal_jar = version_dir / f"{version}-universal.jar"
                if universal_jar.exists():
                    universal_jar_str = str(universal_jar)
                    if universal_jar_str not in seen_libraries:
                        logging.info(f"Adding NeoForge universal jar: {universal_jar}")
                        classpath_parts.append(universal_jar_str)
                        seen_libraries.add(universal_jar_str)

            # Add main Minecraft JAR - this should be last in classpath for proper loading order
            jar_path = self.minecraft_dir / "versions" / version / f"{version}.jar"
            if jar_path.exists():
                jar_path_str = str(jar_path)
                if jar_path_str not in seen_libraries:
                    classpath_parts.append(jar_path_str)
                    seen_libraries.add(jar_path_str)
                else:
                    logging.warning(
                        f"Main JAR was already in classpath: {jar_path_str}"
                    )
            else:
                logging.error(f"Main Minecraft JAR not found: {jar_path}")

            # Join with appropriate separator
            separator = ";" if platform.system() == "Windows" else ":"
            classpath = separator.join(classpath_parts)

            logging.info(
                f"Built classpath with {len(classpath_parts)} unique entries (removed duplicates)"
            )

            # Only log classpath details in debug mode to avoid spam
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                if len(classpath) > 2000:  # Only log first part if very long
                    logging.debug(
                        f"Classpath (first 1000 chars): {classpath[:1000]}..."
                    )
                else:
                    logging.debug(f"Full classpath: {classpath}")

            return classpath

        except Exception as e:
            logging.error(f"Failed to build classpath: {e}")
            return ""

    def _should_include_library(self, library):
        """Check if a library should be included based on rules"""
        if "rules" not in library:
            return True

        # Process rules similar to ATLauncher
        for rule in library["rules"]:
            action = rule.get("action", "allow")

            # Check OS-specific rules
            if "os" in rule:
                os_rule = rule["os"]
                current_os = platform.system().lower()

                # Map platform names
                os_mapping = {"windows": "windows", "darwin": "osx", "linux": "linux"}

                rule_os = os_rule.get("name", "").lower()
                if rule_os in os_mapping.values():
                    if action == "allow" and rule_os != os_mapping.get(current_os):
                        return False
                    elif action == "disallow" and rule_os == os_mapping.get(current_os):
                        return False

                # Check architecture if specified
                if "arch" in os_rule:
                    import platform as plat

                    arch = plat.architecture()[0]
                    rule_arch = os_rule["arch"]
                    if rule_arch == "x86" and "64" in arch:
                        if action == "allow":
                            return False
                    elif rule_arch == "x86-64" and "32" in arch:
                        if action == "allow":
                            return False

            # If it's a disallow rule without specific conditions, exclude it
            if action == "disallow" and "os" not in rule:
                return False

        return True

    def _get_library_path(self, library, libraries_dir):
        """Get the path to a library file"""
        try:
            if "downloads" in library and "artifact" in library["downloads"]:
                artifact_path = library["downloads"]["artifact"]["path"]
                return libraries_dir / artifact_path

            # Fallback: construct path from name
            name = library.get("name", "")
            parts = name.split(":")
            if len(parts) >= 3:
                group, artifact, version = parts[0], parts[1], parts[2]
                path = (
                    "/".join(group.split("."))
                    + f"/{artifact}/{version}/{artifact}-{version}.jar"
                )
                return libraries_dir / path

            return None

        except Exception as e:
            logging.error(f"Failed to get library path: {e}")
            return None

    def _build_game_arguments(self, version_data, version, profile_data=None):
        """Build game-specific arguments using profile data"""
        try:
            args = []

            # Completely ignored arguments that cause launch issues (following ATLauncher approach)
            ignored_arguments = ["--xuid", "${auth_xuid}", "--clientId", "${clientid}"]

            # Get authentication info
            auth_info = self.auth_service.get_auth_info()
            if auth_info:
                username = auth_info["username"]
                uuid_str = auth_info["uuid"]
                access_token = auth_info["access_token"]
                # Don't use xuid or client_id for now as they cause issues
            else:
                # Fallback to fake data if no auth
                username = "Player"
                uuid_str = str(uuid.uuid4())
                access_token = "fake_access_token"

            # Use your instance directory from profile or constants
            if profile_data and "gameDir" in profile_data:
                game_dir = profile_data["gameDir"]
            else:
                game_dir = AppPath.INSTANCE_DIR.value

            # Standard game arguments
            if "game" in version_data.get("arguments", {}):
                for arg in version_data["arguments"]["game"]:
                    if isinstance(arg, str):
                        # Skip problematic arguments that cause launch issues
                        if arg in ignored_arguments:
                            logging.debug(f"Skipping problematic argument: {arg}")
                            continue

                        # Replace variables
                        arg = arg.replace("${auth_player_name}", username)
                        arg = arg.replace("${version_name}", version)
                        arg = arg.replace("${game_directory}", game_dir)
                        arg = arg.replace(
                            "${assets_root}", str(self.minecraft_dir / "assets")
                        )
                        arg = arg.replace(
                            "${assets_index_name}",
                            version_data.get("assetIndex", {}).get("id", version),
                        )
                        arg = arg.replace("${auth_uuid}", uuid_str)
                        arg = arg.replace("${auth_access_token}", access_token)
                        arg = arg.replace(
                            "${user_type}", "msa" if auth_info else "offline"
                        )  # Use proper user type
                        arg = arg.replace(
                            "${version_type}", version_data.get("type", "release")
                        )
                        # Skip clientid and xuid variables completely
                        if "${clientid}" in arg or "${auth_xuid}" in arg:
                            logging.debug(
                                f"Skipping argument with clientid/xuid: {arg}"
                            )
                            continue
                        args.append(arg)
            else:
                # Fallback for older versions - don't include problematic parameters
                args.extend(
                    [
                        "--username",
                        username,
                        "--version",
                        version,
                        "--gameDir",
                        game_dir,
                        "--assetsDir",
                        str(self.minecraft_dir / "assets"),
                        "--assetIndex",
                        version_data.get("assetIndex", {}).get("id", version),
                        "--uuid",
                        uuid_str,
                        "--accessToken",
                        access_token,
                        "--userType",
                        "msa" if auth_info else "offline",
                    ]
                )
                # Completely skip --xuid and --clientId parameters to avoid launch issues

            logging.info(f"Using game directory: {game_dir}")
            return args

        except Exception as e:
            logging.error(f"Failed to build game arguments: {e}")
            return []
