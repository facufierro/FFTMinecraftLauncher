"""UI utility functions for the FFT Minecraft Launcher."""

from typing import Tuple
import customtkinter as ctk


class UIUtils:
    """Utility class for UI operations."""
    
    @staticmethod
    def center_window(window, width: int, height: int) -> None:
        """Center a window on the screen."""
        window.update_idletasks()
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    @staticmethod
    def get_theme_colors() -> dict:
        """Get theme colors based on current appearance mode."""
        appearance_mode = ctk.get_appearance_mode()
        
        if appearance_mode == "Dark":
            return {
                'bg_color': '#212121',
                'fg_color': '#2b2b2b',
                'text_color': '#ffffff',
                'button_color': '#1f538d',
                'button_hover_color': '#14375e'
            }
        else:
            return {
                'bg_color': '#f0f0f0',
                'fg_color': '#ffffff',
                'text_color': '#000000',
                'button_color': '#3b8ed0',
                'button_hover_color': '#36719f'
            }
    
    @staticmethod
    def setup_responsive_grid(widget: ctk.CTkFrame, columns: int, rows: int) -> None:
        """Setup responsive grid for a widget."""
        for i in range(columns):
            widget.columnconfigure(i, weight=1)
        for i in range(rows):
            widget.rowconfigure(i, weight=1)
    
    @staticmethod
    def create_info_frame(parent: ctk.CTkFrame, title: str, value: str, row: int, column: int = 0, columnspan: int = 2) -> Tuple[ctk.CTkLabel, ctk.CTkLabel]:
        """Create an info frame with title and value labels."""
        title_label = ctk.CTkLabel(parent, text=f"{title}:")
        title_label.grid(row=row, column=column, sticky="w", padx=(10, 5), pady=2)
        
        value_label = ctk.CTkLabel(parent, text=value)
        value_label.grid(row=row, column=column + 1, sticky="w", padx=(5, 10), pady=2)
        
        return title_label, value_label
    
    @staticmethod
    def show_error_dialog(title: str, message: str) -> None:
        """Show an error dialog."""
        from tkinter import messagebox
        messagebox.showerror(title, message)
    
    @staticmethod
    def show_info_dialog(title: str, message: str) -> None:
        """Show an info dialog."""
        from tkinter import messagebox
        messagebox.showinfo(title, message)
    
    @staticmethod
    def show_warning_dialog(title: str, message: str) -> None:
        """Show a warning dialog."""
        from tkinter import messagebox
        messagebox.showwarning(title, message)
    
    @staticmethod
    def ask_yes_no(title: str, message: str) -> bool:
        """Show a yes/no dialog and return the result."""
        from tkinter import messagebox
        return messagebox.askyesno(title, message)
