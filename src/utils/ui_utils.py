"""UI utility functions for the FFT Minecraft Launcher."""

from typing import Tuple, Optional
import customtkinter as ctk
from pathlib import Path


class UIUtils:
    """Utility class for UI operations."""
    
    @staticmethod
    def set_window_icon(window) -> None:
        """Set the application icon for a window.
        
        Args:
            window: The window to set the icon for
        """
        try:
            # Get the path to the icon file
            # When running from bootstrap, we need to go up from the launcher directory
            current_dir = Path(__file__).parent.parent.parent  # Go up from src/utils/ to project root
            icon_path = current_dir / "assets" / "minecraft_icon.ico"
            if icon_path.exists():
                window.iconbitmap(str(icon_path))
        except Exception:
            # If icon loading fails, continue without it
            pass
    
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
        """Get enhanced theme colors based on current appearance mode."""
        appearance_mode = ctk.get_appearance_mode()
        
        if appearance_mode == "Dark":
            return {
                'bg_color': '#1a1a1a',
                'fg_color': '#2b2b2b',
                'card_color': '#333333',
                'text_color': '#ffffff',
                'text_secondary': '#cccccc',
                'button_color': '#28a745',
                'button_hover_color': '#1e7e34',
                'accent_color': '#3b8ed0',
                'success_color': '#28a745',
                'warning_color': '#ffc107',
                'error_color': '#dc3545',
                'info_color': '#17a2b8'
            }
        else:
            return {
                'bg_color': '#f8f9fa',
                'fg_color': '#ffffff',
                'card_color': '#f8f9fa',
                'text_color': '#000000',
                'text_secondary': '#666666',
                'button_color': '#28a745',
                'button_hover_color': '#1e7e34',
                'accent_color': '#3b8ed0',
                'success_color': '#28a745',
                'warning_color': '#ffc107',
                'error_color': '#dc3545',
                'info_color': '#17a2b8'
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
        import tkinter as tk
        
        # Create a temporary root window for the dialog
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        UIUtils.set_window_icon(root)
        
        messagebox.showerror(title, message, parent=root)
        root.destroy()
    
    @staticmethod
    def show_info_dialog(title: str, message: str) -> None:
        """Show an info dialog."""
        from tkinter import messagebox
        import tkinter as tk
        
        # Create a temporary root window for the dialog
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        UIUtils.set_window_icon(root)
        
        messagebox.showinfo(title, message, parent=root)
        root.destroy()
    
    @staticmethod
    def show_warning_dialog(title: str, message: str) -> None:
        """Show a warning dialog."""
        from tkinter import messagebox
        import tkinter as tk
        
        # Create a temporary root window for the dialog
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        UIUtils.set_window_icon(root)
        
        messagebox.showwarning(title, message, parent=root)
        root.destroy()
    
    @staticmethod
    def ask_yes_no(title: str, message: str) -> bool:
        """Show a yes/no dialog and return the result."""
        from tkinter import messagebox
        import tkinter as tk
        
        # Create a temporary root window for the dialog
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        UIUtils.set_window_icon(root)
        
        result = messagebox.askyesno(title, message, parent=root)
        root.destroy()
        return result
    
    @staticmethod
    def create_modern_card(parent, title: str, value: str, icon: str = "", width: Optional[int] = None) -> ctk.CTkFrame:
        """Create a modern card with title, value, and optional icon.
        
        Args:
            parent: Parent widget
            title: Card title
            value: Card value
            icon: Optional unicode icon
            width: Optional card width
            
        Returns:
            The created card frame
        """
        card = ctk.CTkFrame(parent, corner_radius=8, height=80)
        if width:
            card.configure(width=width)
        card.grid_propagate(False)
        
        # Icon (if provided)
        if icon:
            icon_label = ctk.CTkLabel(card, text=icon, font=ctk.CTkFont(size=20))
            icon_label.pack(pady=(8, 2))
        
        # Title
        title_label = ctk.CTkLabel(
            card, 
            text=title, 
            font=ctk.CTkFont(size=11, weight="normal"),
            text_color=("gray60", "gray40")
        )
        title_label.pack()
        
        # Value
        value_label = ctk.CTkLabel(
            card, 
            text=value, 
            font=ctk.CTkFont(size=12, weight="bold")
        )
        value_label.pack(pady=(2, 8))
        
        return card
    
    @staticmethod
    def animate_widget_opacity(widget, target_alpha: float, duration: int = 300, steps: int = 20):
        """Animate widget opacity (simplified version for customtkinter).
        
        Args:
            widget: Widget to animate
            target_alpha: Target opacity (0.0 to 1.0)
            duration: Animation duration in milliseconds
            steps: Number of animation steps
        """
        # Note: CustomTkinter doesn't support true opacity animations
        # This is a placeholder for potential future enhancements
        pass
    
    @staticmethod
    def create_tooltip(widget, text: str):
        """Create a tooltip for a widget.
        
        Args:
            widget: Widget to add tooltip to
            text: Tooltip text
        """
        def on_enter(event):
            tooltip = ctk.CTkToplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.configure(fg_color=("black", "white"))
            
            label = ctk.CTkLabel(
                tooltip, 
                text=text, 
                font=ctk.CTkFont(size=10),
                text_color=("white", "black")
            )
            label.pack(padx=5, pady=2)
            
            x = widget.winfo_rootx() + 25
            y = widget.winfo_rooty() + 25
            tooltip.geometry(f"+{x}+{y}")
            
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
