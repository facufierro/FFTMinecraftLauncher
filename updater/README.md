# App Updater

A modular, GitHub-based application updater that downloads and replaces files from a GitHub repository.

## Features

- **GitHub Integration**: Downloads files directly from GitHub repositories
- **Process Management**: Automatically closes running applications before updating
- **Safe Updates**: Creates backups and handles rollback on failure
- **Clean GUI**: Simple, user-friendly interface
- **Error Handling**: Comprehensive error reporting and recovery
- **Modularity**: Clean architecture with separation of concerns
- **CLI Support**: Command-line options for headless operation
- **Configuration**: JSON-based configuration options

## Architecture

The project follows a modular architecture:

- **Models** - Core business logic
  - `app_updater.py` - Handles file downloading, replacement and launching
- **Services** - Application services
  - `updater_service.py` - Orchestrates the update process
- **UI** - User interfaces
  - `updater_gui.py` - Tkinter-based GUI

## Structure

```
app.py                # Main entry point
config.json           # Configuration file
src/
  __init__.py         # Package initialization
  models/             # Core business logic
    __init__.py
    app_updater.py    # Download and replace functionality
  services/           # Application services
    __init__.py
    updater_service.py # Service orchestration
  ui/                 # User interfaces
    __init__.py
    updater_gui.py    # Tkinter GUI
scripts/
  build.ps1           # Build script
  specs/
    updater.spec      # PyInstaller specification
dist/
  updater.exe         # Compiled executable
```

## Configuration

Create a `config.json` file:

```json
{
    "target_file": "app.exe",
    "github_repo": "username/repository",
    "github_file_path": "path/to/file.exe",
    "auto_launch": true
}
```

## Usage

### Basic Usage

```bash
python app.py
```

### Command-line Options

```bash
# Use custom configuration
python app.py --config custom_config.json

# Run in headless mode (no GUI)
python app.py --headless

# Don't launch the application after update
python app.py --no-launch
```

## How It Works

1. **Launch**: User runs `app.py` or the compiled executable
2. **Configure**: Loads settings from configuration file or defaults
3. **Close**: Automatically closes any running instances of the target app
4. **Download**: Downloads the latest version from GitHub
5. **Replace**: Safely replaces the target file with backup/rollback support
6. **Launch**: Starts the updated application (if configured)

## Building

Run the build script:
```powershell
.\scripts\build.ps1
```

## Dependencies

- `psutil`: Process management
- `requests`: HTTP downloads
- `tkinter`: GUI (included with Python)

## Advanced Usage

### Service Integration

The modular architecture allows for easy integration with other systems:

```python
from src.services.updater_service import UpdaterService

# Create service with custom configuration
service = UpdaterService({
    "target_file": "custom_app.exe",
    "github_repo": "username/repository",
    "github_file_path": "releases/latest.exe"
})

# Run update process
service.run()
```
