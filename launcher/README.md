# FFT Minecraft Launcher

A modern Minecraft launcher with automatic updates using a bootstrap pattern to solve Windows file locking issues.

## Project Structure

```
FFTMinecraftLauncher/
├── src/                     # Main launcher source code
│   ├── core/               # Core launcher functionality
│   ├── models/             # Data models
│   ├── services/           # Business logic services
│   ├── ui/                 # User interface components
│   └── utils/              # Utility functions
├── bootstrap/              # Bootstrap system
│   ├── bootstrap.py        # Bootstrap launcher script
│   └── bootstrap.spec      # PyInstaller spec for bootstrap
├── scripts/                # Build and deployment scripts
│   └── build_bootstrap.bat # Main build script
├── assets/                 # Static assets (icons, etc.)
├── .vscode/                # VS Code configuration
├── app.py                  # Main launcher entry point
├── version.json            # Version configuration
└── requirements.txt        # Python dependencies
```

## How It Works

### Bootstrap Pattern
1. **FFTMinecraftLauncher.exe** (small bootstrap) checks for updates
2. Downloads latest **launcher_package.zip** from GitHub releases if needed
3. Extracts main launcher to `launcher/` directory
4. Launches the main launcher and exits

This solves Windows file locking issues during self-updates.

## Development

### Requirements
- Python 3.13+
- Virtual environment in `_env/`

### Building
Use VS Code action buttons or run manually:
```bash
./scripts/build_bootstrap.bat
```

### Release Process
1. Update `version.json`
2. Click **Build** button in VS Code
3. Click **Release** button to create GitHub release

## Features
- ✅ Automatic updates via bootstrap pattern
- ✅ Clean UI with PyQt6
- ✅ Minecraft profile management
- ✅ NeoForge mod support
- ✅ GitHub integration for releases

