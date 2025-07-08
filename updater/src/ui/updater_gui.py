"""
Updater GUI Module
-----------------
User interface for the updater application
"""

import tkinter as tk
from tkinter import messagebox


class UpdaterGUI:
    """Graphical user interface for the updater application"""
    
    def __init__(self, updater, auto_launch=True):
        """
        Initialize the GUI
        
        Args:
            updater (AppUpdater): The updater instance to use
            auto_launch (bool): Whether to automatically launch the application after update
        """
        self.updater = updater
        self.auto_launch = auto_launch
        self.setup_ui()
    
    def setup_ui(self):
        """Create the user interface"""
        self.root = tk.Tk()
        self.root.title("App Updater")
        self.root.resizable(False, False)
        
        # Main frame
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(expand=True, fill=tk.BOTH)
        
        # Title label
        title_label = tk.Label(
            main_frame,
            text="Application Updater",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_label = tk.Label(
            main_frame,
            text=f"This will update {self.updater.target_file}\nfrom the latest GitHub release.",
            justify=tk.CENTER
        )
        desc_label.pack(pady=(0, 20))
        
        # Main button
        self.update_button = tk.Button(
            main_frame, 
            text="Update & Launch", 
            command=self.on_update_click,
            width=20, 
            height=2,
            font=("Arial", 10)
        )
        self.update_button.pack()
        
        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Ready to update",
            font=("Arial", 9),
            fg="gray"
        )
        self.status_label.pack(pady=(10, 0))
        
        # Center window
        self.center_window()
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_update_click(self):
        """Handle update button click"""
        self.update_button.config(state="disabled", text="Updating...")
        self.status_label.config(text="Checking for running instances...")
        self.root.update()
        
        try:
            # Close running instances
            was_running = self.updater.close_target_app()
            if was_running:
                self.status_label.config(text="Closed running application...")
                self.root.update()
            
            # Download new version
            self.status_label.config(text="Downloading update from GitHub...")
            self.root.update()
            temp_file = self.updater.download_from_github()
            
            # Replace file
            self.status_label.config(text="Installing update...")
            self.root.update()
            self.updater.replace_target_file(temp_file)
            
            self.status_label.config(text="Update completed successfully!")
            self.root.update()
            messagebox.showinfo("Update Complete", "Application updated successfully!")
            
            # Launch updated app if configured
            if self.auto_launch:
                self.updater.launch_target_app()
            
            self.root.destroy()
            
        except Exception as e:
            error_message = str(e)
            self.status_label.config(text=f"Error: {error_message[:30]}...")
            self.update_button.config(state="normal", text="Retry Update")
            messagebox.showerror("Update Failed", f"Failed to update application:\n{e}")
            
            # Try to launch existing app if configured
            if self.auto_launch:
                try:
                    self.updater.launch_target_app()
                except Exception as launch_error:
                    messagebox.showerror("Launch Failed", f"Could not launch application:\n{launch_error}")
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()
