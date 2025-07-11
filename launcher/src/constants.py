"""Constants for the FFT Minecraft Launcher."""

# GitHub Repository Configuration
GITHUB_REPO = "facufierro/FFTClientMinecraft1211"

# Default Sync Folders
DEFAULT_SYNC_FOLDERS = [
    "config", 
    "mods", 
    "resourcepacks", 
    "kubejs", 
    "scripts", 
    "defaultconfigs"
]

# Note: Versions are now dynamic!
# - Launcher version: Read from version.json (generated during build)
# - Client version: Fetched from GitHub API (FFTClientMinecraft1211 repo)
# Use src.utils.github_utils for dynamic version management
