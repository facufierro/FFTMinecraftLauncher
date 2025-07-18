## Launcher Flow: Implementation Checklist

### 1. Startup
- **Start the launcher**
  - Entry point for the application.

### 2. Updater Handling
- **Replace the updater**
  - Ensure the updater executable is up-to-date before proceeding.

### 3. Launcher Update
- **Check for launcher updates**
  - If an update is available:
    - Run the updater
    - Close the launcher
    - Apply the update
    - Restart the launcher

### 4. Profile Management
- **Check for profile updates**
  - If the profile name is missing in `launcher_settings` inside `.minecraft`, add it.

### 5. Loader Management
- **Check loader updates in `versions.json`**
  - If the loader is not installed, install it in `.minecraft`.
  - If an update is needed, remove the old loader and install the new version.

### 6. Instance Setup
- **Check instance installation**
  - If the instance is missing, create a new one at the root directory.

### 7. Configurations
- **Check `defaultconfigs` folder**
  - If configs are present, replace the corresponding files in the `config` folder.

### 8. Folder Integrity Checks
- **Check `kubejs` folder for anomalies**
  - Replace if necessary.
- **Check ``modflared`` folder for anomalies**
  - Replace if necessary.
- **Check `mods` folder for anomalies**
  - Replace if necessary.

### 9. Resource Packs
- **Check `resourcepacks` folder for required packs (from `constants.py`)**
  - Replace or add required packs as needed (do not remove non-required packs).
  - Activate required packs with the correct priority.

### 10. Shaders
- **Check `shaders` folder**
  - Add recommended shaders without removing existing ones.

### 11. Server List
- **Replace `servers.dat`**
  - Use the new version provided.