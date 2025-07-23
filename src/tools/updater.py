import logging
import os
import sys
from src.models.constants import get_downloads_dir
import subprocess
import time
import tkinter as tk
from tkinter import ttk


def get_base_directory():
    """Get the directory where the executable or script is located"""
    # Always use the root directory passed as the first argument, or fallback to executable/script dir
    if len(sys.argv) > 1:
        return os.path.abspath(sys.argv[1])
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))




# Always log to the logs directory in the root app folder (passed as first argument)
if len(sys.argv) > 1:
    root_dir = sys.argv[1]
else:
    # Fallback: use the directory of the executable or script
    root_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
logs_dir = os.path.join(root_dir, "logs")
os.makedirs(logs_dir, exist_ok=True)
log_file = os.path.join(logs_dir, "updater.log")
logging.basicConfig(
    filename=log_file,
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logging.info("Updater started.")


class UpdateProgress:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Updating...")
        self.root.geometry("300x80")
        self.root.resizable(False, False)

        # Center the window
        self.root.eval("tk::PlaceWindow . center")

        # Remove window decorations for clean look
        self.root.overrideredirect(True)

        # Create progress bar
        self.progress = ttk.Progressbar(self.root, length=250, mode="determinate")
        self.progress.pack(pady=20)

        # Status label
        self.status = tk.Label(self.root, text="Initializing...", font=("Arial", 9))
        self.status.pack()

        self.root.update()

    def update_progress(self, value, status_text):
        self.progress["value"] = value
        self.status.config(text=status_text)
        self.root.update()

    def close(self):
        self.root.destroy()


def replace_file():
    """Replace FFTLauncher.exe with FFTLauncher.update"""
    progress = UpdateProgress()
    logging.info("[Updater] Starting update process.")

    base_dir = get_base_directory()
    logging.debug(f"[Updater] Base directory: {base_dir}")
    exe_file = os.path.join(base_dir, "FFTLauncher.exe")
    downloads_dir = get_downloads_dir()
    update_file = os.path.join(downloads_dir, "FFTLauncher.exe")

    logging.debug(f"[Updater] exe_file: {exe_file}")
    logging.debug(f"[Updater] downloads_dir: {downloads_dir}")
    logging.debug(f"[Updater] update_file (from downloads): {update_file}")

    # Wait for the update file to appear (up to 30 seconds)
    progress.update_progress(10, "Waiting for update file in downloads...")
    try:
        found = False
        for i in range(30):
            logging.debug(f"[Updater] Checking for update file, attempt {i+1}/30...")
            if os.path.exists(update_file):
                found = True
                logging.info("[Updater] Update file found in downloads.")
                break
            progress.update_progress(
                10 + (i * 2), f"Waiting for update file... ({i+1}/30)"
            )
            time.sleep(1)

        if not found:
            logging.error("[Updater] Update file not found in downloads after waiting.")
            progress.update_progress(100, "Update file not found!")
            time.sleep(2)
            return False

        # Wait for file to be fully written
        progress.update_progress(70, "Preparing update...")
        logging.info("[Updater] Preparing update...")
        time.sleep(2)

        # Remove the exe file if it exists
        progress.update_progress(80, "Removing old launcher...")
        if os.path.exists(exe_file):
            try:
                logging.debug(f"[Updater] Attempting to remove old launcher: {exe_file}")
                os.remove(exe_file)
                logging.info("[Updater] Old launcher removed.")
            except Exception as e:
                logging.error(f"[Updater] Failed to remove old launcher: {e}")
                raise
        else:
            logging.debug(f"[Updater] Old launcher not found at: {exe_file}")

        # Move update file from downloads to root as exe
        progress.update_progress(90, "Installing update...")
        try:
            logging.debug(f"[Updater] Moving update file from {update_file} to {exe_file}")
            os.rename(update_file, exe_file)
            logging.info("[Updater] Update file moved from downloads to launcher executable.")
            # Delete the update file from downloads if it still exists (shouldn't, but for safety)
            if os.path.exists(update_file):
                logging.warning(f"[Updater] Update file still exists after move, removing: {update_file}")
                os.remove(update_file)
        except Exception as e:
            logging.error(f"[Updater] Failed to move update file: {e}")
            raise

        # Launch the new executable
        progress.update_progress(95, "Launching updated launcher...")
        try:
            logging.debug(f"[Updater] Launching new executable: {exe_file}")
            subprocess.Popen([exe_file], creationflags=subprocess.CREATE_NO_WINDOW)
            logging.info("[Updater] Launched updated launcher.")
        except Exception as e:
            logging.error(f"[Updater] Failed to launch updated launcher: {e}")

        progress.update_progress(100, "Update complete!")
        logging.info("[Updater] Update complete!")
        time.sleep(1)
        return True
    except Exception as e:
        logging.error(f"[Updater] Update failed: {e}")
        progress.update_progress(100, "Update failed!")
        time.sleep(2)
        return False
    finally:
        progress.close()
        logging.info("[Updater] Updater exiting.")


def main():
    try:
        replace_file()
    except Exception:
        pass
    # Exit immediately without any output or pause
    sys.exit(0)


if __name__ == "__main__":
    main()
