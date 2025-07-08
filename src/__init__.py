"""FFT Minecraft Launcher - A modular Minecraft launcher with GitHub integration."""

__version__ = "2.0.0"
__author__ = "FFT Team"
__description__ = "A launcher that syncs specific folders from GitHub repo before launching Minecraft client."

from .core.launcher import LauncherCore
from .models.config import LauncherConfig
from .utils.logging_utils import setup_logger, get_logger

__all__ = ['LauncherCore', 'LauncherConfig', 'setup_logger', 'get_logger']
