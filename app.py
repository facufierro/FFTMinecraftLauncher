
# FFT Minecraft Launcher (customtkinter version)
# A launcher that syncs specific folders from GitHub repo before launching Minecraft client.

import os
import sys
import json
import shutil
import hashlib
import requests
import zipfile
import threading
import customtkinter as ctk
from tkinter import messagebox
from pathlib import Path
import subprocess
from datetime import datetime

class MinecraftLauncher:
    def __init__(self):
        ctk.set_appearance_mode("System")  # or "Dark"/"Light"
        ctk.set_default_color_theme("dark-blue")
        self.root = ctk.CTk()
        self.root.title("FFT Minecraft Launcher")
        self.center_window(self.root, 800, 600)
        self.root.resizable(True, True)
        self.night_mode = False

    def center_window(self, window, width, height):
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Configuration
        self.config_file = "launcher_config.json"
        self.load_config()
        self.night_mode = self.config.get('night_mode', False)
        
        # Paths
        self.launcher_dir = Path(__file__).parent
        self.minecraft_dir = Path(self.config.get("minecraft_dir", "../FFTClientMinecraft1211"))
        
        # State
        self.is_updating = False
        self.update_thread = None
        
        self.setup_ui()
        self.add_dark_mode_toggle()

    def add_dark_mode_toggle(self):
        # Place a button with a sun/moon icon in the top right using CTkButton
        self.dark_mode_btn = ctk.CTkButton(self.root, text="🌙", width=40, command=self.toggle_night_mode)
        self.dark_mode_btn.place(relx=1.0, x=-10, y=10, anchor='ne')

    def toggle_night_mode(self):
        # Use customtkinter's built-in appearance mode
        current = ctk.get_appearance_mode()
        if current == "Dark":
            ctk.set_appearance_mode("Light")
            self.dark_mode_btn.configure(text="🌙")
        else:
            ctk.set_appearance_mode("Dark")
            self.dark_mode_btn.configure(text="☀️")
    # No longer needed with customtkinter
        
    def load_config(self):
        """Load configuration from JSON file"""
        default_config = {
            # github_repo, use_releases, and release_tag are now hardcoded in code, not in config
            "minecraft_dir": "../FFTClientMinecraft1211",
            "folders_to_sync": [
                "config",
                "mods",
                "resourcepacks",
                "kubejs",
                "scripts"
            ],
            "minecraft_executable": "minecraft.exe",
            "check_on_startup": True,
            "auto_update": False,
            "current_version": None
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    self.config = {**default_config, **loaded_config}
            else:
                self.config = default_config
                self.save_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config = default_config
    
    def save_config(self):
        """Save configuration to JSON file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_ui(self):
        """Setup the user interface using customtkinter"""
        # Main frame
        main_frame = ctk.CTkFrame(self.root, corner_radius=10)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

        # Title
        title_label = ctk.CTkLabel(main_frame, text="FFT Minecraft Launcher", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Status frame
        status_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        status_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(status_frame, text="Repository:").grid(row=0, column=0, sticky="w")
        self.repo_label = ctk.CTkLabel(status_frame, text="facufierro/FFTClientMinecraft1211")
        self.repo_label.grid(row=0, column=1, sticky="w", padx=(10, 0))

        ctk.CTkLabel(status_frame, text="Local Directory:").grid(row=1, column=0, sticky="w")
        self.dir_label = ctk.CTkLabel(status_frame, text=str(self.minecraft_dir.resolve()))
        self.dir_label.grid(row=1, column=1, sticky="w", padx=(10, 0))

        ctk.CTkLabel(status_frame, text="Last Check:").grid(row=2, column=0, sticky="w")
        self.last_check_label = ctk.CTkLabel(status_frame, text="Never")
        self.last_check_label.grid(row=2, column=1, sticky="w", padx=(10, 0))

        # Progress frame
        progress_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        progress_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)

        self.progress_var = ctk.StringVar(value="Ready")
        self.progress_label = ctk.CTkLabel(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        self.progress_bar.set(0)

        # Buttons frame
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))

        self.check_button = ctk.CTkButton(buttons_frame, text="Check for Updates", command=self.check_updates)
        self.check_button.grid(row=0, column=0, padx=(0, 10))

        self.update_button = ctk.CTkButton(buttons_frame, text="Update Files", command=self.update_files, state="disabled")
        self.update_button.grid(row=0, column=1, padx=(0, 10))

        self.force_update_button = ctk.CTkButton(buttons_frame, text="Force Update", command=self.force_update)
        self.force_update_button.grid(row=0, column=4, padx=(0, 10))

        self.launch_button = ctk.CTkButton(buttons_frame, text="Launch Minecraft", command=self.launch_minecraft, state="disabled")
        self.launch_button.grid(row=0, column=2, padx=(0, 10))

        self.settings_button = ctk.CTkButton(buttons_frame, text="Settings", command=self.open_settings)
        self.settings_button.grid(row=0, column=3)

        # Log frame
        log_frame = ctk.CTkFrame(main_frame, corner_radius=8)
        log_frame.grid(row=4, column=0, columnspan=3, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = ctk.CTkTextbox(log_frame, height=250, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # Initialize
        self.log("Launcher initialized")
        self.check_minecraft_dir()

        if self.config.get('check_on_startup', True):
            self.root.after(1000, self.check_updates)  # Check after 1 second
    
    def log(self, message):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"

        self.log_text.configure(state='normal')
        self.log_text.insert('end', formatted_message)
        self.log_text.see('end')
        self.log_text.configure(state='disabled')

        print(f"LOG: {message}")  # Also print to console
    
    def check_minecraft_dir(self):
        """Check if Minecraft directory exists and is accessible"""
        if not self.minecraft_dir.exists():
            self.log(f"Warning: Minecraft directory not found: {self.minecraft_dir}")
            self.launch_button.configure(state='disabled')
            return False

        self.log(f"Minecraft directory found: {self.minecraft_dir}")
        self.launch_button.configure(state='normal')
        return True
    
    def check_updates(self):
        """Check for updates from GitHub releases"""
        if self.is_updating:
            return
        
        self.is_updating = True
        self.check_button.configure(state='disabled')
        self.progress_bar.start()
        self.progress_var.set("Checking for updates...")
        
        def check_thread():
            try:
                github_repo = "facufierro/FFTClientMinecraft1211"
                # Always use GitHub releases and latest tag
                releases_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
                self.log("Checking for new releases...")
                response = requests.get(releases_url, timeout=10)
                if response.status_code == 200:
                    release_data = response.json()
                    latest_version = release_data['tag_name']
                    current_version = self.config.get('current_version')
                    self.log(f"Latest release: {latest_version}")
                    self.log(f"Current version: {current_version or 'None'}")
                    updates_needed = current_version != latest_version
                    self.root.after(0, self.check_complete_releases, updates_needed, latest_version, release_data)
                else:
                    self.root.after(0, self.check_error, f"Could not fetch release info: HTTP {response.status_code}")
            except Exception as e:
                self.root.after(0, self.check_error, str(e))
        
        self.update_thread = threading.Thread(target=check_thread, daemon=True)
        self.update_thread.start()
    
    def folder_needs_update(self, local_folder, remote_files):
        """Compare local folder with remote files to see if update is needed"""
        if not local_folder.exists():
            return True
        
        # Simple comparison - in a real implementation you might want to check file hashes
        # For now, we'll assume updates are needed if remote has files we don't have
        try:
            local_files = set(f.name for f in local_folder.rglob('*') if f.is_file())
            remote_filenames = set(item['name'] for item in remote_files if item['type'] == 'file')
            
            # Check if remote has files we don't have
            return not remote_filenames.issubset(local_files)
        except Exception:
            return True  # If we can't compare, assume update is needed
    
    def check_complete_releases(self, updates_needed, latest_version, release_data):
        """Called when release-based update check is complete"""
        self.is_updating = False
        self.progress_bar.stop()
        self.check_button.configure(state='normal')
        self.last_check_label.configure(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if updates_needed:
            self.progress_var.set(f"New release available: {latest_version}")
            self.update_button.configure(state='normal')
            self.log(f"New release available: {latest_version}")
            self.latest_release_data = release_data  # Store for download
        else:
            self.progress_var.set(f"Up to date (Version: {latest_version})")
            self.update_button.configure(state='disabled')
            self.log(f"Already up to date with version: {latest_version}")
    
    def check_complete(self, updates_needed):
        """Called when update check is complete"""
        self.is_updating = False
        self.progress_bar.stop()
        self.check_button.configure(state='normal')
        self.last_check_label.configure(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if updates_needed:
            self.progress_var.set(f"Updates available for: {', '.join(updates_needed)}")
            self.update_button.configure(state='normal')
            self.log(f"Found updates for {len(updates_needed)} folders")
        else:
            self.progress_var.set("All files up to date")
            self.update_button.configure(state='disabled')
            self.log("All files are up to date")
    
    def check_error(self, error_msg):
        """Called when update check fails"""
        self.is_updating = False
        self.progress_bar.stop()
        self.check_button.configure(state='normal')
        self.progress_var.set("Error checking updates")
        self.log(f"Error checking updates: {error_msg}")
        messagebox.showerror("Error", f"Failed to check for updates:\n{error_msg}")
    
    def update_files(self):
        """Download and update files from repository or release"""
        # ...existing code...

    def force_update(self):
        """Force update: always download and overwrite everything from the release, even if up to date."""
        # ...existing code...
        """Force update: always download and overwrite everything from the release, even if up to date."""
        if self.is_updating:
            return
        self.is_updating = True
        self.update_button.configure(state='disabled')
        self.check_button.configure(state='disabled')
        self.progress_bar.start()
        self.progress_var.set("Force updating files...")

        def force_update_thread():
            try:
                github_repo = "facufierro/FFTClientMinecraft1211"
                # Always fetch the latest release data, even if current_version matches
                releases_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
                self.log("Force update: fetching release info...")
                response = requests.get(releases_url, timeout=10)
                if response.status_code == 200:
                    release_data = response.json()
                    self.latest_release_data = release_data
                    # Now run the update_files logic, but always update
                    # Download from release
                    download_url = None
                    for asset in release_data.get('assets', []):
                        if asset['name'].endswith('.zip'):
                            download_url = asset['browser_download_url']
                            break
                    if not download_url:
                        download_url = release_data['zipball_url']
                    self.log(f"Force downloading release {release_data['tag_name']} from: {download_url}")
                    resp = requests.get(download_url, timeout=30)
                    resp.raise_for_status()
                    zip_path = self.launcher_dir / "temp_update.zip"
                    with open(zip_path, 'wb') as f:
                        f.write(resp.content)
                    self.log("Extracting files...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        extract_path = self.launcher_dir / "temp_extract"
                        zip_ref.extractall(extract_path)
                    repo_folders = list(extract_path.glob("*"))
                    if repo_folders:
                        repo_folder = repo_folders[0]
                        extracted_items = [p for p in repo_folder.iterdir()]
                        self.log(f"Extracted repo folder contents: {[p.name for p in extracted_items]}")
                        for item in extracted_items:
                            dst_path = self.minecraft_dir / item.name
                            self.log(f"Force syncing '{item.name}' to '{dst_path}'")
                            if item.is_dir():
                                if dst_path.exists():
                                    shutil.rmtree(dst_path)
                                shutil.copytree(item, dst_path)
                            else:
                                shutil.copy2(item, dst_path)
                    self.config['current_version'] = release_data['tag_name']
                    self.save_config()
                    shutil.rmtree(extract_path)
                    zip_path.unlink()
                    self.root.after(0, self.update_complete)
                else:
                    self.root.after(0, self.update_error, f"Could not fetch release info: HTTP {response.status_code}")
            except Exception as e:
                self.root.after(0, self.update_error, str(e))
        self.update_thread = threading.Thread(target=force_update_thread, daemon=True)
        self.update_thread.start()
        """Download and update files from repository or release"""
        if self.is_updating:
            return
        
        self.is_updating = True
        self.update_button.configure(state='disabled')
        self.check_button.configure(state='disabled')
        self.progress_bar.start()
        self.progress_var.set("Downloading updates...")
        
        def update_thread():
            try:
                if self.config.get('use_releases', True) and hasattr(self, 'latest_release_data'):
                    # Download from release
                    release_data = self.latest_release_data
                    # Find the source code zip asset
                    download_url = None
                    for asset in release_data.get('assets', []):
                        if asset['name'].endswith('.zip'):
                            download_url = asset['browser_download_url']
                            break
                    # If no assets, use the source code archive
                    if not download_url:
                        download_url = release_data['zipball_url']
                    self.log(f"Downloading release {release_data['tag_name']} from: {download_url}")
                    response = requests.get(download_url, timeout=30)
                    response.raise_for_status()
                    # Save and extract ZIP
                    zip_path = self.launcher_dir / "temp_update.zip"
                    with open(zip_path, 'wb') as f:
                        f.write(response.content)
                    self.log("Extracting files...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        extract_path = self.launcher_dir / "temp_extract"
                        zip_ref.extractall(extract_path)
                    # Find the extracted repo folder
                    repo_folders = list(extract_path.glob("*"))
                    if repo_folders:
                        repo_folder = repo_folders[0]
                        # List all folders/files in the extracted repo folder
                        extracted_items = [p for p in repo_folder.iterdir()]
                        self.log(f"Extracted repo folder contents: {[p.name for p in extracted_items]}")
                        # For each folder or file in the extracted repo folder, copy it to the minecraft_dir
                        for item in extracted_items:
                            dst_path = self.minecraft_dir / item.name
                            self.log(f"Syncing '{item.name}' to '{dst_path}'")
                            if item.is_dir():
                                if dst_path.exists():
                                    shutil.rmtree(dst_path)
                                shutil.copytree(item, dst_path)
                            else:
                                shutil.copy2(item, dst_path)
                    # Update version in config
                    self.config['current_version'] = release_data['tag_name']
                    self.save_config()
                    # Cleanup
                    shutil.rmtree(extract_path)
                    zip_path.unlink()
                    self.root.after(0, self.update_complete)
                else:
                    # Original branch-based download
                    repo_url = f"https://github.com/{self.config['github_repo']}/archive/{self.config['github_branch']}.zip"
                    self.log(f"Downloading from: {repo_url}")
                    response = requests.get(repo_url, timeout=30)
                    response.raise_for_status()
                    # Save and extract ZIP
                    zip_path = self.launcher_dir / "temp_update.zip"
                    with open(zip_path, 'wb') as f:
                        f.write(response.content)
                    self.log("Extracting files...")
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        extract_path = self.launcher_dir / "temp_extract"
                        zip_ref.extractall(extract_path)
                    # Find the extracted repo folder
                    repo_folders = list(extract_path.glob("*"))
                    if repo_folders:
                        repo_folder = repo_folders[0]
                        for folder in self.config['folders_to_sync']:
                            src_folder = repo_folder / folder
                            dst_folder = self.minecraft_dir / folder
                            if src_folder.exists():
                                self.log(f"Updating folder: {folder}")
                                if dst_folder.exists():
                                    for item in dst_folder.iterdir():
                                        if item.is_dir():
                                            shutil.rmtree(item)
                                        else:
                                            item.unlink()
                                else:
                                    dst_folder.mkdir(parents=True, exist_ok=True)
                                for item in src_folder.iterdir():
                                    s = item
                                    d = dst_folder / item.name
                                    if s.is_dir():
                                        shutil.copytree(s, d)
                                    else:
                                        shutil.copy2(s, d)
                            else:
                                self.log(f"Folder not found in repo: {folder}")
                    shutil.rmtree(extract_path)
                    zip_path.unlink()
                    self.root.after(0, self.update_complete)
            except Exception as e:
                self.root.after(0, self.update_error, str(e))
        self.update_thread = threading.Thread(target=update_thread, daemon=True)
        self.update_thread.start()
    
    def update_complete(self):
        """Called when update is complete"""
        self.is_updating = False
        self.progress_bar.stop()
        self.check_button.configure(state='normal')
        self.update_button.configure(state='disabled')
        self.progress_var.set("Update completed successfully")
        self.log("Files updated successfully")
        messagebox.showinfo("Success", "Files updated successfully!")
    
    def update_error(self, error_msg):
        """Called when update fails"""
        self.is_updating = False
        self.progress_bar.stop()
        self.check_button.configure(state='normal')
        self.progress_var.set("Error updating files")
        self.log(f"Error updating files: {error_msg}")
        messagebox.showerror("Error", f"Failed to update files:\n{error_msg}")
    
    def launch_minecraft(self):
        """Launch the Minecraft client"""
        try:
            minecraft_exe = self.minecraft_dir / self.config['minecraft_executable']
            if not minecraft_exe.exists():
                # Try common Minecraft launcher names
                possible_names = ['minecraft.exe', 'MinecraftLauncher.exe', 'launcher.exe']
                for name in possible_names:
                    test_path = self.minecraft_dir / name
                    if test_path.exists():
                        minecraft_exe = test_path
                        break
                else:
                    messagebox.showerror("Error", f"Minecraft executable not found in {self.minecraft_dir}")
                    return
            self.log(f"Launching Minecraft: {minecraft_exe}")
            subprocess.Popen([str(minecraft_exe)], cwd=str(self.minecraft_dir))
            self.root.quit()
        except Exception as e:
            self.log(f"Error launching Minecraft: {str(e)}")
            messagebox.showerror("Error", f"Failed to launch Minecraft:\n{str(e)}")
    
    def open_settings(self):
        """Open settings dialog (customtkinter)"""
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Launcher Settings")
        self.center_window(settings_window, 380, 250)
        settings_window.transient(self.root)
        settings_window.grab_set()

        # Settings form
        frame = ctk.CTkFrame(settings_window, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(frame, text="Minecraft Directory:").pack(anchor="w")
        dir_entry = ctk.CTkEntry(frame, width=280)
        dir_entry.insert(0, self.config['minecraft_dir'])
        dir_entry.pack(fill="x", pady=(0, 10))
        def on_dir_change(event=None):
            self.config['minecraft_dir'] = dir_entry.get().strip()
            self.save_config()
            self.minecraft_dir = Path(self.config['minecraft_dir'])
            self.dir_label.configure(text=str(self.minecraft_dir.resolve()))
        dir_entry.bind('<KeyRelease>', on_dir_change)

        ctk.CTkLabel(frame, text="Minecraft Executable:").pack(anchor="w")
        exe_entry = ctk.CTkEntry(frame, width=280)
        exe_entry.insert(0, self.config['minecraft_executable'])
        exe_entry.pack(fill="x", pady=(0, 10))
        def on_exe_change(event=None):
            self.config['minecraft_executable'] = exe_entry.get().strip()
            self.save_config()
        exe_entry.bind('<KeyRelease>', on_exe_change)

        # Checkboxes
        check_startup_var = ctk.BooleanVar(value=self.config.get('check_on_startup', True))
        def on_check_startup_change():
            self.config['check_on_startup'] = check_startup_var.get()
            self.save_config()
        check_startup_cb = ctk.CTkCheckBox(frame, text="Check for updates on startup", variable=check_startup_var, command=on_check_startup_change)
        check_startup_cb.pack(anchor="w", pady=(0, 5))

        auto_update_var = ctk.BooleanVar(value=self.config.get('auto_update', False))
        def on_auto_update_change():
            self.config['auto_update'] = auto_update_var.get()
            self.save_config()
        auto_update_cb = ctk.CTkCheckBox(frame, text="Auto-update without asking", variable=auto_update_var, command=on_auto_update_change)
        auto_update_cb.pack(anchor="w", pady=(0, 10))

        # Buttons
        button_frame = ctk.CTkFrame(frame, fg_color="transparent")
        button_frame.pack(fill="x")
        ctk.CTkButton(button_frame, text="Close", command=settings_window.destroy).pack(side="right")
    
    def run(self):
        """Start the launcher"""
        self.root.mainloop()

if __name__ == "__main__":
    launcher = MinecraftLauncher()
    launcher.run()
