"""
FFT Minecraft Launcher
A launcher that syncs specific folders from GitHub repo before launching Minecraft client.
"""

import os
import sys
import json
import shutil
import hashlib
import requests
import zipfile
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
import subprocess
from datetime import datetime

class MinecraftLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("FFT Minecraft Launcher")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Configuration
        self.config_file = "launcher_config.json"
        self.load_config()
        
        # Paths
        self.launcher_dir = Path(__file__).parent
        self.minecraft_dir = Path(self.config.get("minecraft_dir", "../FFTClientMinecraft1211"))
        
        # State
        self.is_updating = False
        self.update_thread = None
        
        self.setup_ui()
        
    def load_config(self):
        """Load configuration from JSON file"""
        default_config = {
            "github_repo": "facufierro/FFTClientMinecraft1211",
            "use_releases": True,
            "release_tag": "latest",  # "latest" for most recent, or specific tag like "v1.0.0"
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
        """Setup the user interface"""
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="FFT Minecraft Launcher", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        ttk.Label(status_frame, text="Repository:").grid(row=0, column=0, sticky=tk.W)
        self.repo_label = ttk.Label(status_frame, text=self.config['github_repo'])
        self.repo_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(status_frame, text="Local Directory:").grid(row=1, column=0, sticky=tk.W)
        self.dir_label = ttk.Label(status_frame, text=str(self.minecraft_dir.resolve()))
        self.dir_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(status_frame, text="Last Check:").grid(row=2, column=0, sticky=tk.W)
        self.last_check_label = ttk.Label(status_frame, text="Never")
        self.last_check_label.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        # Progress frame
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        self.check_button = ttk.Button(buttons_frame, text="Check for Updates", 
                                      command=self.check_updates)
        self.check_button.grid(row=0, column=0, padx=(0, 10))
        
        self.update_button = ttk.Button(buttons_frame, text="Update Files", 
                                       command=self.update_files, state='disabled')
        self.update_button.grid(row=0, column=1, padx=(0, 10))

        self.force_update_button = ttk.Button(buttons_frame, text="Force Update", command=self.force_update)
        self.force_update_button.grid(row=0, column=4, padx=(0, 10))
        
        self.launch_button = ttk.Button(buttons_frame, text="Launch Minecraft", 
                                       command=self.launch_minecraft, state='disabled')
        self.launch_button.grid(row=0, column=2, padx=(0, 10))
        
        self.settings_button = ttk.Button(buttons_frame, text="Settings", 
                                         command=self.open_settings)
        self.settings_button.grid(row=0, column=3)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state='disabled')
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
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        
        print(f"LOG: {message}")  # Also print to console
    
    def check_minecraft_dir(self):
        """Check if Minecraft directory exists and is accessible"""
        if not self.minecraft_dir.exists():
            self.log(f"Warning: Minecraft directory not found: {self.minecraft_dir}")
            self.launch_button.config(state='disabled')
            return False
        
        self.log(f"Minecraft directory found: {self.minecraft_dir}")
        self.launch_button.config(state='normal')
        return True
    
    def check_updates(self):
        """Check for updates from GitHub releases"""
        if self.is_updating:
            return
        
        self.is_updating = True
        self.check_button.config(state='disabled')
        self.progress_bar.start()
        self.progress_var.set("Checking for updates...")
        
        def check_thread():
            try:
                if self.config.get('use_releases', True):
                    # Check GitHub releases
                    if self.config['release_tag'] == "latest":
                        releases_url = f"https://api.github.com/repos/{self.config['github_repo']}/releases/latest"
                    else:
                        releases_url = f"https://api.github.com/repos/{self.config['github_repo']}/releases/tags/{self.config['release_tag']}"
                    
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
                else:
                    # Original branch-based checking (fallback)
                    repo_url = f"https://api.github.com/repos/{self.config['github_repo']}/contents"
                    updates_needed = []
                    
                    for folder in self.config['folders_to_sync']:
                        self.log(f"Checking folder: {folder}")
                        
                        try:
                            response = requests.get(f"{repo_url}/{folder}", timeout=10)
                            if response.status_code == 200:
                                remote_files = response.json()
                                local_folder = self.minecraft_dir / folder
                                
                                if self.folder_needs_update(local_folder, remote_files):
                                    updates_needed.append(folder)
                                    self.log(f"Updates available for: {folder}")
                                else:
                                    self.log(f"Up to date: {folder}")
                            else:
                                self.log(f"Could not check folder {folder}: HTTP {response.status_code}")
                        except Exception as e:
                            self.log(f"Error checking folder {folder}: {str(e)}")
                    
                    self.root.after(0, self.check_complete, updates_needed)
                
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
        self.check_button.config(state='normal')
        self.last_check_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        if updates_needed:
            self.progress_var.set(f"New release available: {latest_version}")
            self.update_button.config(state='normal')
            self.log(f"New release available: {latest_version}")
            self.latest_release_data = release_data  # Store for download
        else:
            self.progress_var.set(f"Up to date (Version: {latest_version})")
            self.update_button.config(state='disabled')
            self.log(f"Already up to date with version: {latest_version}")
    
    def check_complete(self, updates_needed):
        """Called when update check is complete"""
        self.is_updating = False
        self.progress_bar.stop()
        self.check_button.config(state='normal')
        self.last_check_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        if updates_needed:
            self.progress_var.set(f"Updates available for: {', '.join(updates_needed)}")
            self.update_button.config(state='normal')
            self.log(f"Found updates for {len(updates_needed)} folders")
        else:
            self.progress_var.set("All files up to date")
            self.update_button.config(state='disabled')
            self.log("All files are up to date")
    
    def check_error(self, error_msg):
        """Called when update check fails"""
        self.is_updating = False
        self.progress_bar.stop()
        self.check_button.config(state='normal')
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
        self.update_button.config(state='disabled')
        self.check_button.config(state='disabled')
        self.progress_bar.start()
        self.progress_var.set("Force updating files...")

        def force_update_thread():
            try:
                # Always fetch the latest release data, even if current_version matches
                if self.config.get('use_releases', True):
                    if self.config['release_tag'] == "latest":
                        releases_url = f"https://api.github.com/repos/{self.config['github_repo']}/releases/latest"
                    else:
                        releases_url = f"https://api.github.com/repos/{self.config['github_repo']}/releases/tags/{self.config['release_tag']}"
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
                else:
                    self.root.after(0, self.update_error, "Force update only supported for releases mode.")
            except Exception as e:
                self.root.after(0, self.update_error, str(e))
        self.update_thread = threading.Thread(target=force_update_thread, daemon=True)
        self.update_thread.start()
        """Download and update files from repository or release"""
        if self.is_updating:
            return
        
        self.is_updating = True
        self.update_button.config(state='disabled')
        self.check_button.config(state='disabled')
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
        self.check_button.config(state='normal')
        self.update_button.config(state='disabled')
        self.progress_var.set("Update completed successfully")
        self.log("Files updated successfully")
        messagebox.showinfo("Success", "Files updated successfully!")
    
    def update_error(self, error_msg):
        """Called when update fails"""
        self.is_updating = False
        self.progress_bar.stop()
        self.check_button.config(state='normal')
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
        """Open settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Launcher Settings")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Settings form
        frame = ttk.Frame(settings_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Repository settings
        ttk.Label(frame, text="GitHub Repository (owner/repo):").pack(anchor=tk.W)
        repo_entry = ttk.Entry(frame, width=50)
        repo_entry.insert(0, self.config['github_repo'])
        repo_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Release/Branch settings
        use_releases_var = tk.BooleanVar(value=self.config.get('use_releases', True))
        ttk.Checkbutton(frame, text="Use GitHub Releases (recommended)", 
                       variable=use_releases_var).pack(anchor=tk.W, pady=(0, 5))
        
        ttk.Label(frame, text="Release Tag (use 'latest' for newest):").pack(anchor=tk.W)
        release_entry = ttk.Entry(frame, width=50)
        release_entry.insert(0, self.config.get('release_tag', 'latest'))
        release_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Minecraft Directory:").pack(anchor=tk.W)
        dir_entry = ttk.Entry(frame, width=50)
        dir_entry.insert(0, self.config['minecraft_dir'])
        dir_entry.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(frame, text="Minecraft Executable:").pack(anchor=tk.W)
        exe_entry = ttk.Entry(frame, width=50)
        exe_entry.insert(0, self.config['minecraft_executable'])
        exe_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Checkboxes
        check_startup_var = tk.BooleanVar(value=self.config.get('check_on_startup', True))
        ttk.Checkbutton(frame, text="Check for updates on startup", 
                       variable=check_startup_var).pack(anchor=tk.W, pady=(0, 5))
        
        auto_update_var = tk.BooleanVar(value=self.config.get('auto_update', False))
        ttk.Checkbutton(frame, text="Auto-update without asking", 
                       variable=auto_update_var).pack(anchor=tk.W, pady=(0, 10))
        
        # Folders to sync
        ttk.Label(frame, text="Folders to sync (one per line):").pack(anchor=tk.W)
        folders_text = tk.Text(frame, height=8, width=50)
        folders_text.insert('1.0', '\n'.join(self.config['folders_to_sync']))
        folders_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X)
        
        def save_settings():
            self.config['github_repo'] = repo_entry.get().strip()
            self.config['use_releases'] = use_releases_var.get()
            self.config['release_tag'] = release_entry.get().strip()
            self.config['minecraft_dir'] = dir_entry.get().strip()
            self.config['minecraft_executable'] = exe_entry.get().strip()
            self.config['check_on_startup'] = check_startup_var.get()
            self.config['auto_update'] = auto_update_var.get()
            
            folders_content = folders_text.get('1.0', tk.END).strip()
            self.config['folders_to_sync'] = [f.strip() for f in folders_content.split('\n') if f.strip()]
            
            self.save_config()
            
            # Update UI
            self.minecraft_dir = Path(self.config['minecraft_dir'])
            self.repo_label.config(text=self.config['github_repo'])
            self.dir_label.config(text=str(self.minecraft_dir.resolve()))
            
            self.log("Settings saved")
            settings_window.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_settings).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.RIGHT)
    
    def run(self):
        """Start the launcher"""
        self.root.mainloop()

if __name__ == "__main__":
    launcher = MinecraftLauncher()
    launcher.run()
