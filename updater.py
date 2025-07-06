#!/usr/bin/env python3
"""
FFT Launcher Updater
Simple updater that replaces the main launcher executable and restarts it.
"""

import sys
import os
import time
import subprocess
import shutil
from pathlib import Path


def main():
    """Main updater function."""
    if len(sys.argv) != 4:
        print("Usage: updater.exe <old_exe_path> <new_exe_path> <launcher_args>")
        sys.exit(1)
    
    old_exe_path = Path(sys.argv[1])
    new_exe_path = Path(sys.argv[2])
    launcher_args = sys.argv[3] if sys.argv[3] != "None" else ""
    
    print(f"FFT Launcher Updater")
    print(f"Updating: {old_exe_path}")
    print(f"From: {new_exe_path}")
    
    try:
        # Wait a moment for the main launcher to fully exit
        print("Waiting for launcher to exit...")
        time.sleep(3)
        
        # Verify the new exe exists
        if not new_exe_path.exists():
            print(f"Error: New executable not found at {new_exe_path}")
            input("Press Enter to exit...")
            sys.exit(1)
        
        # Create backup of old exe
        backup_path = old_exe_path.with_suffix('.exe.backup')
        if old_exe_path.exists():
            print("Creating backup...")
            shutil.copy2(old_exe_path, backup_path)
        
        # Replace the old executable with the new one
        print("Installing update...")
        if old_exe_path.exists():
            os.remove(old_exe_path)
        
        shutil.move(str(new_exe_path), str(old_exe_path))
        
        # Verify the replacement was successful
        if not old_exe_path.exists():
            print("Error: Failed to install new executable")
            # Restore backup if possible
            if backup_path.exists():
                print("Restoring backup...")
                shutil.move(str(backup_path), str(old_exe_path))
            input("Press Enter to exit...")
            sys.exit(1)
        
        print("Update completed successfully!")
        
        # Launch the updated launcher
        print("Starting updated launcher...")
        if launcher_args:
            subprocess.Popen([str(old_exe_path)] + launcher_args.split())
        else:
            subprocess.Popen([str(old_exe_path)])
        
        # Clean up backup after successful launch
        time.sleep(2)
        if backup_path.exists():
            try:
                os.remove(backup_path)
            except:
                pass  # Don't fail if we can't clean up backup
        
        print("Launcher restarted. Updater exiting.")
        
    except Exception as e:
        print(f"Update failed: {e}")
        
        # Try to restore backup
        backup_path = old_exe_path.with_suffix('.exe.backup')
        if backup_path.exists() and not old_exe_path.exists():
            try:
                print("Restoring backup...")
                shutil.move(str(backup_path), str(old_exe_path))
                print("Backup restored.")
            except Exception as restore_error:
                print(f"Failed to restore backup: {restore_error}")
        
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
