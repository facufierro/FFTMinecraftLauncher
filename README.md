# FFT Minecraft Launcher

A modern, modular Minecraft launcher with GitHub integration for automatic mod and configuration synchronization.

## Project Structure

```
FFTMinecraftLauncher/
├── src/                          # Source code
│   ├── core/                     # Core launcher logic
│   │   ├── __init__.py
│   │   ├── launcher.py           # Main launcher coordinator
│   │   └── events.py             # Event system
│   ├── models/                   # Data models
│   │   ├── __init__.py
│   │   ├── config.py             # Configuration model
│   │   └── update_info.py        # Update information model
│   ├── services/                 # Business logic services
│   │   ├── __init__.py
│   │   ├── github_service.py     # GitHub API interactions
│   │   ├── update_service.py     # Update management
│   │   └── minecraft_service.py  # Minecraft operations
│   ├── ui/                       # User interface
│   │   ├── __init__.py
│   │   ├── main_window.py        # Main application window
│   │   ├── settings_window.py    # Settings dialog
│   │   └── components.py         # Reusable UI components
│   ├── utils/                    # Utility modules
│   │   ├── __init__.py
│   │   ├── logger.py             # Logging utilities
│   │   ├── file_utils.py         # File operations
│   │   └── ui_utils.py           # UI utilities
│   └── __init__.py
├── main.py                       # Application entry point
├── app.py                        # Legacy entry point (deprecated)
├── launcher_config.json          # Configuration file
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Features

- **Modular Architecture**: Clean separation of concerns with dedicated modules for different responsibilities
- **GitHub Integration**: Automatic synchronization with GitHub releases
- **Event-Driven**: Reactive UI updates through an event system
- **Configuration Management**: JSON-based configuration with validation
- **Comprehensive Logging**: Both file and UI logging with multiple levels
- **Modern UI**: CustomTkinter-based interface with theme support
- **Error Handling**: Robust error handling throughout the application
- **Type Safety**: Full type hints for better code quality

## Architecture

### Core Components

1. **LauncherCore** (`src/core/launcher.py`)
   - Central coordinator for all launcher operations
   - Manages configuration, services, and events
   - Provides high-level API for UI interactions

2. **Event System** (`src/core/events.py`)
   - Publisher-subscriber pattern for loose coupling
   - Allows UI to react to backend changes
   - Extensible event types for future features

3. **Configuration Model** (`src/models/config.py`)
   - Type-safe configuration management
   - JSON serialization with validation
   - Default values and error handling

### Services

1. **GitHubService** (`src/services/github_service.py`)
   - GitHub API interactions
   - Release fetching and download management
   - Repository information retrieval

2. **UpdateService** (`src/services/update_service.py`)
   - File synchronization logic
   - Progress tracking and reporting
   - Atomic update operations

3. **MinecraftService** (`src/services/minecraft_service.py`)
   - Minecraft installation validation
   - Executable detection and launching
   - Installation information gathering

### User Interface

1. **MainWindow** (`src/ui/main_window.py`)
   - Primary application interface
   - Event-driven updates
   - Responsive design

2. **Components** (`src/ui/components.py`)
   - Reusable UI widgets
   - Consistent styling
   - Modular design

### Utilities

1. **Logger** (`src/utils/logger.py`)
   - Dual logging (file + UI)
   - Configurable log levels
   - Centralized logging management

2. **FileUtils** (`src/utils/file_utils.py`)
   - Safe file operations
   - Hash calculation
   - Directory management

## Usage

### Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run the launcher
python main.py
```

### Configuration

The launcher uses `launcher_config.json` for configuration. Key settings include:

- `github_repo`: Repository to sync from (format: "owner/repo")
- `minecraft_dir`: Path to Minecraft installation
- `minecraft_executable`: Name of Minecraft executable
- `folders_to_sync`: List of folders to synchronize
- `check_on_startup`: Whether to check for updates on startup
- `auto_update`: Whether to update automatically without prompting

### Extending the Launcher

#### Adding New Events

1. Add event type to `EventType` enum in `src/core/events.py`
2. Emit events using `launcher_core.events.emit(EventType.YOUR_EVENT, data)`
3. Subscribe to events using `launcher_core.events.subscribe(EventType.YOUR_EVENT, callback)`

#### Adding New Services

1. Create service class in `src/services/`
2. Initialize in `LauncherCore._initialize_services()`
3. Add to `src/services/__init__.py`

#### Adding New UI Components

1. Create component class inheriting from appropriate CTk widget
2. Add to `src/ui/components.py`
3. Use in main window or settings window

## Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Dependency Injection**: Services are injected into classes that need them
3. **Event-Driven Architecture**: Loose coupling through events
4. **Configuration Over Code**: Behavior controlled through configuration
5. **Error Handling**: Graceful degradation and user-friendly error messages
6. **Type Safety**: Comprehensive type hints for maintainability
7. **Testability**: Modular design enables easy unit testing

## Migration from Legacy Code

The legacy `app.py` has been restructured into this modular architecture. Key changes:

- Monolithic class split into specialized services
- UI and business logic separated
- Configuration externalized and typed
- Event system replaces direct method calls
- Comprehensive error handling added
- Modern Python practices adopted

## Future Enhancements

- Plugin system for custom functionality
- Multiple repository support
- Incremental updates with file diffing
- GUI theme customization
- Automated testing suite
- Package distribution (exe, installer)
- Configuration backup and restore
- Update rollback functionality

## Legacy Support

The original `app.py` is still available for backward compatibility but is deprecated. Please use `main.py` for the new modular architecture.
