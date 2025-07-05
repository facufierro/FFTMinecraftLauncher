# FFT Minecraft Launcher

A Python-based launcher that automatically syncs specific folders from a GitHub repository to your local Minecraft client directory before launching the game.

## Features

- **Automatic Updates**: Checks for updates from your GitHub repository
- **Selective Sync**: Only syncs specified folders (config, mods, resourcepacks, etc.)
- **User-Friendly GUI**: Modern interface with progress tracking and logging
- **Configurable**: Easy-to-edit settings for repository, folders, and behavior
- **Safe Updates**: Downloads and extracts safely before replacing files

## Setup Instructions

### 1. Prerequisites
- Python 3.7 or higher installed on your system
- Internet connection
- Your Minecraft modpack files in a GitHub repository

### 2. Configuration

Edit `launcher_config.json` to configure your launcher:

```json
{
    "github_repo": "yourusername/your-minecraft-repo",
    "github_branch": "main",
    "minecraft_dir": "../FFTClientMinecraft1211",
    "folders_to_sync": [
        "config",
        "mods",
        "resourcepacks",
        "kubejs",
        "scripts",
        "defaultconfigs"
    ],
    "minecraft_executable": "minecraft.exe",
    "check_on_startup": true,
    "auto_update": false
}
```

**Key Settings:**
- `github_repo`: Your GitHub repository in format "username/repository-name"
- `github_branch`: The branch to sync from (usually "main" or "master")
- `minecraft_dir`: Path to your Minecraft client directory
- `folders_to_sync`: List of folders to sync from the repository
- `minecraft_executable`: Name of the Minecraft executable file
- `check_on_startup`: Whether to check for updates when launcher starts
- `auto_update`: Whether to auto-update without user confirmation

### 3. Repository Structure

Your GitHub repository should have the following structure:
```
your-minecraft-repo/
├── config/           # Mod configurations
├── mods/            # Mod files (.jar)
├── resourcepacks/   # Resource packs
├── kubejs/          # KubeJS scripts
├── scripts/         # CraftTweaker scripts
├── defaultconfigs/  # Default configurations
└── README.md        # Repository documentation
```

### 4. Running the Launcher

#### Option 1: Use the Batch File (Recommended)
Double-click `run_launcher.bat` - this will:
- Install required Python packages
- Start the launcher GUI

#### Option 2: Manual Run
```powershell
# Install dependencies
pip install -r requirements.txt

# Run launcher
python launcher.py
```

## How It Works

1. **Startup Check**: When launched, checks your specified GitHub repository
2. **Comparison**: Compares local files with repository contents
3. **Update Detection**: Identifies which folders need updating
4. **Download**: Downloads the entire repository as a ZIP file
5. **Selective Sync**: Extracts and copies only the specified folders
6. **Launch**: Starts your Minecraft client

## Usage

### Main Interface
- **Check for Updates**: Manually check if updates are available
- **Update Files**: Download and apply updates from the repository
- **Launch Minecraft**: Start your Minecraft client
- **Settings**: Configure repository, folders, and behavior

### Settings Dialog
- Change GitHub repository and branch
- Modify which folders to sync
- Set Minecraft directory and executable
- Enable/disable automatic checking and updating

## Troubleshooting

### Common Issues

1. **"Repository not found" error**
   - Check that your `github_repo` setting is correct
   - Ensure the repository is public or you have access
   - Verify the branch name exists

2. **"Minecraft directory not found"**
   - Check the `minecraft_dir` path in settings
   - Make sure the path is relative to the launcher or use absolute path

3. **"Permission denied" errors**
   - Run as administrator if needed
   - Close Minecraft before updating
   - Check that files aren't read-only

4. **Python not found**
   - Install Python from python.org
   - Make sure Python is added to your system PATH

### Log Files
Check the log area in the launcher for detailed error messages and update progress.

## Advanced Configuration

### Custom Folder Structure
You can sync any folders by modifying the `folders_to_sync` list in the configuration.

### Multiple Repositories
Create separate launcher instances in different directories for different modpacks.

### Automatic Updates
Enable `auto_update` to automatically apply updates without user confirmation (use with caution).

## Security Notes

- The launcher downloads files from public GitHub repositories
- Only specified folders are modified in your Minecraft directory
- Original files are backed up by replacement, not deletion
- No sensitive information is transmitted

## License

This launcher is provided as-is for educational and personal use.
